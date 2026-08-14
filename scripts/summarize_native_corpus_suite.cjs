#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { streamIdentity } = require('./nuvio_client_lab.cjs');

const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const dirIndex = args.indexOf('--dir');
const outputIndex = args.indexOf('--output');
const inputDir = path.resolve(dirIndex >= 0 ? args[dirIndex + 1] : process.cwd());
const outputPath = path.resolve(outputIndex >= 0 ? args[outputIndex + 1] : path.join(inputDir, 'native-corpus-summary.json'));

const corpus = JSON.parse(fs.readFileSync(path.join(root, '.github/triggers/nuvio-client-lab.json'), 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const fixtureMap = new Map((corpus.fixtures || []).map((row) => [row.slug, row.fixture || {}]));
const minRatio = Number(corpus.policy?.minimum_duration_ratio || 0.55);
const maxRatio = Number(corpus.policy?.maximum_duration_ratio || 1.8);
const manifestMap = new Map(
  (manifest.scrapers || [])
    .filter((row) => row && typeof row === 'object')
    .map((row) => [String(row.id || '').toLowerCase(), row]),
);

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

function syntheticUrl(host, hint) {
  if (!host || !hint) return '';
  return `https://${host}/${encodeURIComponent(hint)}`;
}

function relevant(provider, fixture) {
  const row = manifestMap.get(String(provider || '').toLowerCase());
  const published = Array.isArray(row?.published_types) ? row.published_types.map((v) => String(v).toLowerCase()) : [];
  if (!published.length) return true;
  const category = String(fixture?.category || fixture?.mediaType || '').toLowerCase();
  if (category === 'anime') return published.includes('anime') || published.includes('tv');
  return published.includes(category);
}

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

const executions = new Map();
const rows = [];
const transports = new Map();
const errors = [];

for (const file of listFiles(inputDir)) {
  const content = fs.readFileSync(file, 'utf8');
  for (const raw of content.split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    if (line.startsWith('FIELD_NATIVE_RESULT ')) {
      const provider = decode(f.provider64);
      const key = `${f.client}\u0000${f.fixture}\u0000${provider}`;
      executions.set(key, {
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        enabled: f.enabled === 'true', durationMs: Number(f.duration_ms || 0), count: Number(f.count || 0),
      });
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      const provider = decode(f.provider64);
      const host = decode(f.host64);
      const mediaHint = decode(f.media_hint64);
      rows.push({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        index: Number(f.index || 0), host, mediaHint,
        stream: {
          title: decode(f.title64), name: decode(f.name64), quality: decode(f.quality64),
          language: decode(f.language64), type: decode(f.type64), url: syntheticUrl(host, mediaHint),
        },
      });
    } else if (line.startsWith('FIELD_NATIVE_TRANSPORT ')) {
      const provider = decode(f.provider64);
      const key = `${f.client}\u0000${f.fixture}\u0000${provider}`;
      transports.set(key, {
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        state: f.state || 'unknown', kind: f.kind || 'unknown', status: Number(f.status || 0),
        contentType: decode(f.content_type64), extm3u: f.extm3u === 'true',
        durationSeconds: Number(f.duration_seconds || 0) || null,
        host: decode(f.host64), mediaHint: decode(f.media_hint64),
      });
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      errors.push({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
        durationMs: Number(f.duration_ms || 0), error: decode(f.error64),
      });
    }
  }
}

const contradictions = [];
for (const row of rows) {
  const fixture = fixtureMap.get(row.fixture) || {};
  let identity = streamIdentity(row.stream, fixture);
  const transport = transports.get(`${row.client}\u0000${row.fixture}\u0000${row.provider}`);
  const expected = Number(fixture.expectedDurationMinutes || 0) * 60 || null;
  const ratio = expected && transport?.durationSeconds ? transport.durationSeconds / expected : null;
  if (row.index === 0 && ratio != null && (ratio < minRatio || ratio > maxRatio)) {
    identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };
  }
  if (identity.status === 'contradiction') {
    contradictions.push({
      client: row.client, fixture: row.fixture, provider: row.provider,
      reason: identity.reason, title: row.stream.title, name: row.stream.name,
      host: row.host || null, mediaHint: row.mediaHint || null, durationRatio: ratio,
    });
  }
}

const transportFailures = [...transports.values()].filter((row) => row.state === 'dead' || row.state === 'error');
const slowExecutions = [...executions.values()].filter((row) => row.durationMs >= 30000);

function groupBy(items, fn) {
  const map = new Map();
  for (const item of items) {
    const key = fn(item);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
  }
  return map;
}

const repeatedContradictions = [...groupBy(contradictions, (row) => row.provider.toLowerCase()).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([provider, values]) => ({ provider, occurrences: values.length, contexts: values.slice(0, 12) }))
  .sort((a, b) => b.occurrences - a.occurrences);

const repeatedTransportFailures = [...groupBy(transportFailures, (row) => row.provider.toLowerCase()).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([provider, values]) => ({ provider, occurrences: values.length, contexts: values.slice(0, 12) }))
  .sort((a, b) => b.occurrences - a.occurrences);

const repeatedSlow = [...groupBy(slowExecutions, (row) => row.provider.toLowerCase()).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([provider, values]) => ({
    provider, occurrences: values.length,
    maxDurationMs: Math.max(...values.map((row) => row.durationMs)),
    contexts: values.slice(0, 12),
  }))
  .sort((a, b) => b.occurrences - a.occurrences || b.maxDurationMs - a.maxDurationMs);

const platformGaps = [];
const byFixtureProvider = groupBy([...executions.values()], (row) => `${row.fixture}\u0000${row.provider.toLowerCase()}`);
for (const values of byFixtureProvider.values()) {
  const byClient = new Map(values.map((row) => [row.client, row]));
  const desktop = byClient.get('desktop');
  const mobile = byClient.get('mobile');
  const tv = byClient.get('tv');
  if (!desktop || desktop.count <= 0) continue;
  if (mobile && mobile.count === 0) platformGaps.push({ provider: desktop.provider, fixture: desktop.fixture, from: 'desktop', to: 'mobile' });
  if (tv && tv.count === 0) platformGaps.push({ provider: desktop.provider, fixture: desktop.fixture, from: 'desktop', to: 'tv' });
}
const repeatedPlatformGaps = [...groupBy(platformGaps, (row) => `${row.provider.toLowerCase()}\u0000${row.to}`).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([, values]) => ({ provider: values[0].provider, targetClient: values[0].to, occurrences: values.length, fixtures: values.map((v) => v.fixture) }))
  .sort((a, b) => b.occurrences - a.occurrences);

const systemicEmpty = [];
const byProvider = groupBy([...executions.values()], (row) => row.provider.toLowerCase());
for (const [providerKey, values] of byProvider.entries()) {
  const relevantValues = values.filter((row) => row.enabled && relevant(row.provider, fixtureMap.get(row.fixture) || {}));
  if (relevantValues.length >= 3 && relevantValues.every((row) => row.count === 0)) {
    systemicEmpty.push({
      provider: relevantValues[0].provider,
      executions: relevantValues.length,
      clients: [...new Set(relevantValues.map((row) => row.client))].sort(),
      fixtures: [...new Set(relevantValues.map((row) => row.fixture))].sort(),
    });
  }
}
systemicEmpty.sort((a, b) => b.executions - a.executions);

const providerRuntimeErrors = [...groupBy(errors, (row) => row.provider.toLowerCase()).entries()]
  .map(([provider, values]) => ({ provider, occurrences: values.length, contexts: values.slice(0, 12) }))
  .sort((a, b) => b.occurrences - a.occurrences);

const summary = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  fixtures: [...fixtureMap.keys()],
  clients: [...new Set([...executions.values()].map((row) => row.client))].sort(),
  providersObserved: [...new Set([...executions.values()].map((row) => row.provider))].length,
  executions: executions.size,
  nonEmptyExecutions: [...executions.values()].filter((row) => row.count > 0).length,
  runtimeErrors: errors.length,
  contradictions: contradictions.length,
  transportFailures: transportFailures.length,
  slowExecutions: slowExecutions.length,
  engineSignals: {
    repeatedContradictions,
    repeatedTransportFailures,
    repeatedSlow,
    repeatedPlatformGaps,
    systemicEmpty,
    providerRuntimeErrors,
  },
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2) + '\n');
console.log(`FIELD_NATIVE_CORPUS_SUITE_SUMMARY ${JSON.stringify({
  providersObserved: summary.providersObserved,
  executions: summary.executions,
  contradictions: summary.contradictions,
  transportFailures: summary.transportFailures,
  runtimeErrors: summary.runtimeErrors,
  repeatedPlatformGaps: repeatedPlatformGaps.length,
  systemicEmpty: systemicEmpty.length,
})}`);
for (const [name, values] of Object.entries(summary.engineSignals)) {
  for (const row of values.slice(0, 30)) console.log(`FIELD_NATIVE_ENGINE_SIGNAL type=${name} data=${JSON.stringify(row)}`);
}
