#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { readerFailureClass, readerSignature, isReaderFailure } = require('./native_player_diagnostics.cjs');

const args = process.argv.slice(2);
const dirIndex = args.indexOf('--dir');
const summaryIndex = args.indexOf('--summary');
if (dirIndex < 0 || !args[dirIndex + 1] || summaryIndex < 0 || !args[summaryIndex + 1]) {
  process.stderr.write('usage: node scripts/enrich_native_corpus_summary_with_player.cjs --dir <logs> --summary <summary.json>\n');
  process.exit(64);
}
const inputDir = path.resolve(args[dirIndex + 1]);
const summaryPath = path.resolve(args[summaryIndex + 1]);
const summary = fs.existsSync(summaryPath) ? JSON.parse(fs.readFileSync(summaryPath, 'utf8')) : {};

function listFiles(directory) {
  if (!fs.existsSync(directory)) return [];
  const out = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) out.push(...listFiles(full));
    else if (entry.isFile() && /(?:desktop|mobile|tv)-native-corpus-.*\.log$/i.test(entry.name)) out.push(full);
  }
  return out.sort();
}
function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}
function fields(line) {
  const out = {};
  const re = /([A-Za-z0-9_]+)=([^\s]+)/g;
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}
function groupBy(items, fn) {
  const out = new Map();
  for (const item of items) {
    const key = fn(item);
    if (!out.has(key)) out.set(key, []);
    out.get(key).push(item);
  }
  return out;
}

const players = [];
const routeTerminals = new Map();
for (const file of listFiles(inputDir)) {
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);

    // A provider execution is terminal whether extraction returned streams or
    // raised a structured runtime error. Provider failures are valid evidence;
    // treating only FIELD_NATIVE_RESULT as execution used to erase exactly the
    // failures the Brain is supposed to learn from.
    if (line.startsWith('FIELD_NATIVE_RESULT ') || line.startsWith('FIELD_NATIVE_ERROR ')) {
      const provider = decode(f.provider64) || String(f.provider || '');
      const client = f.client || 'unknown';
      const fixture = f.fixture || 'unknown';
      const requestType = String(f.request_type || 'unknown').toLowerCase();
      const routeMode = String(f.route_mode || 'declared').toLowerCase();
      const key = `${client}\u0000${fixture}\u0000${provider.toLowerCase()}\u0000${requestType}\u0000${routeMode}`;
      routeTerminals.set(key, {
        client, fixture, provider, requestType, routeMode,
        terminal: line.startsWith('FIELD_NATIVE_ERROR ') ? 'error' : 'result',
      });
      continue;
    }

    if (!line.startsWith('FIELD_NATIVE_PLAYER ')) continue;
    const row = {
      client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
      requestType: String(f.request_type || 'unknown').toLowerCase(),
      routeMode: String(f.route_mode || 'declared').toLowerCase(),
      index: Number(f.index || 0), state: f.state || 'unknown', engine: f.engine || 'unknown',
      httpStatus: Number(f.http_status || 0), failureStage: f.failure_stage || 'unknown',
      durationSeconds: Number(f.duration_seconds || 0) || null, host: decode(f.host64),
      errorClass: decode(f.error_class64), errorCode: decode(f.error_code64),
      exceptionChain: decode(f.exception_chain64), responseHeaderNames: decode(f.response_header_names64),
    };
    row.failureClass = readerFailureClass(row);
    row.signature = readerSignature(row);
    players.push(row);
  }
}

const failures = players.filter(isReaderFailure);
const healthy = players.filter((row) => !isReaderFailure(row));
const byClass = [...groupBy(failures, (row) => row.failureClass).entries()]
  .map(([failureClass, values]) => ({
    failureClass, occurrences: values.length,
    providers: [...new Set(values.map((row) => row.provider))].sort(),
    clients: [...new Set(values.map((row) => row.client))].sort(),
    contexts: values.slice(0, 24),
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.failureClass.localeCompare(b.failureClass));
const byProvider = [...groupBy(failures, (row) => String(row.provider || '').toLowerCase()).entries()]
  .filter(([provider]) => provider)
  .map(([provider, values]) => ({
    provider, occurrences: values.length,
    failureClasses: Object.fromEntries([...groupBy(values, (row) => row.failureClass).entries()].map(([key, rows]) => [key, rows.length])),
    clients: [...new Set(values.map((row) => row.client))].sort(),
    fixtures: [...new Set(values.map((row) => row.fixture))].sort(),
    contexts: values.slice(0, 24),
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.provider.localeCompare(b.provider));
const repeated = [...groupBy(failures, (row) => `${String(row.provider || '').toLowerCase()}\u0000${row.failureClass}`).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([, values]) => ({
    provider: String(values[0].provider || '').toLowerCase(), failureClass: values[0].failureClass,
    occurrences: values.length, signatures: [...new Set(values.map((row) => row.signature))].slice(0, 12),
    clients: [...new Set(values.map((row) => row.client))].sort(),
    fixtures: [...new Set(values.map((row) => row.fixture))].sort(),
    contexts: values.slice(0, 16),
  }))
  .sort((a, b) => b.occurrences - a.occurrences);

const terminalRows = [...routeTerminals.values()];
const executedProviders = [...new Set(terminalRows.map((row) => String(row.provider || '').toLowerCase()).filter(Boolean))].sort();
const observedClients = [...new Set([
  ...terminalRows.map((row) => row.client),
  ...players.map((row) => row.client),
].filter(Boolean))].sort();

summary.schemaVersion = Math.max(4, Number(summary.schemaVersion || 0));
summary.clients = observedClients.length ? observedClients : (Array.isArray(summary.clients) ? summary.clients : []);
summary.providersObserved = executedProviders.length;
summary.executions = routeTerminals.size;
summary.mediaVerified = players.length;
summary.nativeEvidenceComplete = summary.providersObserved > 0 && summary.executions > 0 && summary.mediaVerified > 0;
summary.nativeReaderObserved = players.length;
summary.nativeReaderHealthy = healthy.length;
summary.nativeReaderFailures = failures.length;
summary.readerFailureClasses = Object.fromEntries(byClass.map((row) => [row.failureClass, row.occurrences]));
summary.readerFailureSignals = byClass;
summary.providerReaderFailures = byProvider;
summary.engineSignals = summary.engineSignals || {};
summary.engineSignals.repeatedReaderFailures = repeated;
summary.readerPrivacy = 'Sanitized only: no raw URLs, query tokens, cookie values, authorization values or response-header values.';

fs.mkdirSync(path.dirname(summaryPath), { recursive: true });
fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2) + '\n');
console.log(
  `FIELD_NATIVE_PLAYER_SUMMARY providers_observed=${summary.providersObserved} executions=${summary.executions} ` +
  `media_verified=${summary.mediaVerified} complete=${summary.nativeEvidenceComplete} observed=${players.length} ` +
  `healthy=${healthy.length} failures=${failures.length} classes=${byClass.length} repeated=${repeated.length}`
);
