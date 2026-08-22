#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const DEFAULT_CONFIG = path.join(ROOT, "engine_v2/config/provider-upstreams.json");
const DEFAULT_CATALOG = path.join(ROOT, "provider_catalog.json");
const DEFAULT_OUTPUT = path.join(ROOT, "weekly-provider-discovery/candidates.json");
const INTERESTING_SCORE = 5;

function canonicalId(value) {
  return String(value ?? "").trim().toLowerCase();
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function manifestScrapers(value) {
  if (Array.isArray(value?.scrapers)) return value.scrapers;
  if (Array.isArray(value?.providers)) return value.providers;
  if (Array.isArray(value)) return value;
  return [];
}

function list(value) {
  if (Array.isArray(value)) return value.map((item) => String(item ?? "").trim()).filter(Boolean);
  if (typeof value === "string" && value.trim()) return [value.trim()];
  return [];
}

function normalizedText(row) {
  return JSON.stringify({
    id: row?.id,
    name: row?.name,
    description: row?.description,
    supportedTypes: row?.supportedTypes,
    contentLanguage: row?.contentLanguage,
    formats: row?.formats,
    filename: row?.filename,
  }).toLowerCase();
}

export function isExcludedProvider(row, exclusions = {}) {
  const id = canonicalId(row?.id);
  const excludedIds = new Set(list(exclusions.provider_ids).map(canonicalId));
  if (!id || excludedIds.has(id)) return true;
  const text = normalizedText(row);
  for (const pattern of list(exclusions.metadata_patterns)) {
    if (pattern && text.includes(pattern.toLowerCase())) return true;
  }
  return false;
}

export function scoreProvider(row) {
  let score = 0;
  const reasons = [];
  const languages = new Set(list(row?.contentLanguage ?? row?.languages).map((x) => x.toLowerCase()));
  const types = new Set(list(row?.supportedTypes ?? row?.types).map((x) => x.toLowerCase()));
  const formats = new Set(list(row?.formats).map((x) => x.toLowerCase()));
  const filename = String(row?.filename ?? "").trim();
  const description = String(row?.description ?? "").trim();

  if (row?.enabled !== false) {
    score += 2;
    reasons.push("upstream_enabled");
  }
  if (languages.has("fr")) {
    score += 4;
    reasons.push("french_content");
  } else if (languages.has("en")) {
    score += 1;
    reasons.push("english_content");
  }
  const usefulTypes = ["movie", "tv", "anime"].filter((type) => types.has(type));
  if (usefulTypes.length) {
    score += Math.min(3, usefulTypes.length);
    reasons.push(`types:${usefulTypes.join(",")}`);
  }
  const directFormats = ["m3u8", "hls", "mp4", "mkv", "dash", "mpd"].filter((format) => formats.has(format));
  if (directFormats.length) {
    score += 2;
    reasons.push(`direct_formats:${directFormats.join(",")}`);
  }
  if (filename) {
    score += 1;
    reasons.push("provider_bundle_declared");
  }
  if (description.length >= 24) {
    score += 1;
    reasons.push("described_upstream");
  }
  if (row?.limited === false) {
    score += 1;
    reasons.push("not_marked_limited");
  }
  return { score, reasons };
}

function candidateShape(row, source) {
  const { score, reasons } = scoreProvider(row);
  return {
    canonicalId: canonicalId(row.id),
    name: String(row.name ?? row.id ?? "").trim(),
    score,
    interesting: score >= INTERESTING_SCORE,
    reasons,
    upstreams: [source.id],
    upstreamRepositories: [source.repositoryUsed ?? source.repository],
    versions: row.version ? [String(row.version)] : [],
    supportedTypes: [...new Set(list(row.supportedTypes ?? row.types).map((x) => x.toLowerCase()))].sort(),
    contentLanguage: [...new Set(list(row.contentLanguage ?? row.languages).map((x) => x.toLowerCase()))].sort(),
    formats: [...new Set(list(row.formats).map((x) => x.toLowerCase()))].sort(),
    enabledUpstream: row.enabled !== false,
    limited: row.limited === true,
    filenames: row.filename ? [String(row.filename)] : [],
    reviewRequired: true,
    autoImportAllowed: false,
  };
}

function mergeCandidate(base, next) {
  base.score = Math.max(base.score, next.score);
  base.interesting = base.interesting || next.interesting;
  base.reasons = [...new Set([...base.reasons, ...next.reasons])].sort();
  base.upstreams = [...new Set([...base.upstreams, ...next.upstreams])].sort();
  base.upstreamRepositories = [...new Set([...base.upstreamRepositories, ...next.upstreamRepositories])].sort();
  base.versions = [...new Set([...base.versions, ...next.versions])].sort();
  base.supportedTypes = [...new Set([...base.supportedTypes, ...next.supportedTypes])].sort();
  base.contentLanguage = [...new Set([...base.contentLanguage, ...next.contentLanguage])].sort();
  base.formats = [...new Set([...base.formats, ...next.formats])].sort();
  base.enabledUpstream = base.enabledUpstream || next.enabledUpstream;
  base.limited = base.limited && next.limited;
  base.filenames = [...new Set([...base.filenames, ...next.filenames])].sort();
}

function rawManifestUrl(repository, branch, manifest) {
  return `https://raw.githubusercontent.com/${repository}/${encodeURIComponent(branch)}/${manifest.split("/").map(encodeURIComponent).join("/")}`;
}

async function fetchJson(url, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": "NiakVIO-upstream-provider-discovery/1" },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function loadSourceManifest(source, fixtureDir = "") {
  if (fixtureDir) {
    const fixture = path.join(fixtureDir, `${source.id}.json`);
    return { manifest: readJson(fixture), repositoryUsed: source.repository, sourceUrl: fixture };
  }
  const repositories = [source.repository, source.fallback_repository].filter(Boolean);
  let lastError = null;
  for (const repository of repositories) {
    const url = rawManifestUrl(repository, source.branch || "main", source.manifest || "manifest.json");
    try {
      return { manifest: await fetchJson(url), repositoryUsed: repository, sourceUrl: url };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError ?? new Error("no upstream repository configured");
}

export async function discover({ config, catalog, fixtureDir = "" }) {
  const knownIds = new Set((catalog.providers ?? []).map((row) => canonicalId(row?.canonicalId ?? row?.scraper?.id)).filter(Boolean));
  const exclusions = readJson(path.join(ROOT, "sources.json")).exclusions ?? {};
  const byId = new Map();
  const errors = [];
  const sourceResults = [];

  for (const configured of config.upstreams ?? []) {
    const source = { ...configured };
    try {
      const loaded = await loadSourceManifest(source, fixtureDir);
      source.repositoryUsed = loaded.repositoryUsed;
      const scrapers = manifestScrapers(loaded.manifest);
      let newCount = 0;
      let excludedCount = 0;
      for (const row of scrapers) {
        if (!row || typeof row !== "object") continue;
        const id = canonicalId(row.id);
        if (!id || knownIds.has(id)) continue;
        if (isExcludedProvider(row, exclusions)) {
          excludedCount += 1;
          continue;
        }
        newCount += 1;
        const shaped = candidateShape(row, source);
        if (byId.has(id)) mergeCandidate(byId.get(id), shaped);
        else byId.set(id, shaped);
      }
      sourceResults.push({
        id: source.id,
        repository: loaded.repositoryUsed,
        sourceUrl: loaded.sourceUrl,
        providerCount: scrapers.length,
        newProviderCount: newCount,
        excludedNewProviderCount: excludedCount,
        status: "ok",
      });
    } catch (error) {
      const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
      errors.push({ id: source.id, repository: source.repository, error: message });
      sourceResults.push({ id: source.id, repository: source.repository, status: "error", error: message });
    }
  }

  const candidates = [...byId.values()].sort((a, b) => b.score - a.score || a.canonicalId.localeCompare(b.canonicalId));
  const interesting = candidates.filter((row) => row.interesting);
  return {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    policy: {
      role: "weekly_read_only_upstream_discovery",
      upstreamWritesAllowed: false,
      niakvioCatalogWritesAllowed: false,
      autoImportAllowed: false,
      autoActivationAllowed: false,
      humanReviewRequired: true,
      p2pExcluded: true,
      interestingScoreThreshold: INTERESTING_SCORE,
    },
    configuredSourceCount: (config.upstreams ?? []).length,
    successfulSourceCount: sourceResults.filter((row) => row.status === "ok").length,
    catalogProviderCount: knownIds.size,
    newProviderCount: candidates.length,
    interestingCandidateCount: interesting.length,
    interestingCandidateIds: interesting.map((row) => row.canonicalId),
    sources: sourceResults,
    candidates,
    errors,
  };
}

function parseArgs(argv) {
  const out = { config: DEFAULT_CONFIG, catalog: DEFAULT_CATALOG, output: DEFAULT_OUTPUT, fixtureDir: "" };
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value === "--config") out.config = path.resolve(argv[++i]);
    else if (value === "--catalog") out.catalog = path.resolve(argv[++i]);
    else if (value === "--output") out.output = path.resolve(argv[++i]);
    else if (value === "--fixture-dir") out.fixtureDir = path.resolve(argv[++i]);
    else throw new Error(`unknown argument: ${value}`);
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const report = await discover({
    config: readJson(args.config),
    catalog: readJson(args.catalog),
    fixtureDir: args.fixtureDir,
  });
  writeJson(args.output, report);
  console.log(
    `FIELD_UPSTREAM_PROVIDER_DISCOVERY sources=${report.successfulSourceCount}/${report.configuredSourceCount} ` +
    `new=${report.newProviderCount} interesting=${report.interestingCandidateCount} errors=${report.errors.length} output=${path.relative(ROOT, args.output)}`
  );
  if (report.successfulSourceCount === 0) process.exitCode = 2;
}

if (path.resolve(process.argv[1] ?? "") === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error?.stack ?? error);
    process.exitCode = 1;
  });
}
