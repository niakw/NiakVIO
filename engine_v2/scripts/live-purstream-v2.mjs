#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { ResolverCore } from "../src/resolver-core.mjs";
import { createTmdbMetadataResolver } from "../src/tmdb-metadata.mjs";
import { createPurstreamAdapter, derivePurstreamEndpoint } from "../providers/purstream.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const domainsPath = argValue("--domains") ?? path.join(root, "reports", "provider-domain-observations.json");
const outputPath = argValue("--output") ?? path.join(root, "reports", "purstream-live-v2.json");
const clientsPath = path.join(root, "config", "nuvio-clients.json");
const domains = await readJson(domainsPath, { providers: [] });
const clients = await readJson(clientsPath, { clients: {} });
const observation = (domains.providers ?? []).find((row) => row.id === "purstream") ?? null;
const candidates = buildCandidates(observation);
const attempts = [];

for (const terminalUrl of candidates) {
  const fetchImpl = (url, options = {}) => fetch(url, {
    ...options,
    signal: options.signal ?? AbortSignal.timeout(8000),
  });
  let adapter;
  try {
    adapter = createPurstreamAdapter({ fetchImpl, terminalUrl, domainSource: "v2-live-lab" });
  } catch (error) {
    attempts.push({ terminalUrl, setupError: String(error?.message ?? error), fixtures: [] });
    continue;
  }
  const core = new ResolverCore({
    metadataResolver: createTmdbMetadataResolver({ fetchImpl, timeoutMs: 6000 }),
    mediaValidationOptions: { timeoutMs: 8000, maxCandidates: 3, probeHlsChild: true },
  });
  const fixtureResults = [];
  for (const fixture of fixtures()) {
    const result = await core.resolve({
      provider: { id: "purstream", name: "Purstream" },
      adapter,
      request: { ...fixture.request, device: fixture.device },
      fixtureId: fixture.id,
      clientRef: fixture.clientRef,
    });
    fixtureResults.push(summarizeFixture(result, fixture));
  }
  const attempt = {
    terminalUrl,
    fixtures: fixtureResults,
    healthyCount: fixtureResults.filter((row) => row.failureClass === "healthy").length,
    playableStreams: fixtureResults.reduce((sum, row) => sum + row.playableStreams, 0),
  };
  attempts.push(attempt);
  if (attempt.healthyCount === fixtureResults.length) break;
  // If the domain resolves the catalogue/API, a fixture-specific failure is not
  // evidence that another suffix is better. Stop domain-hopping and let Repair Brain classify it.
  if (fixtureResults.some((row) => ["search_gap", "identity_mismatch", "detail_gap", "episode_gap", "media_extraction_gap", "media_validation_gap", "playback_context_gap"].includes(row.failureClass))) break;
}

const best = [...attempts]
  .filter((row) => !row.setupError)
  .sort((a, b) => (b.healthyCount ?? 0) - (a.healthyCount ?? 0) || (b.playableStreams ?? 0) - (a.playableStreams ?? 0))[0] ?? null;
const report = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  mode: "diagnostic-not-publication-blocker",
  provider: "purstream",
  presentation: "core-shared-facts-plus-tmdb",
  domainObservation: observation ? {
    selected: observation.selected ?? null,
    hubUrls: observation.hubUrls ?? [],
    registryCandidateCount: observation.registryCandidateCount ?? 0,
    hubTerminalCandidateCount: observation.hubTerminalCandidateCount ?? 0,
  } : null,
  candidates,
  attempts,
  best,
  summary: {
    bothHealthy: best?.healthyCount === 2,
    interstellarHealthy: best?.fixtures?.find((row) => row.id === "interstellar")?.failureClass === "healthy",
    breakingBadHealthy: best?.fixtures?.find((row) => row.id === "breaking-bad-s01e01")?.failureClass === "healthy",
  },
};
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

function fixtures() {
  return [
    {
      id: "interstellar",
      device: "desktop",
      clientRef: clients.clients?.desktop?.accepted_ref ?? "desktop-unknown",
      request: { tmdbId: "157336", mediaType: "movie", title: "Interstellar", year: 2014, languages: ["fr"] },
    },
    {
      id: "breaking-bad-s01e01",
      device: "tv",
      clientRef: clients.clients?.tv?.accepted_ref ?? "tv-unknown",
      request: { tmdbId: "1396", mediaType: "series", title: "Breaking Bad", year: 2008, season: 1, episode: 1, languages: ["fr"] },
    },
  ];
}

function buildCandidates(observation) {
  const values = [];
  const add = (value) => {
    if (!value) return;
    try {
      const endpoint = derivePurstreamEndpoint(value);
      if (!values.includes(endpoint.site)) values.push(endpoint.site);
    } catch {}
  };
  add(observation?.selected?.url);
  for (const probe of observation?.probes ?? []) {
    if (probe.role === "hub") continue;
    add(probe.http?.finalUrl ?? probe.url);
  }
  // Historical suffixes are only a bounded fallback after official hub/registry/current observation.
  for (const suffix of ["club", "mx", "ch", "ac", "cx", "art", "co", "me", "to", "store"]) add(`https://purstream.${suffix}/`);
  return values.slice(0, 8);
}

function summarizeFixture(result, fixture) {
  return {
    id: fixture.id,
    device: fixture.device,
    mediaType: result.request.mediaType,
    season: result.request.season,
    episode: result.request.episode,
    failureClass: result.repair.failureClass,
    repairHypotheses: result.repair.hypotheses.map((item) => item.id),
    playableStreams: result.evidence.playableStreams,
    streams: result.streams.map((stream) => ({
      title: stream.title,
      description: stream.description,
      quality: stream.quality,
      language: stream.language,
      codec: stream.codec,
      audio: stream.audio,
      duration: stream.duration,
      sourceType: stream.sourceType,
      ageRating: stream.ageRating,
      displayBadges: stream.displayBadges,
      playable: stream.playable,
      host: safeHost(stream.validation?.finalUrl ?? stream.url),
    })),
    streamHosts: [...new Set(result.streams.filter((stream) => stream.playable).map((stream) => safeHost(stream.validation?.finalUrl ?? stream.url)).filter(Boolean))],
    stages: Object.fromEntries(Object.entries(result.evidence.stages).map(([name, stage]) => [name, compactStage(stage)])),
    errors: result.evidence.errors,
  };
}

function compactStage(stage = {}) {
  const keep = ["observed", "skipped", "ok", "status", "reachable", "matches", "matched", "found", "season", "episode", "streamCount", "playable", "playableCount", "testedCount", "statuses", "reasons", "accepted", "error"];
  return Object.fromEntries(keep.filter((key) => stage[key] !== undefined).map((key) => [key, stage[key]]));
}

function safeHost(value) {
  try { return new URL(value).hostname; } catch { return null; }
}

async function readJson(file, fallback) {
  try { return JSON.parse(await fs.readFile(file, "utf8")); } catch { return fallback; }
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : null;
}