#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { streamIdentity } = require('./nuvio_client_lab.cjs');

const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}
const inputDir = path.resolve(arg('--dir', process.cwd()));
const outputPath = path.resolve(arg('--output', path.join(inputDir, 'provider-portfolio.json')));
const corpus = JSON.parse(fs.readFileSync(path.join(root, '.github/triggers/nuvio-client-lab.json'), 'utf8'));
const policy = JSON.parse(fs.readFileSync(path.join(root, '.github/provider-portfolio-policy.json'), 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const vfPath = path.join(root, 'vf', 'manifest.json');
const vfManifest = fs.existsSync(vfPath) ? JSON.parse(fs.readFileSync(vfPath, 'utf8')) : { scrapers: [] };
const overridesPath = path.join(root, 'provider-overrides.json');
const overrides = fs.existsSync(overridesPath) ? JSON.parse(fs.readFileSync(overridesPath, 'utf8')) : {};

const fixtureMap = new Map((corpus.fixtures || []).map((row) => [row.slug, row.fixture || {}]));
const manifestMap = new Map((manifest.scrapers || []).filter(Boolean).map((row) => [String(row.id || '').toLowerCase(), row]));
const vfSet = new Set((vfManifest.scrapers || []).filter(Boolean).map((row) => String(row.id || '').toLowerCase()).filter(Boolean));
const providerPatches = overrides.provider_patches || {};
const configuredCapabilities = overrides.provider_capabilities || {};
const minRatio = Number(corpus.policy?.minimum_duration_ratio || 0.55);
const maxRatio = Number(corpus.policy?.maximum_duration_ratio || 1.8);
const cfg = policy.eligibility || {};
const weights = policy.score_weights || {};

function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}
function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let m;
  while ((m = re.exec(line)) !== null) out[m[1]] = m[2];
  return out;
}
function listFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listFiles(full));
    else if (entry.isFile() && /(?:desktop|mobile|tv)-native-corpus-.*\.log$/i.test(entry.name)) out.push(full);
  }
  return out.sort();
}
function providerPolicy(provider) {
  const id = String(provider || '').toLowerCase();
  const manifestRow = manifestMap.get(id) || {};
  const patch = providerPatches[id] || {};
  const configured = configuredCapabilities[id] || {};
  const strategy = String(patch.capability || (typeof configured === 'object' ? configured.strategy : configured) || manifestRow.capability || 'unknown');
  const allowEmbed = strategy === 'iframe_player' || (strategy === 'mixed_embed_resolver' && (manifestRow.supportsExternalPlayer === true || patch.preserve_embed_urls === true));
  return { strategy, allowEmbed };
}
function relevant(provider, fixture) {
  const row = manifestMap.get(String(provider || '').toLowerCase());
  const published = Array.isArray(row?.published_types) ? row.published_types.map((v) => String(v).toLowerCase()) : [];
  if (!published.length) return true;
  const category = String(fixture?.category || fixture?.mediaType || '').toLowerCase();
  if (category === 'anime') return published.includes('anime') || published.includes('tv');
  return published.includes(category);
}
function key(client, fixture, provider) { return `${client}\u0000${fixture}\u0000${String(provider || '').toLowerCase()}`; }
function clamp01(v) { return Math.max(0, Math.min(1, Number(v) || 0)); }
function round(v, n = 4) { const p = 10 ** n; return Math.round((Number(v) || 0) * p) / p; }

const executions = new Map();
const streamRows = [];
const transports = new Map();
const runtimeErrors = new Set();
for (const file of listFiles(inputDir)) {
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    if (line.startsWith('FIELD_NATIVE_RESULT ')) {
      const provider = decode(f.provider64);
      executions.set(key(f.client, f.fixture, provider), {
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        enabled: f.enabled === 'true', count: Number(f.count || 0), durationMs: Number(f.duration_ms || 0),
      });
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      streamRows.push({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64), index: Number(f.index || 0),
        stream: { title: decode(f.title64), name: decode(f.name64), quality: decode(f.quality64), language: decode(f.language64), type: decode(f.type64), url: `https://${decode(f.host64)}/${encodeURIComponent(decode(f.media_hint64))}` },
      });
    } else if (line.startsWith('FIELD_NATIVE_TRANSPORT ')) {
      const provider = decode(f.provider64);
      transports.set(key(f.client, f.fixture, provider), {
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        state: f.state || 'unknown', kind: f.kind || 'unknown', status: Number(f.status || 0),
        durationSeconds: Number(f.duration_seconds || 0) || null,
      });
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      runtimeErrors.add(key(f.client, f.fixture, decode(f.provider64)));
    }
  }
}

