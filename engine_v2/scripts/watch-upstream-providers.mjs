#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

export function providerKey(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .trim();
}

export function catalogIdentity(catalog = {}) {
  const ids = new Set();
  const names = new Set();
  for (const row of catalog.providers ?? []) {
    if (!row || typeof row !== "object") continue;
    for (const value of [row.canonicalId, row.scraper?.id]) {
      const key = providerKey(value);
      if (key) ids.add(key);
    }
    const name = providerKey(row.scraper?.name);
    if (name) names.add(name);
    const filename = String(row.scraper?.filename ?? "");
    const stem = path.basename(filename).split("--", 1)[0].replace(/\.js$/i, "");
    const stemKey = providerKey(stem);
    if (stemKey) ids.add(stemKey);
  }
  return { ids, names };
}

export function manifestRows(payload = {}) {
  const candidates = [payload.scrapers, payload.providers, payload.items];
  return candidates.find(Array.isArray) ?? [];
}

export function interestFor(row = {}) {
  const reasons = [];
  let score = 0;
  const languages = list(row.contentLanguage ?? row.languages).map((value) => value.toLowerCase());
  const formats = list(row.formats).map((value) => value.toLowerCase());
  const types = list(row.supportedTypes).map((value) => value.toLowerCase());
  const description = `${row.name ?? ""} ${row.description ?? ""}`.toLowerCase();

  if (languages.some((value) => ["fr", "fra", "french", "vf", "vostfr"].includes(value))) {
    score += 4;
    reasons.push("French/VF metadata");
  }
  if (types.includes("movie") && (types.includes("tv") || types.includes("anime"))) {
    score += 2;
    reasons.push("movie + episodic coverage");
  } else if (types.length) {
    score += 1;
    reasons.push(`covers ${types.join("/")}`);
  }
  const directFormats = formats.filter((value) => ["m3u8", "mp4", "mkv", "mpd", "webm"].includes(value));
  if (directFormats.length) {
    score += Math.min(3, directFormats.length);
    reasons.push(`direct formats: ${directFormats.join(", ")}`);
  }
  if (/\b(?:4k|uhd|2160p)\b/.test(description)) {
    score += 2;
    reasons.push("4K/UHD signal");
  }
  if (/anime|vostfr|french|francais|français/.test(description)) {
    score += 1;
    reasons.push("catalogue niche/language signal");
  }
  if (row.enabled !== false) {
    score += 1;
    reasons.push("enabled upstream");
  }
  if (row.limited === true) {
    score -= 1;
    reasons.push("limited upstream");
  }

  return { score, interesting: score >= 4, reasons };
}

export function compareManifest({ upstream, manifest, catalog }) {
  const known = catalogIdentity(catalog);
  const unseen = [];
  const existing = [];

  for (const row of manifestRows(manifest)) {
    if (!row || typeof row !== "object") continue;
    const id = String(row.id ?? row.name ?? "").trim();
    if (!id) continue;
    const idKey = providerKey(id);
    const nameKey = providerKey(row.name);
    const isKnown = known.ids.has(idKey) || (nameKey && known.names.has(nameKey));
    const summary = {
      upstream: upstream.id,
      repository: upstream.repository,
      id,
      name: row.name ?? id,
      version: row.version ?? null,
      filename: row.filename ?? null,
      supportedTypes: list(row.supportedTypes),
      contentLanguage: list(row.contentLanguage ?? row.languages),
      formats: list(row.formats),
      enabled: row.enabled !== false,
      limited: row.limited === true,
    };
    if (isKnown) {
      existing.push(summary);
      continue;
    }
    const interest = interestFor(row);
    unseen.push({ ...summary, ...interest });
  }

  unseen.sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
  return { unseen, existingCount: existing.length };
}

async function readJson(filename) {
  return JSON.parse(await fs.readFile(filename, "utf8"));
}

