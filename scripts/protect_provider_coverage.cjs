#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
function arg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}
const inputDir = path.resolve(arg('--dir', process.cwd()));
const portfolioPath = path.resolve(arg('--portfolio', path.join(inputDir, 'provider-portfolio.json')));
const policy = JSON.parse(fs.readFileSync(path.join(root, '.github/provider-portfolio-policy.json'), 'utf8'));
const portfolio = JSON.parse(fs.readFileSync(portfolioPath, 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const overridesPath = path.join(root, 'provider-overrides.json');
const overrides = fs.existsSync(overridesPath) ? JSON.parse(fs.readFileSync(overridesPath, 'utf8')) : {};
const cfg = policy.coverage_preservation || {};
const manifestMap = new Map((manifest.scrapers || []).filter(Boolean).map((row) => [String(row.id || '').toLowerCase(), row]));
const providerPatches = overrides.provider_patches || {};
const configuredCapabilities = overrides.provider_capabilities || {};

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
function normalize(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}
function frenchAudioEvidence(f) {
  const language = normalize(decode(f.language64));
  const labels = normalize(`${decode(f.title64)} ${decode(f.name64)} ${language}`);
  if (/\bvostfr\b|\bvost\b|\bsub(?:bed|title|titles)?\b|sous[- ]?titr/.test(labels)) return false;
  if (/^(?:fr|fr-fr|fra|fre|french|francais|vf|truefrench)$/.test(language)) return true;
  return /\b(?:truefrench|vf|french audio|audio fr|audio francais|francais)\b/.test(labels);
}
function key(client, fixture, provider) {
  return `${client}\u0000${fixture}\u0000${String(provider || '').toLowerCase()}`;
}
function providerAllowsEmbed(provider) {
  const id = String(provider || '').toLowerCase();
  const manifestRow = manifestMap.get(id) || {};
  const patch = providerPatches[id] || {};
  const configured = configuredCapabilities[id] || {};
  const strategy = String(patch.capability || (typeof configured === 'object' ? configured.strategy : configured) || manifestRow.capability || 'unknown');
  return strategy === 'iframe_player' || (strategy === 'mixed_embed_resolver' && (manifestRow.supportsExternalPlayer === true || patch.preserve_embed_urls === true));
}

const rawResults = new Map();
const rowVfEvidence = new Set();
const runtimeErrors = new Set();
const transports = new Map();
for (const file of listFiles(inputDir)) {
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const resultMarker = raw.indexOf('FIELD_NATIVE_RESULT ');
    if (resultMarker >= 0) {
      const f = fields(raw.slice(resultMarker).trim());
      const provider = decode(f.provider64);
      rawResults.set(key(f.client || '', f.fixture || '', provider), {
        client: f.client || '', fixture: f.fixture || '', provider,
        count: Number(f.count || 0),
      });
      continue;
    }
    const rowMarker = raw.indexOf('FIELD_NATIVE_ROW ');
    if (rowMarker >= 0) {
      const f = fields(raw.slice(rowMarker).trim());
      const provider = decode(f.provider64);
      if (frenchAudioEvidence(f)) rowVfEvidence.add(key(f.client || '', f.fixture || '', provider));
      continue;
    }
    const transportMarker = raw.indexOf('FIELD_NATIVE_TRANSPORT ');
    if (transportMarker >= 0) {
      const f = fields(raw.slice(transportMarker).trim());
      const provider = decode(f.provider64);
      transports.set(key(f.client || '', f.fixture || '', provider), {
        state: String(f.state || 'unknown').toLowerCase(),
        kind: String(f.kind || 'unknown').toLowerCase(),
        provider,
      });
      continue;
    }
    const errorMarker = raw.indexOf('FIELD_NATIVE_ERROR ');
    if (errorMarker >= 0) {
      const f = fields(raw.slice(errorMarker).trim());
      runtimeErrors.add(key(f.client || '', f.fixture || '', decode(f.provider64)));
    }
  }
}

function transportUsable(k, provider) {
  const transport = transports.get(k);
  if (!transport) return true;
  if (transport.state === 'ok') return true;
  if (transport.state === 'dead' && transport.kind === 'html' && providerAllowsEmbed(provider)) return true;
  return transport.state !== 'dead' && transport.state !== 'error';
}
function executionUsable(k, result) {
  return !!result && result.count > 0 && !runtimeErrors.has(k) && transportUsable(k, result.provider);
}

const hits = new Map();
const vfHits = new Map();
const observedAttempts = new Map();
function hitInto(store, provider, fixture, client) {
  const id = String(provider || '').toLowerCase();
  if (!id || !fixture || !client) return;
  if (!store.has(id)) store.set(id, new Map());
  const byFixture = store.get(id);
  if (!byFixture.has(fixture)) byFixture.set(fixture, new Set());
  byFixture.get(fixture).add(client);
}
for (const [k, result] of rawResults) {
  hitInto(observedAttempts, result.provider, result.fixture, result.client);
  if (!executionUsable(k, result)) continue;
  hitInto(hits, result.provider, result.fixture, result.client);
  if (rowVfEvidence.has(k)) hitInto(vfHits, result.provider, result.fixture, result.client);
}

const rows = Array.isArray(portfolio.providers) ? portfolio.providers : [];
const rowById = new Map(rows.map((row) => [String(row.provider || '').toLowerCase(), row]));
const selected = new Set((portfolio.selected || []).map((v) => String(v).toLowerCase()));
const baseSelected = new Set(selected);
const protectedByCoverage = new Map();
const protectedByVfCoverage = new Map();
const repairPriority = new Map();
const minimumClientsActive = Number(cfg.minimum_clients_for_active_guard || 3);
const minimumClientsRepair = Number(cfg.minimum_clients_for_repair_priority || 1);
const minGeneral = Number(cfg.minimum_provider_redundancy_per_fixture || 2);
const minVf = Number(cfg.minimum_vf_provider_redundancy_per_fixture || 2);
const rareGeneral = Number(cfg.rare_fixture_provider_threshold || 2);
const rareVf = Number(cfg.rare_vf_fixture_provider_threshold || 2);

function clientsFor(provider, fixture) {
  return hits.get(provider)?.get(fixture) || new Set();
}
function attemptedClientsFor(provider, fixture) {
  return observedAttempts.get(provider)?.get(fixture) || new Set();
}
function vfClientsFor(provider, fixture) {
  return vfHits.get(provider)?.get(fixture) || new Set();
}
function fixturesFor(provider) {
  const all = new Set([...(hits.get(provider)?.keys() || []), ...(observedAttempts.get(provider)?.keys() || [])]);
  return [...all];
}
function isSafe(row) {
  return !!row && (row.contentSafetyEligible === true || (row.contentSafetyEligible == null && row.safetyEligible === true));
}
function fullHit(provider, fixture) {
  return clientsFor(provider, fixture).size >= minimumClientsActive;
}
function fullVfHit(provider, fixture) {
  return vfClientsFor(provider, fixture).size >= minimumClientsActive;
}
function candidatesFor(fixture, vfOnly, fullOnly) {
  return rows
    .filter((row) => isSafe(row))
    .filter((row) => {
      const id = String(row.provider || '').toLowerCase();
      const clients = vfOnly ? vfClientsFor(id, fixture) : clientsFor(id, fixture);
      return fullOnly ? clients.size >= minimumClientsActive : clients.size >= minimumClientsRepair;
    })
    .sort((a, b) => Number(b.score || 0) - Number(a.score || 0) || Number(b.catalogueCoverageRate || 0) - Number(a.catalogueCoverageRate || 0) || String(a.provider).localeCompare(String(b.provider)));
}
function selectedCount(fixture, vfOnly) {
  let count = 0;
  for (const id of selected) {
    const row = rowById.get(id);
    if (!row || !isSafe(row)) continue;
    if (vfOnly ? fullVfHit(id, fixture) : fullHit(id, fixture)) count++;
  }
  return count;
}
function markCoverage(row, fixture, reason) {
  const id = String(row.provider || '').toLowerCase();
  if (!protectedByCoverage.has(id)) protectedByCoverage.set(id, new Set());
  protectedByCoverage.get(id).add(`${fixture}:${reason}`);
}
function markVfCoverage(row, fixture, reason) {
  const id = String(row.provider || '').toLowerCase();
  markCoverage(row, fixture, reason);
  if (!protectedByVfCoverage.has(id)) protectedByVfCoverage.set(id, new Set());
  protectedByVfCoverage.get(id).add(fixture);
}
function protect(row, fixture, reason) {
  selected.add(String(row.provider || '').toLowerCase());
  if (reason === 'vf_redundancy') markVfCoverage(row, fixture, reason);
  else markCoverage(row, fixture, reason);
}

const fixtures = new Set();
for (const byFixture of observedAttempts.values()) for (const fixture of byFixture.keys()) fixtures.add(fixture);

for (const fixture of [...fixtures].sort()) {
  while (selectedCount(fixture, false) < minGeneral) {
    const next = candidatesFor(fixture, false, true).find((row) => !selected.has(String(row.provider).toLowerCase()));
    if (!next) break;
    protect(next, fixture, 'general_redundancy');
  }
  const vfCandidates = candidatesFor(fixture, true, true);
  if (vfCandidates.length) {
    while (selectedCount(fixture, true) < minVf) {
      const next = vfCandidates.find((row) => !selected.has(String(row.provider).toLowerCase()));
      if (!next) break;
      protect(next, fixture, 'vf_redundancy');
    }
    if (vfCandidates.length <= minVf) {
      for (const row of vfCandidates) {
        if (selected.has(String(row.provider || '').toLowerCase())) markVfCoverage(row, fixture, 'vf_scarcity');
      }
    }
  }
}

for (const row of rows) {
  const id = String(row.provider || '').toLowerCase();
  if (!id || !isSafe(row)) continue;
  for (const fixture of fixturesFor(id)) {
    const workingClients = clientsFor(id, fixture).size;
    const attemptedClients = attemptedClientsFor(id, fixture).size;
    if (attemptedClients < minimumClientsRepair || workingClients >= minimumClientsActive) continue;
    const hasAnyWorking = workingClients >= minimumClientsRepair;
    const partialVfClients = vfClientsFor(id, fixture).size;
    const hasPartialVf = partialVfClients >= minimumClientsRepair;
    const safeProviders = candidatesFor(fixture, false, false).length;
    const safeVfProviders = hasPartialVf ? candidatesFor(fixture, true, false).length : 999;
    const runtimeOrTransportBroken = [...attemptedClientsFor(id, fixture)].some((client) => {
      const k = key(client, fixture, id);
      const result = rawResults.get(k);
      return !!result && result.count > 0 && !executionUsable(k, result);
    });
    if (
      runtimeOrTransportBroken ||
      (hasAnyWorking && safeProviders <= rareGeneral) ||
      (hasPartialVf && safeVfProviders <= rareVf) ||
      (hasAnyWorking && selectedCount(fixture, false) < minGeneral) ||
      (hasPartialVf && selectedCount(fixture, true) < minVf)
    ) {
      if (!repairPriority.has(id)) repairPriority.set(id, new Set());
      repairPriority.get(id).add(fixture);
    }
  }
}

for (const row of rows) {
  const id = String(row.provider || '').toLowerCase();
  row.coverageProtectionFixtures = [...(protectedByCoverage.get(id) || [])];
  row.vfCoverageProtectionFixtures = [...(protectedByVfCoverage.get(id) || [])];
  row.repairPriorityFixtures = [...(repairPriority.get(id) || [])];
  row.observedVfFixtures = fixturesFor(id).filter((fixture) => vfClientsFor(id, fixture).size >= minimumClientsRepair);
  row.fullCrossPlatformVfFixtures = fixturesFor(id).filter((fixture) => fullVfHit(id, fixture));
  row.fullCrossPlatformCoverageFixtures = fixturesFor(id).filter((fixture) => fullHit(id, fixture));
  if (protectedByCoverage.has(id) && !baseSelected.has(id)) row.recommendation = 'active_coverage_guard';
  else if (repairPriority.has(id) && !selected.has(id)) row.recommendation = 'repair_priority_unique_coverage';
  else if (repairPriority.has(id) && selected.has(id)) row.repairPriority = true;
}

const orderedSelected = rows.filter((row) => selected.has(String(row.provider || '').toLowerCase())).map((row) => String(row.provider).toLowerCase());
portfolio.schemaVersion = Math.max(Number(portfolio.schemaVersion || 1), 4);
portfolio.selected = orderedSelected;
portfolio.recommendedActive = orderedSelected.length;
portfolio.recommendedReductionObserved = Math.max(0, Number(portfolio.currentlyActiveObserved || 0) - orderedSelected.length);
portfolio.recommendedVf = rows.filter((row) => selected.has(String(row.provider || '').toLowerCase()) && (row.fullCrossPlatformVfFixtures || []).length > 0).length;
portfolio.protectedCoverageProviders = [...protectedByCoverage.keys()].sort();
portfolio.protectedVfCoverageProviders = [...protectedByVfCoverage.keys()].sort();
portfolio.repairPriorityProviders = [...repairPriority.keys()].sort();
portfolio.normalPortfolioMax = Number(policy.portfolio?.normal_max_unique_active || policy.portfolio?.target_unique_active || 45);
portfolio.coverageOverrideAboveNormalMax = orderedSelected.length > portfolio.normalPortfolioMax;
portfolio.coverageEvidence = 'FIELD_NATIVE_RESULT count plus usable transport/runtime evidence per fixture and client; broken executions do not count as successful coverage';
portfolio.vfCoverageEvidence = 'usable FIELD_NATIVE_ROW language/title evidence per fixture and client; VOSTFR/subtitle-only or broken executions do not count as VF';
portfolio.coveragePolicy = cfg;
fs.writeFileSync(portfolioPath, JSON.stringify(portfolio, null, 2) + '\n');
console.log(`FIELD_PROVIDER_COVERAGE_GUARD ${JSON.stringify({ recommendedActive: portfolio.recommendedActive, recommendedVf: portfolio.recommendedVf, protectedCoverageProviders: portfolio.protectedCoverageProviders, protectedVfCoverageProviders: portfolio.protectedVfCoverageProviders, repairPriorityProviders: portfolio.repairPriorityProviders, coverageOverrideAboveNormalMax: portfolio.coverageOverrideAboveNormalMax })}`);