const contradictions = new Set();
for (const row of streamRows) {
  const fixture = fixtureMap.get(row.fixture) || {};
  let identity = streamIdentity(row.stream, fixture);
  const transport = transports.get(key(row.client, row.fixture, row.provider));
  const expected = Number(fixture.expectedDurationMinutes || 0) * 60 || null;
  const ratio = expected && transport?.durationSeconds ? transport.durationSeconds / expected : null;
  if (row.index === 0 && ratio != null && (ratio < minRatio || ratio > maxRatio)) identity = { status: 'contradiction' };
  if (identity.status === 'contradiction') contradictions.add(key(row.client, row.fixture, row.provider));
}

const transportFailures = new Set();
const transportSuccesses = new Set();
for (const [k, row] of transports) {
  const pp = providerPolicy(row.provider);
  const expectedEmbed = row.state === 'dead' && row.kind === 'html' && pp.allowEmbed;
  if ((row.state === 'dead' || row.state === 'error') && !expectedEmbed) transportFailures.add(k);
  else if (row.state === 'ok' || expectedEmbed) transportSuccesses.add(k);
}

const byProvider = new Map();
for (const [k, ex] of executions) {
  const id = String(ex.provider || '').toLowerCase();
  const fixture = fixtureMap.get(ex.fixture) || {};
  if (!relevant(id, fixture)) continue;
  if (!byProvider.has(id)) byProvider.set(id, []);
  byProvider.get(id).push({ ...ex, k });
}

const rows = [];
for (const [id, values] of byProvider) {
  const manifestRow = manifestMap.get(id) || {};
  const opportunities = values.length;
  const usable = values.filter((v) => v.count > 0 && !contradictions.has(v.k) && !transportFailures.has(v.k) && !runtimeErrors.has(v.k));
  const coverageRate = opportunities ? usable.length / opportunities : 0;
  const fixtureGroups = new Map();
  for (const v of values) {
    if (!fixtureGroups.has(v.fixture)) fixtureGroups.set(v.fixture, []);
    fixtureGroups.get(v.fixture).push(v);
  }
  let crossEligible = 0;
  let crossHits = 0;
  for (const group of fixtureGroups.values()) {
    const clients = new Set(group.map((v) => v.client));
    if (!['desktop', 'mobile', 'tv'].every((c) => clients.has(c))) continue;
    crossEligible++;
    if (['desktop', 'mobile', 'tv'].every((c) => group.some((v) => v.client === c && usable.some((u) => u.k === v.k)))) crossHits++;
  }
  const crossRate = crossEligible ? crossHits / crossEligible : 0;
  const transportRows = values.filter((v) => transports.has(v.k));
  const transportRate = transportRows.length ? transportRows.filter((v) => transportSuccesses.has(v.k)).length / transportRows.length : coverageRate;
  const avgMs = opportunities ? values.reduce((sum, v) => sum + Math.max(0, v.durationMs), 0) / opportunities : 0;
  const slowThreshold = Number(cfg.slow_execution_ms || 30000);
  const slowCount = values.filter((v) => v.durationMs >= slowThreshold).length;
  const slowRate = opportunities ? slowCount / opportunities : 1;
  const latencyRate = clamp01(1 - avgMs / slowThreshold);
  const contradictionCount = values.filter((v) => contradictions.has(v.k)).length;
  const transportFailureCount = values.filter((v) => transportFailures.has(v.k)).length;
  const runtimeErrorCount = values.filter((v) => runtimeErrors.has(v.k)).length;
  const published = Array.isArray(manifestRow.published_types) ? manifestRow.published_types.map((v) => String(v).toLowerCase()) : [];
  const animeSpecialist = published.length > 0 && published.every((v) => v === 'anime' || v === 'tv') && published.includes('anime');
  const movieTvCore = !animeSpecialist && (!published.length || published.includes('movie') || published.includes('tv'));
  const vf = vfSet.has(id);
  const score =
    clamp01(coverageRate) * Number(weights.catalogue_coverage || 50) +
    clamp01(crossRate) * Number(weights.cross_platform_consistency || 25) +
    clamp01(transportRate) * Number(weights.transport_success || 12) +
    latencyRate * Number(weights.latency || 8) +
    (vf ? Number(weights.vf_value || 3) : 0) +
    (animeSpecialist ? Number(weights.specialist_value || 2) : 0);

  // Content safety is absolute: a provider that serves the wrong work must be
  // quarantined. Native transport/runtime failures are different: they are
  // reliability defects to repair, especially when the provider carries rare
  // catalogue/VF coverage, and must not be mislabeled as unsafe content.
  const contentSafetyEligible = contradictionCount <= Number(cfg.maximum_identity_contradictions || 0);
  const nativeReliabilityEligible = transportFailureCount <= Number(cfg.maximum_transport_failures || 0) && runtimeErrorCount <= Number(cfg.maximum_runtime_errors || 0);
  const safetyEligible = contentSafetyEligible;
  const evidenceEnough = opportunities >= Number(cfg.minimum_relevant_executions || 6);
  const qualityEligible = contentSafetyEligible && nativeReliabilityEligible && evidenceEnough && coverageRate >= Number(cfg.minimum_catalogue_coverage_rate || 0.5) && crossRate >= Number(cfg.minimum_cross_platform_fixture_rate || 0.5) && slowRate <= Number(cfg.maximum_slow_execution_rate || 0.25);
  rows.push({
    provider: id,
    currentlyActive: manifestRow.enabled !== false,
    vf,
    animeSpecialist,
    movieTvCore,
    capability: providerPolicy(id).strategy,
    opportunities,
    usableExecutions: usable.length,
    catalogueCoverageRate: round(coverageRate),
    crossPlatformFixtures: crossEligible,
    crossPlatformHits: crossHits,
    crossPlatformFixtureRate: round(crossRate),
    transportSuccessRate: round(transportRate),
    averageDurationMs: Math.round(avgMs),
    slowExecutionRate: round(slowRate),
    identityContradictions: contradictionCount,
    transportFailures: transportFailureCount,
    runtimeErrors: runtimeErrorCount,
    contentSafetyEligible,
    nativeReliabilityEligible,
    safetyEligible,
    evidenceEnough,
    qualityEligible,
    score: round(score, 2),
  });
}

