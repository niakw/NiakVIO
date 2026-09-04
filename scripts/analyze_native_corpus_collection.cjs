#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const [, , fixture, ...logs] = process.argv;
if (!fixture || logs.length === 0) {
  process.stderr.write('usage: node scripts/analyze_native_corpus_collection.cjs <fixture> <log> [log ...]\n');
  process.exit(64);
}

const analyzer = path.join(__dirname, 'analyze_native_corpus_results.cjs');
const child = spawnSync(process.execPath, [analyzer, fixture, ...logs], { encoding: 'utf8' });
if (child.stdout) process.stdout.write(child.stdout);
if (child.stderr) process.stderr.write(child.stderr);

const starts = new Map();
const ends = new Set();
const observed = new Map();
const executed = new Map();
const positive = new Map();
const mediaVerified = new Map();
const playerTerminals = new Map();
const clients = new Set();
let readableLogs = 0;
let hasCapabilityProbe = false;
for (const log of logs) {
  if (!fs.existsSync(log)) continue;
  readableLogs += 1;
  const text = fs.readFileSync(log, 'utf8');
  if (/route_mode=capability_probe(?:\s|$)/.test(text)) hasCapabilityProbe = true;
  for (const raw of text.split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    const client = f.client || '';
    const rowFixture = f.fixture || '';
    if (client) clients.add(client);
    if (rowFixture && rowFixture !== fixture) continue;
    const key = `${client}\u0000${fixture}`;
    if (line.startsWith('FIELD_NATIVE_CORPUS_BEGIN ')) {
      starts.set(key, Number(f.providers || 0));
    } else if (line.startsWith('FIELD_NATIVE_CORPUS_END ')) {
      ends.add(key);
    } else if (
      line.startsWith('FIELD_NATIVE_RESULT ') ||
      line.startsWith('FIELD_NATIVE_ERROR ') ||
      line.startsWith('FIELD_NATIVE_PROVIDER_SKIPPED ')
    ) {
      if (!observed.has(key)) observed.set(key, new Set());
      if (f.provider64) observed.get(key).add(f.provider64);
      if (line.startsWith('FIELD_NATIVE_RESULT ') || line.startsWith('FIELD_NATIVE_ERROR ')) {
        if (!executed.has(key)) executed.set(key, new Set());
        const provider = f.provider64 || f.provider || '<unknown>';
        const requestType = String(f.request_type || 'unknown').toLowerCase();
        const route = `${provider}\u0000${requestType}`;
        executed.get(key).add(route);
        if (line.startsWith('FIELD_NATIVE_RESULT ') && Number(f.count || 0) > 0) {
          if (!positive.has(key)) positive.set(key, new Set());
          positive.get(key).add(route);
        }
      }
    } else if (line.startsWith('FIELD_NATIVE_PLAYER ')) {
      if (!playerTerminals.has(key)) playerTerminals.set(key, new Set());
      const provider = f.provider64 || f.provider || '<unknown>';
      const requestType = String(f.request_type || 'unknown').toLowerCase();
      const index = Number(f.index || 0);
      const playerKey = `${provider}\u0000${requestType}\u0000${index}`;
      playerTerminals.get(key).add(playerKey);
      const state = String(f.state || 'unknown').toLowerCase();
      const failureStage = String(f.failure_stage || 'none').toLowerCase();
      if (state === 'ready' && (failureStage === 'none' || failureStage === '')) {
        if (!mediaVerified.has(key)) mediaVerified.set(key, new Set());
        mediaVerified.get(key).add(playerKey);
      }
    }
  }
}

