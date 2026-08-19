#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

const argv = process.argv.slice(2);
let streamScope = 'all';
const scopeIndex = argv.indexOf('--streams');
if (scopeIndex >= 0) {
  streamScope = String(argv[scopeIndex + 1] || '').trim().toLowerCase();
  argv.splice(scopeIndex, 2);
}
const logs = argv;
if (!logs.length || !(streamScope === 'all' || /^[1-4]$/.test(streamScope))) {
  console.error('usage: node scripts/gate_native_reader_coverage.cjs [--streams all|1|2|3|4] <log> [log ...]');
  process.exit(64);
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
function key(client, fixture, provider) { return `${client}\u0000${fixture}\u0000${provider.toLowerCase()}`; }
function expectedStreams(returned) {
  return streamScope === 'all' ? returned : Math.min(returned, Number(streamScope));
}

const expectedProviders = new Map();
const results = new Map();
const players = new Map();
let readable = 0;

for (const file of logs) {
  if (!fs.existsSync(file)) continue;
  readable += 1;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const beginAt = raw.indexOf('FIELD_NATIVE_CORPUS_BEGIN ');
    if (beginAt >= 0) {
      const f = fields(raw.slice(beginAt));
      expectedProviders.set(`${f.client || 'unknown'}\u0000${f.fixture || 'unknown'}`, Number(f.providers || 0));
      continue;
    }
    const resultAt = raw.indexOf('FIELD_NATIVE_RESULT ');
    if (resultAt >= 0) {
      const f = fields(raw.slice(resultAt));
      const provider = decode(f.provider64);
      results.set(key(f.client || 'unknown', f.fixture || 'unknown', provider), {
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        returned: Math.max(0, Number(f.count || 0) || 0),
      });
      continue;
    }
    const playerAt = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (playerAt >= 0) {
      const f = fields(raw.slice(playerAt));
      const provider = decode(f.provider64);
      const k = key(f.client || 'unknown', f.fixture || 'unknown', provider);
      if (!players.has(k)) players.set(k, new Set());
      players.get(k).add(Math.max(0, Number(f.index || 0) || 0));
    }
  }
}

if (!readable) {
  console.error('FIELD_NATIVE_READER_COVERAGE state=infra_error reason=no_readable_log');
  process.exit(2);
}
if (!results.size) {
  console.error('FIELD_NATIVE_READER_COVERAGE state=infra_error reason=no_provider_results');
  process.exit(2);
}

const failures = [];
for (const [scope, expected] of expectedProviders) {
  const [client, fixture] = scope.split('\u0000');
  const observed = [...results.values()].filter((row) => row.client === client && row.fixture === fixture).length;
  if (expected !== observed) failures.push({ client, fixture, reason: 'provider_coverage', expected, observed });
}
for (const [k, result] of results) {
  const observed = players.get(k)?.size || 0;
  const expected = expectedStreams(result.returned);
  if (observed !== expected) {
    failures.push({
      client: result.client, fixture: result.fixture, provider: result.provider,
      reason: 'stream_coverage', scope: streamScope, returned: result.returned, expectedPlayed: expected, played: observed,
    });
  }
}

const returned = [...results.values()].reduce((sum, row) => sum + row.returned, 0);
const expectedPlayed = [...results.values()].reduce((sum, row) => sum + expectedStreams(row.returned), 0);
const played = [...players.values()].reduce((sum, set) => sum + set.size, 0);
console.log(`FIELD_NATIVE_READER_COVERAGE state=${failures.length ? 'failed' : 'passed'} scope=${streamScope} providers=${results.size} returned=${returned} expected_played=${expectedPlayed} played=${played} failures=${failures.length}`);
for (const failure of failures.slice(0, 120)) console.log(`FIELD_NATIVE_READER_COVERAGE_FAILURE ${JSON.stringify(failure)}`);
process.exit(failures.length ? 1 : 0);