rows.sort((a, b) => b.score - a.score || b.catalogueCoverageRate - a.catalogueCoverageRate || a.averageDurationMs - b.averageDurationMs || a.provider.localeCompare(b.provider));
const target = Number(policy.portfolio?.target_unique_active || 36);
const hardMax = Number(policy.portfolio?.hard_max_unique_active || 45);
const minVf = Number(policy.portfolio?.minimum_vf_unique || 10);
const minAnime = Number(policy.portfolio?.minimum_anime_specialists || 5);
const minMovieTv = Number(policy.portfolio?.minimum_movie_tv_core || 10);
const eligible = rows.filter((r) => r.qualityEligible);
const selected = [];
const selectedIds = new Set();
function add(row) {
  if (!row || selectedIds.has(row.provider) || selected.length >= hardMax) return false;
  selectedIds.add(row.provider); selected.push(row); return true;
}
for (const row of eligible.slice(0, target)) add(row);
function ensure(predicate, minimum) {
  let have = selected.filter(predicate).length;
  if (have >= minimum) return;
  for (const row of eligible) {
    if (have >= minimum || selected.length >= hardMax) break;
    if (predicate(row) && add(row)) have++;
  }
}
ensure((r) => r.vf, minVf);
ensure((r) => r.animeSpecialist, minAnime);
ensure((r) => r.movieTvCore, minMovieTv);

for (const row of rows) {
  row.recommendation = selectedIds.has(row.provider) ? 'active_core'
    : !row.contentSafetyEligible ? 'quarantine_unsafe'
    : !row.nativeReliabilityEligible ? 'repair_runtime_or_transport'
    : !row.evidenceEnough ? 'lab_only_insufficient_evidence'
    : !row.qualityEligible ? 'lab_only_low_coverage_or_stability'
    : 'lab_only_redundant';
}
const currentActive = rows.filter((r) => r.currentlyActive).length;
const output = {
  schemaVersion: 2,
  generatedAt: new Date().toISOString(),
  policy,
  observedProviders: rows.length,
  currentlyActiveObserved: currentActive,
  recommendedActive: selected.length,
  recommendedReductionObserved: Math.max(0, currentActive - selected.length),
  recommendedVf: selected.filter((r) => r.vf).length,
  recommendedAnimeSpecialists: selected.filter((r) => r.animeSpecialist).length,
  recommendedMovieTvCore: selected.filter((r) => r.movieTvCore).length,
  selected: selected.map((r) => r.provider),
  providers: rows,
};
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(output, null, 2) + '\n');
console.log(`FIELD_PROVIDER_PORTFOLIO ${JSON.stringify({ observedProviders: output.observedProviders, currentlyActiveObserved: output.currentlyActiveObserved, recommendedActive: output.recommendedActive, recommendedReductionObserved: output.recommendedReductionObserved, recommendedVf: output.recommendedVf, recommendedAnimeSpecialists: output.recommendedAnimeSpecialists })}`);
for (const row of rows.slice(0, 60)) console.log(`FIELD_PROVIDER_PORTFOLIO_ROW ${JSON.stringify(row)}`);