const problems = [];
if (readableLogs === 0) problems.push('no_readable_log');
if (starts.size === 0) problems.push('missing_begin_marker');
let providersObservedCount = 0;
let executionCount = 0;
let positiveResultCount = 0;
let positiveProviderCount = 0;
let playerTerminalCount = 0;
let mediaVerifiedCount = 0;
for (const [key, expected] of starts) {
  if (!ends.has(key)) problems.push(`missing_end:${safeKey(key)}`);
  const count = observed.get(key)?.size || 0;
  const scopeExecutions = executed.get(key) || new Set();
  const scopeProviders = new Set([...scopeExecutions].map((value) => value.split('\u0000')[0]).filter(Boolean));
  const scopePositive = positive.get(key) || new Set();
  const scopePositiveProviders = new Set([...scopePositive].map((value) => value.split('\u0000')[0]).filter(Boolean));
  const scopePlayerTerminals = playerTerminals.get(key)?.size || 0;
  const scopeMediaVerified = mediaVerified.get(key)?.size || 0;
  providersObservedCount += scopeProviders.size;
  executionCount += scopeExecutions.size;
  positiveResultCount += scopePositive.size;
  positiveProviderCount += scopePositiveProviders.size;
  playerTerminalCount += scopePlayerTerminals;
  mediaVerifiedCount += scopeMediaVerified;
  if (expected <= 0) problems.push(`invalid_expected_provider_count:${safeKey(key)}`);
  else if (count < expected) problems.push(`incomplete_provider_traversal:${safeKey(key)}:${count}/${expected}`);
  if (scopeProviders.size === 0) problems.push(`zero_providers_observed:${safeKey(key)}`);
  if (scopeExecutions.size === 0) problems.push(`zero_provider_executions:${safeKey(key)}`);
  if (scopePositive.size === 0) problems.push(`zero_positive_provider_results:${safeKey(key)}`);
  if (scopePlayerTerminals === 0) problems.push(`zero_player_terminals:${safeKey(key)}`);
  if (scopeMediaVerified === 0) problems.push(`zero_media_verified:${safeKey(key)}`);
}

const anomalyStatus = Number.isInteger(child.status) ? child.status : 1;
if (anomalyStatus !== 0) problems.push(`native_result_analyzer_failed:${anomalyStatus}`);

// Media-type discovery is Brain evidence, not a provider repair. Run it only when
// the generated corpus actually exercised an undeclared tv/anime capability.
// The dedicated diagnostic is itself fail-closed on backend/frontend completeness.
if (hasCapabilityProbe && problems.length === 0) {
  const client = clients.size === 1 ? [...clients][0] : 'cross-client';
  const evidenceRoot = path.join(path.dirname(path.resolve(logs[0])), 'native-evidence', client, fixture);
  fs.mkdirSync(evidenceRoot, { recursive: true });
  const output = path.join(evidenceRoot, 'native-media-capabilities-brain.json');
  const capabilityBrain = path.join(__dirname, '..', 'engine_v2', 'scripts', 'diagnose-native-media-capabilities.mjs');
  const capability = spawnSync(process.execPath, [capabilityBrain, '--output', output, ...logs], { encoding: 'utf8' });
  if (capability.stdout) process.stdout.write(capability.stdout);
  if (capability.stderr) process.stderr.write(capability.stderr);
  const status = Number.isInteger(capability.status) ? capability.status : 2;
  if (status !== 0) problems.push(`capability_evidence_incomplete:${client}:${status}`);
  else console.log(`FIELD_NATIVE_MEDIA_CAPABILITY_ARTIFACT client=${client} fixture=${fixture} path=${output}`);
}

const complete = problems.length === 0;
console.log(
  `FIELD_NATIVE_CORPUS_COLLECTION_GATE fixture=${fixture} complete=${complete} ` +
  `analyzer_status=${anomalyStatus} capability_probe=${hasCapabilityProbe} providers_observed=${providersObservedCount} ` +
  `executions=${executionCount} positive_results=${positiveResultCount} positive_providers=${positiveProviderCount} ` +
  `player_terminals=${playerTerminalCount} media_verified=${mediaVerifiedCount} problems=${problems.length}`
);
for (const problem of problems) console.log(`FIELD_NATIVE_CORPUS_INFRA_ERROR ${problem}`);

// Traversal is not functionality. ERROR/SKIPPED/RESULT count=0 prove that a route
// was visited, but they never prove a provider or the native player works. The
// lower-level analyzer is authoritative for runtime/transport/player anomalies.
process.exitCode = complete ? 0 : 2;

function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}
function safeKey(key) {
  return key.replace(/\u0000/g, ':').replace(/[^A-Za-z0-9_.:-]/g, '_').slice(0, 160);
}
