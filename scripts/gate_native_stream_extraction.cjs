#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

const args = process.argv.slice(2);
let client = 'desktop';
let fixture = '';
let expectedProviders = [];
const logs = [];
for (let i = 0; i < args.length; i += 1) {
  const arg = args[i];
  if (arg === '--client') client = String(args[++i] || '').trim();
  else if (arg === '--fixture') fixture = String(args[++i] || '').trim();
  else if (arg === '--providers') {
    expectedProviders = String(args[++i] || '').split(',').map((v) => v.trim()).filter(Boolean);
  } else logs.push(arg);
}
if (!fixture || !expectedProviders.length || !logs.length) {
  console.error('usage: node scripts/gate_native_stream_extraction.cjs --client <client> --fixture <fixture> --providers <id,id,...> <log> [log ...]');
  process.exit(64);
}

const SENTINEL = '__NIAKVIO_RUNTIME_ERROR__';
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
function key(value) { return String(value || '').trim().toLowerCase(); }

const expected = new Map(expectedProviders.map((id) => [key(id), id]));
const state = new Map(expectedProviders.map((id) => [key(id), {
  id,
  observed: false,
  maxCount: 0,
  runtimeError: false,
  nativeError: false,
}]));
let readable = 0;

for (const file of logs) {
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) continue;
  readable += 1;
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
  let currentProvider = '';
  for (const raw of lines) {
    if (raw.includes('FIELD_NATIVE_RESULT ')) {
      const f = fields(raw.slice(raw.indexOf('FIELD_NATIVE_RESULT ')));
      if (String(f.client || '') !== client || String(f.fixture || '') !== fixture) continue;
      const provider = decode(f.provider64);
      const providerKey = key(provider);
      if (!expected.has(providerKey)) continue;
      currentProvider = providerKey;
      const row = state.get(providerKey);
      row.observed = true;
      row.maxCount = Math.max(row.maxCount, Number(f.count || 0) || 0);
    } else if (raw.includes('FIELD_NATIVE_ERROR ')) {
      const f = fields(raw.slice(raw.indexOf('FIELD_NATIVE_ERROR ')));
      if (String(f.client || '') !== client || String(f.fixture || '') !== fixture) continue;
      const providerKey = key(decode(f.provider64));
      if (state.has(providerKey)) {
        state.get(providerKey).observed = true;
        state.get(providerKey).nativeError = true;
      }
    } else if (raw.includes('FIELD_NATIVE_ROW ')) {
      const f = fields(raw.slice(raw.indexOf('FIELD_NATIVE_ROW ')));
      if (String(f.client || '') !== client || String(f.fixture || '') !== fixture) continue;
      const providerKey = key(decode(f.provider64));
      if (!state.has(providerKey)) continue;
      const decoded = [f.title64, f.name64, f.type64, f.quality64, f.language64].map(decode);
      if (decoded.some((value) => value.includes(SENTINEL))) state.get(providerKey).runtimeError = true;
      currentProvider = providerKey;
    } else if (raw.includes(SENTINEL) && currentProvider && state.has(currentProvider)) {
      state.get(currentProvider).runtimeError = true;
    }
  }
}

if (!readable) {
  console.error('FIELD_NATIVE_EXTRACTION_GATE state=infra_error reason=no_readable_log');
  process.exit(2);
}

const rows = [...state.values()];
const missing = rows.filter((row) => !row.observed);
const runtimeErrors = rows.filter((row) => row.runtimeError);
const nativeErrors = rows.filter((row) => row.nativeError);
const positive = rows.filter((row) => row.maxCount > 0 && !row.runtimeError);
const systematicRuntimeFailure = runtimeErrors.length === rows.length;
const noVisibleStreams = positive.length === 0;
const failed = missing.length > 0 || systematicRuntimeFailure || noVisibleStreams;

console.log(
  `FIELD_NATIVE_EXTRACTION_GATE state=${failed ? 'failed' : 'passed'} client=${client} fixture=${fixture} ` +
  `expected=${rows.length} observed=${rows.length - missing.length} positive=${positive.length} ` +
  `runtime_errors=${runtimeErrors.length} native_errors=${nativeErrors.length}`
);
for (const row of rows) {
  console.log(`FIELD_NATIVE_EXTRACTION_PROVIDER ${JSON.stringify({
    provider: row.id,
    observed: row.observed,
    maxCount: row.maxCount,
    runtimeError: row.runtimeError,
    nativeError: row.nativeError,
  })}`);
}
if (missing.length) console.error(`FIELD_NATIVE_EXTRACTION_GATE_FAILURE reason=missing_provider_evidence providers=${missing.map((r) => r.id).join(',')}`);
if (systematicRuntimeFailure) console.error('FIELD_NATIVE_EXTRACTION_GATE_FAILURE reason=systematic_runtime_error');
if (noVisibleStreams) console.error('FIELD_NATIVE_EXTRACTION_GATE_FAILURE reason=no_visible_streams');
process.exit(failed ? 1 : 0);