async function fetchManifest(upstream) {
  const repositories = [upstream.repository, upstream.fallback_repository].filter(Boolean);
  const errors = [];
  for (const repository of repositories) {
    const url = `https://raw.githubusercontent.com/${repository}/${encodeURIComponent(upstream.branch)}/${upstream.manifest}`;
    try {
      const response = await fetch(url, {
        headers: { "User-Agent": "NiakVIO-upstream-provider-watch/1" },
        signal: AbortSignal.timeout(20_000),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      return { payload, repository, url };
    } catch (error) {
      errors.push(`${repository}: ${error?.message ?? error}`);
    }
  }
  throw new Error(`${upstream.id}: unable to fetch manifest (${errors.join("; ")})`);
}

function markdown(report) {
  const lines = [
    "# Weekly upstream provider watch",
    "",
    `Generated: ${report.generatedAt}`,
    `New candidates: **${report.summary.newCandidates}** — interesting: **${report.summary.interestingCandidates}**`,
    "",
  ];
  for (const source of report.sources) {
    lines.push(`## ${source.id} — ${source.repository}`);
    lines.push("");
    if (!source.unseen.length) {
      lines.push("No provider missing from the NiakVIO catalogue.", "");
      continue;
    }
    lines.push("| Score | Provider | Types | Languages | Formats | Why |", "| ---: | --- | --- | --- | --- | --- |");
    for (const row of source.unseen) {
      lines.push(`| ${row.score} | ${escapeTable(row.name)} (${escapeTable(row.id)}) | ${escapeTable(row.supportedTypes.join(", ") || "-")} | ${escapeTable(row.contentLanguage.join(", ") || "-")} | ${escapeTable(row.formats.join(", ") || "-")} | ${escapeTable(row.reasons.join("; ") || "new upstream provider")} |`);
    }
    lines.push("");
  }
  lines.push("Candidates are observations only. This job never imports or publishes a provider automatically.", "");
  return lines.join("\n");
}

function escapeTable(value) {
  return String(value ?? "").replace(/\|/g, "\\|").replace(/\s+/g, " ").trim();
}

function list(value) {
  return Array.isArray(value) ? value.map((item) => String(item).trim()).filter(Boolean) : value == null ? [] : [String(value).trim()].filter(Boolean);
}

async function main() {
  const configPath = process.env.NIAKVIO_PROVIDER_UPSTREAMS ?? path.join(ROOT, "engine_v2/config/provider-upstreams.json");
  const catalogPath = process.env.NIAKVIO_PROVIDER_CATALOG ?? path.join(ROOT, "provider_catalog.json");
  const outputPath = process.env.NIAKVIO_UPSTREAM_REPORT ?? path.join(ROOT, "health-output/upstream-provider-watch.json");
  const markdownPath = process.env.NIAKVIO_UPSTREAM_MARKDOWN ?? path.join(ROOT, "health-output/upstream-provider-watch.md");

  const [config, catalog] = await Promise.all([readJson(configPath), readJson(catalogPath)]);
  const sources = [];
  for (const upstream of config.upstreams ?? []) {
    const fetched = await fetchManifest(upstream);
    const comparison = compareManifest({ upstream: { ...upstream, repository: fetched.repository }, manifest: fetched.payload, catalog });
    sources.push({
      id: upstream.id,
      repository: fetched.repository,
      branch: upstream.branch,
      manifest: upstream.manifest,
      fetchedFrom: fetched.url,
      existingCount: comparison.existingCount,
      unseen: comparison.unseen,
    });
  }

  const all = sources.flatMap((source) => source.unseen);
  const report = {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    policy: {
      importAutomatically: false,
      compareAgainst: "provider_catalog.json",
      sources: sources.map((source) => source.id),
    },
    summary: {
      newCandidates: all.length,
      interestingCandidates: all.filter((row) => row.interesting).length,
    },
    sources,
  };

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
  await fs.writeFile(markdownPath, markdown(report));
  console.log(`upstream provider watch: new=${report.summary.newCandidates} interesting=${report.summary.interestingCandidates}`);
  for (const row of all.filter((candidate) => candidate.interesting).slice(0, 30)) {
    console.log(`interesting: ${row.upstream}/${row.id} score=${row.score} ${row.reasons.join("; ")}`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => {
    console.error(error?.stack ?? error);
    process.exitCode = 1;
  });
}
