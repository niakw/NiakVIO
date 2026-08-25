#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const RUNTIME_ERROR_SENTINEL = '__NIAKVIO_RUNTIME_ERROR__';
const argv = process.argv.slice(2);
let inputDir = '';
let requiredClients = [];
let minComparisons = 3;
let failureRatio = 0.8;
const explicitFiles = [];

for (let i = 0; i < argv.length; i += 1) {
  const arg = argv[i];
  if (arg === '--dir') inputDir = argv[++i] || '';
  else if (arg === '--require-clients') requiredClients = String(argv[++i] || '').split(',').map((v) => v.trim().toLowerCase()).filter(Boolean);
  else if (arg === '--min-comparisons') minComparisons = Math.max(1, Number(argv[++i] || 3) || 3);
  else if (arg === '--failure-ratio') failureRatio = Math.min(1, Math.max(0.5, Number(argv[++i] || 0.8) || 0.8));
  else if (arg.startsWith('--')) {
    console.error(`unknown argument: ${arg}`);
    process.exit(64);
  } else explicitFiles.push(path.resolve(arg));
}

function listLogs(root) {
  const output = [];
  if (!root || !fs.existsSync(root)) return output;
  const stack = [path.resolve(root)];
  while (stack.length) {
    const current = stack.pop();
    const stat = fs.statSync(current);
    if (stat.isDirectory()) {
      for (const name of fs.readdirSync(current)) stack.push(path.join(current, name));
    } else if (stat.isFile() && /(?:desktop|mobile|tv)-native-corpus-.*\.log$/i.test(path.basename(current))) {
      output.push(current);
    }
  }
  return output.sort();
}

const files = [...new Set([...explicitFiles, ...listLogs(inputDir)])];
if (!files.length) {
  console.error('FIELD_NATIVE_CROSS_RUNTIME_GATE state=infra_error reason=no_native_corpus_logs blocking=true owner=lab_infra');
  process.exit(2);
}

function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}
function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}
function normalizedClient(value) {
  const client = String(value || 'unknown').trim().toLowerCase();
  if (client === 'macos' || client === 'windows' || client === 'linux') return 'desktop';
  return client;
}
function routeKey(f) {
  const provider = decode(f.provider64) || String(f.provider || '').trim();
  return [String(f.fixture || 'unknown'), provider.toLowerCase(), String(f.request_type || 'unknown').toLowerCase()].join('\u0000');
}
function routeLabel(key) {
  return key.split('\u0000').join(':');
}

const routes = new Map();
const clientsSeen = new Set();
let readable = 0;
let resultRows = 0;
let sentinelRows = 0;
let explicitRuntimeErrors = 0;

function observation(key, client) {
  if (!routes.has(key)) routes.set(key, new Map());
  const byClient = routes.get(key);
  if (!byClient.has(client)) byClient.set(client, { count: null, runtimeError: false, sentinel: false });
  return byClient.get(client);
}

for (const file of files) {
  if (!fs.existsSync(file)) continue;
  readable += 1;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    const client = normalizedClient(f.client);
    if (client && client !== 'unknown') clientsSeen.add(client);

    if (line.startsWith('FIELD_NATIVE_RESULT ')) {
      if (String(f.route_mode || 'declared').toLowerCase() === 'capability_probe') continue;
      const row = observation(routeKey(f), client);
      row.count = Math.max(0, Number(f.count ?? f.returned ?? 0) || 0);
      resultRows += 1;
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      if (String(f.route_mode || 'declared').toLowerCase() === 'capability_probe') continue;
      const row = observation(routeKey(f), client);
      row.runtimeError = true;
      if (row.count == null) row.count = 0;
      explicitRuntimeErrors += 1;
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      if (String(f.route_mode || 'declared').toLowerCase() === 'capability_probe') continue;
      const type = decode(f.type64);
      const title = decode(f.title64);
      if (type !== RUNTIME_ERROR_SENTINEL && title !== RUNTIME_ERROR_SENTINEL) continue;
      const row = observation(routeKey(f), client);
      row.runtimeError = true;
      row.sentinel = true;
      sentinelRows += 1;
    }
  }
}

if (!readable || !resultRows) {
  console.error(
    `FIELD_NATIVE_CROSS_RUNTIME_GATE state=infra_error reason=missing_runtime_results ` +
    `logs=${readable} results=${resultRows} blocking=true owner=lab_infra`
  );
  process.exit(2);
}

