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
const cfg = policy.coverage_preservation || {};

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

const hits = new Map();
function hit(provider, fixture, client) {
  const id = String(provider || '').toLowerCase();
  if (!id || !fixture || !client) return;
  if (!hits.has(id)) hits.set(id, new Map());
  const byFixture = hits.get(id);
  if (!byFixture.has(fixture)) byFixture.set(fixture, new Set());
  byFixture.get(fixture).add(client);
}

for (const file of listFiles(inputDir)) {
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_RESULT ');
    if (marker < 0) continue;
    const f = fields(raw.slice(marker).trim());
    if (Number(f.count || 0) <= 0) continue;
    hit(decode(f.provider64), f.fixture || '', f.client || '');
  }
}

const rows = Array.isArray(portfolio.providers) ? portfolio.providers : [];
const rowById = new Map(rows.map((row) => [String(row.provider || '').toLowerCase(), row]));
const selected = new Set((portfolio.selected || []).map((v) => String(v).toLowerCase()));
const baseSelected = new Set(selected);
const protectedByCoverage = new Map();
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
function fixturesFor(provider) {
  return [...(hits.get(provider)?.keys() || [])];
}
function isSafe(row) {
  return !!row && row.safetyEligible === true;
}
function fullHit(provider, fixture) {
  return clientsFor(provider, fixture).size >= minimumClientsActive;
}
function candidatesFor(fixture, vfOnly, fullOnly) {
  return rows
    .filter((row) => isSafe(row))
    .filter((row) => !vfOnly || row.vf === true)
    .filter((row) => fullOnly ? fullHit(String(row.provider).toLowerCase(), fixture) : clientsFor(String(row.provider).toLowerCase(), fixture).size >= minimumClientsRepair)
    .sort((a, b) => Number(b.score || 0) - Number(a.score || 0) || Number(b.catalogueCoverageRate || 0) - Number(a.catalogueCoverageRate || 0) || String(a.provider).localeCompare(String(b.provider)));
}
function selectedCount(fixture, vfOnly) {
  let count = 0;
  for (const id of selected) {
    const row = rowById.get(id);
    if (!row || !isSafe(row) || (vfOnly && row.vf !== true)) continue;
    if (fullHit(id, fixture)) count++;
  }
  return count;
}
function protect(row, fixture, reason) {
  const id = String(row.provider || '').toLowerCase();
  selected.add(id);
  if (!protectedByCoverage.has(id)) protectedByCoverage.set(id, new Set());
  protectedByCoverage.get(id).add(`${fixture}:${reason}`);
}

const fixtures = new Set();
for (const byFixture of hits.values()) for (const fixture of byFixture.keys()) fixtures.add(fixture);

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
  }
}

for (const row of rows) {
  const id = String(row.provider || '').toLowerCase();
  if (!id || !isSafe(row) || selected.has(id)) continue;
  for (const fixture of fixturesFor(id)) {
    const clients = clientsFor(id, fixture).size;
    if (clients < minimumClientsRepair || clients >= minimumClientsActive) continue;
    const safeProviders = candidatesFor(fixture, false, false).length;
    const safeVfProviders = row.vf === true ? candidatesFor(fixture, true, false).length : 999;
    if (safeProviders <= rareGeneral || safeVfProviders <= rareVf || selectedCount(fixture, false) < minGeneral || (row.vf === true && selectedCount(fixture, true) < minVf)) {
      if (!repairPriority.has(id)) repairPriority.set(id, new Set());
      repairPriority.get(id).add(fixture);
    }
  }
}

for (const row of rows) {
  const id = String(row.provider || '').toLowerCase();
  row.coverageProtectionFixtures = [...(protectedByCoverage.get(id) || [])];
  row.repairPriorityFixtures = [...(repairPriority.get(id) || [])];
  if (protectedByCoverage.has(id) && !baseSelected.has(id)) row.recommendation = 'active_coverage_guard';
  else if (repairPriority.has(id) && !selected.has(id)) row.recommendation = 'repair_priority_unique_coverage';
}

const orderedSelected = rows.filter((row) => selected.has(String(row.provider || '').toLowerCase())).map((row) => String(row.provider).toLowerCase());
portfolio.schemaVersion = Math.max(Number(portfolio.schemaVersion || 1), 2);
portfolio.selected = orderedSelected;
portfolio.recommendedActive = orderedSelected.length;
portfolio.recommendedReductionObserved = Math.max(0, Number(portfolio.currentlyActiveObserved || 0) - orderedSelected.length);
portfolio.recommendedVf = rows.filter((row) => selected.has(String(row.provider || '').toLowerCase()) && row.vf === true).length;
portfolio.protectedCoverageProviders = [...protectedByCoverage.keys()].sort();
portfolio.repairPriorityProviders = [...repairPriority.keys()].sort();
portfolio.normalPortfolioMax = Number(policy.portfolio?.normal_max_unique_active || policy.portfolio?.target_unique_active || 45);
portfolio.coverageOverrideAboveNormalMax = orderedSelected.length > portfolio.normalPortfolioMax;
portfolio.coveragePolicy = cfg;
fs.writeFileSync(portfolioPath, JSON.stringify(portfolio, null, 2) + '\n');
console.log(`FIELD_PROVIDER_COVERAGE_GUARD ${JSON.stringify({ recommendedActive: portfolio.recommendedActive, protectedCoverageProviders: portfolio.protectedCoverageProviders, repairPriorityProviders: portfolio.repairPriorityProviders, coverageOverrideAboveNormalMax: portfolio.coverageOverrideAboveNormalMax })}`);