if (!requiredClients.length) requiredClients = [...clientsSeen].sort();
requiredClients = [...new Set(requiredClients)];
const missingClients = requiredClients.filter((client) => !clientsSeen.has(client));
if (missingClients.length) {
  console.error(
    `FIELD_NATIVE_CROSS_RUNTIME_GATE state=infra_error reason=missing_required_clients ` +
    `required=${requiredClients.join(',')} seen=${[...clientsSeen].sort().join(',')} ` +
    `missing=${missingClients.join(',')} blocking=true owner=lab_infra`
  );
  process.exit(2);
}
if (requiredClients.length < 2) {
  console.error(
    `FIELD_NATIVE_CROSS_RUNTIME_GATE state=infra_error reason=need_multiple_clients ` +
    `required=${requiredClients.join(',')} blocking=true owner=lab_infra`
  );
  process.exit(2);
}

function healthy(row) {
  return Boolean(row && !row.runtimeError && Number(row.count || 0) > 0);
}
function failed(row) {
  return Boolean(row && (row.runtimeError || Number(row.count || 0) === 0));
}

const clientStats = Object.fromEntries(requiredClients.map((client) => [client, {
  comparisons: 0,
  failuresAgainstHealthyPeer: 0,
  healthyAgainstPeer: 0,
  sentinelFailures: 0,
}]));
const divergences = [];
let comparableRoutes = 0;

for (const [key, byClient] of routes) {
  const available = requiredClients.filter((client) => byClient.has(client));
  if (available.length < 2) continue;
  let routeCompared = false;
  for (const client of requiredClients) {
    const own = byClient.get(client);
    if (!own) continue;
    const healthyPeers = requiredClients.filter((peer) => peer !== client && healthy(byClient.get(peer)));
    if (!healthyPeers.length) continue;
    routeCompared = true;
    const stats = clientStats[client];
    stats.comparisons += 1;
    if (failed(own)) {
      stats.failuresAgainstHealthyPeer += 1;
      if (own.sentinel) stats.sentinelFailures += 1;
      divergences.push({
        route: routeLabel(key),
        client,
        peers: healthyPeers,
        count: Number(own.count || 0),
        runtimeError: own.runtimeError,
        runtimeSentinel: own.sentinel,
      });
    } else {
      stats.healthyAgainstPeer += 1;
    }
  }
  if (routeCompared) comparableRoutes += 1;
}

if (comparableRoutes < minComparisons) {
  console.error(
    `FIELD_NATIVE_CROSS_RUNTIME_GATE state=infra_error reason=insufficient_comparable_routes ` +
    `comparable=${comparableRoutes} minimum=${minComparisons} required=${requiredClients.join(',')} ` +
    `blocking=true owner=lab_infra`
  );
  process.exit(2);
}

const systemic = [];
for (const client of requiredClients) {
  const stats = clientStats[client];
  const ratio = stats.comparisons ? stats.failuresAgainstHealthyPeer / stats.comparisons : 0;
  if (stats.comparisons >= minComparisons && stats.failuresAgainstHealthyPeer >= minComparisons && ratio >= failureRatio) {
    systemic.push({ client, ...stats, failureRatio: ratio });
  }
}

if (systemic.length) {
  console.error(
    `FIELD_NATIVE_CROSS_RUNTIME_GATE state=failed reason=systemic_cross_client_divergence ` +
    `clients=${systemic.map((row) => row.client).join(',')} comparable=${comparableRoutes} ` +
    `runtime_sentinels=${sentinelRows} explicit_runtime_errors=${explicitRuntimeErrors} ` +
    `blocking=true owner=runtime_contract`
  );
  for (const row of systemic) {
    console.error(`FIELD_NATIVE_CROSS_RUNTIME_CLIENT ${JSON.stringify(row)}`);
  }
  for (const row of divergences.slice(0, 80)) {
    console.error(`FIELD_NATIVE_CROSS_RUNTIME_DIVERGENCE ${JSON.stringify(row)}`);
  }
  process.exit(1);
}

console.log(
  `FIELD_NATIVE_CROSS_RUNTIME_GATE state=passed required=${requiredClients.join(',')} ` +
  `comparable=${comparableRoutes} divergences=${divergences.length} ` +
  `runtime_sentinels=${sentinelRows} explicit_runtime_errors=${explicitRuntimeErrors} ` +
  `blocking=false owner=runtime_contract`
);
for (const row of divergences.slice(0, 40)) {
  console.log(`FIELD_NATIVE_CROSS_RUNTIME_OBSERVATION ${JSON.stringify(row)}`);
}
