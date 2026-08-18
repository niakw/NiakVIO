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
const overridesPath = path.join(root, 'provider-overrides.json');
const overrides = fs.existsSync(overridesPath) ? JSON.parse(fs.readFileSync(overridesPath, 'utf8')) : {};
const fixtureMap = new Map((corpus.fixtures || []).map((row) => [row.slug, row.fixture || {}]));
const minRatio = Number(corpus.policy?.minimum_duration_ratio || 0.55);
const maxRatio = Number(corpus.policy?.maximum_duration_ratio || 1.8);
const manifestMap = new Map(
  (manifest.scrapers || [])
    .filter((row) => row && typeof row === 'object')
    .map((row) => [String(row.id || '').toLowerCase(), row]),
);
const configuredCapabilities = overrides.provider_capabilities || {};
const providerPatches = overrides.provider_patches || {};

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
function providerPolicy(provider) {
  const id = String(provider || '').toLowerCase();
  const manifestRow = manifestMap.get(id) || {};
  const patch = providerPatches[id] || {};
  const configured = configuredCapabilities[id] || {};
  const strategy = String(
    patch.capability ||
    (typeof configured === 'object' ? configured.strategy : configured) ||
    manifestRow.capability ||
    'unknown'
  );
  const allowEmbed = strategy === 'iframe_player' || (
    strategy === 'mixed_embed_resolver' && (
      manifestRow.supportsExternalPlayer === true || patch.preserve_embed_urls === true
    )
  );
  return { strategy, allowEmbed };
}
function withCapability(row) {
  const policy = providerPolicy(row.provider);
  return { ...row, capability: policy.strategy, allowEmbed: policy.allowEmbed };
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
function executionKey(client, fixture, provider) {
  return `${client}\u0000${fixture}\u0000${provider}`;
}
function attemptKey(client, fixture, provider, index = 0) {
  return `${executionKey(client, fixture, provider)}\u0000${Number(index || 0)}`;
}

const executions = new Map();
const rows = [];
const transports = new Map();
const playbacks = [];
const playbackProviders = new Map();
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
      const key = executionKey(f.client, f.fixture, provider);
      executions.set(key, withCapability({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        enabled: f.enabled === 'true', durationMs: Number(f.duration_ms || 0), count: Number(f.count || 0),
      }));
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      const provider = decode(f.provider64);
      const host = decode(f.host64);
      const mediaHint = decode(f.media_hint64);
      rows.push(withCapability({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        index: Number(f.index || 0), host, mediaHint,
        stream: {
          title: decode(f.title64), name: decode(f.name64), quality: decode(f.quality64),
          language: decode(f.language64), type: decode(f.type64), url: syntheticUrl(host, mediaHint),
        },
      }));
    } else if (line.startsWith('FIELD_NATIVE_TRANSPORT ')) {
      const provider = decode(f.provider64);
      const index = Number(f.index || 0);
      const key = attemptKey(f.client, f.fixture, provider, index);
      transports.set(key, withCapability({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider, index,
        state: f.state || 'unknown', kind: f.kind || 'unknown', status: Number(f.status || 0),
        contentType: decode(f.content_type64), extm3u: f.extm3u === 'true',
        durationSeconds: Number(f.duration_seconds || 0) || null,
        host: decode(f.host64), mediaHint: decode(f.media_hint64),
      }));
    } else if (line.startsWith('FIELD_NATIVE_PLAYBACK ')) {
      const provider = decode(f.provider64);
      playbacks.push(withCapability({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider,
        index: Number(f.index || 0), state: f.state || 'error', engine: f.engine || 'none',
        repairClass: f.repair_class || 'player_runtime_gap',
        sourceStatus: Number(f.source_status || 0), sourceSignature: f.signature || 'unknown',
        acceptsRanges: f.ranges === 'true', contentType: decode(f.content_type64), finalHost: decode(f.final_host64),
        exoState: f.exo_state || 'unknown', exoCode: Number(f.exo_code || 0), exoName: f.exo_name || '',
        exoCause: decode(f.exo_cause64), retryMime: decode(f.retry_mime64),
        mpvState: f.mpv_state || 'not_needed', mpvName: f.mpv_name || '', mpvCause: decode(f.mpv_cause64),
      }));
    } else if (line.startsWith('FIELD_NATIVE_PLAYBACK_PROVIDER ')) {
      const provider = decode(f.provider64);
      playbackProviders.set(executionKey(f.client, f.fixture, provider), withCapability({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider, state: f.state || 'unplayable',
      }));
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      errors.push(withCapability({
        client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
        durationMs: Number(f.duration_ms || 0), error: decode(f.error64),
      }));
    }
  }
}

const contradictions = [];
for (const row of rows) {
  const fixture = fixtureMap.get(row.fixture) || {};
  let identity = streamIdentity(row.stream, fixture);
  const transport = transports.get(attemptKey(row.client, row.fixture, row.provider, row.index));
  const expected = Number(fixture.expectedDurationMinutes || 0) * 60 || null;
  const ratio = expected && transport?.durationSeconds ? transport.durationSeconds / expected : null;
  if (row.index === 0 && ratio != null && (ratio < minRatio || ratio > maxRatio)) {
    identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };
  }
  if (identity.status === 'contradiction') {
    contradictions.push({
      client: row.client, fixture: row.fixture, provider: row.provider, capability: row.capability,
      reason: identity.reason, title: row.stream.title, name: row.stream.name,
      host: row.host || null, mediaHint: row.mediaHint || null, durationRatio: ratio,
    });
  }
}

const expectedEmbeds = [...transports.values()]
  .filter((row) => row.state === 'dead' && row.kind === 'html' && row.allowEmbed);
const transportFailures = [...transports.values()]
  .filter((row) => (row.state === 'dead' || row.state === 'error') && !(row.state === 'dead' && row.kind === 'html' && row.allowEmbed));
const playbackReady = playbacks.filter((row) => row.state === 'ready');
const playbackFailures = playbacks.filter((row) => row.state !== 'ready');
const mpvOnly = playbackReady.filter((row) => row.engine === 'mpv');
const exoContainerUnsupported = playbackFailures.filter((row) => row.exoName === 'ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED');
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
function groupedCapabilitySignals(items, keyFn, minOccurrences = 2) {
  return [...groupBy(items, keyFn).entries()]
    .filter(([, values]) => values.length >= minOccurrences)
    .map(([key, values]) => ({
      capability: values[0].capability || String(key).split('\u0000')[0] || 'unknown',
      occurrences: values.length,
      providers: [...new Set(values.map((row) => row.provider))].sort(),
      clients: [...new Set(values.map((row) => row.client).filter(Boolean))].sort(),
      fixtures: [...new Set(values.map((row) => row.fixture).filter(Boolean))].sort(),
      contexts: values.slice(0, 16),
    }))
    .sort((a, b) => b.occurrences - a.occurrences || b.providers.length - a.providers.length);
}

const repeatedContradictions = [...groupBy(contradictions, (row) => row.provider.toLowerCase()).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([provider, values]) => ({ provider, capability: values[0].capability, occurrences: values.length, contexts: values.slice(0, 12) }))
  .sort((a, b) => b.occurrences - a.occurrences);
const repeatedTransportFailures = [...groupBy(transportFailures, (row) => row.provider.toLowerCase()).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([provider, values]) => ({ provider, capability: values[0].capability, occurrences: values.length, contexts: values.slice(0, 12) }))
  .sort((a, b) => b.occurrences - a.occurrences);
const repeatedPlaybackFailures = [...groupBy(playbackFailures, (row) => `${row.provider.toLowerCase()}\u0000${row.repairClass}`).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([, values]) => ({
    provider: values[0].provider,
    capability: values[0].capability,
    repairClass: values[0].repairClass,
    occurrences: values.length,
    clients: [...new Set(values.map((row) => row.client))].sort(),
    fixtures: [...new Set(values.map((row) => row.fixture))].sort(),
    exoCodeNames: [...new Set(values.map((row) => row.exoName).filter(Boolean))].sort(),
    mpvRecovered: values.some((row) => row.mpvState === 'ready'),
    contexts: values.slice(0, 12),
  }))
  .sort((a, b) => b.occurrences - a.occurrences);
const repeatedSlow = [...groupBy(slowExecutions, (row) => row.provider.toLowerCase()).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([provider, values]) => ({
    provider, capability: values[0].capability, occurrences: values.length,
    maxDurationMs: Math.max(...values.map((row) => row.durationMs)), contexts: values.slice(0, 12),
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
  if (mobile && mobile.count === 0) platformGaps.push({ provider: desktop.provider, capability: desktop.capability, fixture: desktop.fixture, from: 'desktop', to: 'mobile', client: 'mobile' });
  if (tv && tv.count === 0) platformGaps.push({ provider: desktop.provider, capability: desktop.capability, fixture: desktop.fixture, from: 'desktop', to: 'tv', client: 'tv' });
}
const repeatedPlatformGaps = [...groupBy(platformGaps, (row) => `${row.provider.toLowerCase()}\u0000${row.to}`).entries()]
  .filter(([, values]) => values.length >= 2)
  .map(([, values]) => ({ provider: values[0].provider, capability: values[0].capability, targetClient: values[0].to, occurrences: values.length, fixtures: values.map((v) => v.fixture) }))
  .sort((a, b) => b.occurrences - a.occurrences);

const systemicEmpty = [];
const byProvider = groupBy([...executions.values()], (row) => row.provider.toLowerCase());
for (const values of byProvider.values()) {
  const relevantValues = values.filter((row) => row.enabled && relevant(row.provider, fixtureMap.get(row.fixture) || {}));
  if (relevantValues.length >= 3 && relevantValues.every((row) => row.count === 0)) {
    systemicEmpty.push({
      provider: relevantValues[0].provider, capability: relevantValues[0].capability,
      executions: relevantValues.length,
      clients: [...new Set(relevantValues.map((row) => row.client))].sort(),
      fixtures: [...new Set(relevantValues.map((row) => row.fixture))].sort(),
    });
  }
}
systemicEmpty.sort((a, b) => b.executions - a.executions);

const providerRuntimeErrors = [...groupBy(errors, (row) => row.provider.toLowerCase()).entries()]
  .map(([provider, values]) => ({ provider, capability: values[0].capability, occurrences: values.length, contexts: values.slice(0, 12) }))
  .sort((a, b) => b.occurrences - a.occurrences);
const capabilityInventory = [...groupBy([...executions.values()], (row) => row.capability).entries()]
  .map(([capability, values]) => ({
    capability, providers: [...new Set(values.map((row) => row.provider))].sort(), executions: values.length,
    nonEmptyExecutions: values.filter((row) => row.count > 0).length,
  }))
  .sort((a, b) => b.executions - a.executions);

const playerProviderEvidence = [...groupBy(playbacks, (row) => row.provider.toLowerCase()).entries()]
  .map(([provider, values]) => {
    const failures = values.filter((row) => row.state !== 'ready');
    return {
      providerId: provider,
      attempts: values.length,
      readyAttempts: values.length - failures.length,
      failedAttempts: failures.length,
      clients: [...new Set(values.map((row) => row.client))].sort(),
      fixtures: [...new Set(values.map((row) => row.fixture))].sort(),
      failureClasses: [...new Set(failures.map((row) => row.repairClass).filter(Boolean))].sort(),
      exoCodes: [...new Set(failures.map((row) => row.exoCode).filter(Boolean))].sort((a, b) => a - b),
      exoCodeNames: [...new Set(failures.map((row) => row.exoName).filter(Boolean))].sort(),
      sourceSignatures: [...new Set(failures.map((row) => row.sourceSignature).filter(Boolean))].sort(),
      sourceStatuses: [...new Set(failures.map((row) => row.sourceStatus).filter(Boolean))].sort((a, b) => a - b),
      mpvRecovered: values.some((row) => row.state === 'ready' && row.engine === 'mpv'),
      playbackReady: values.some((row) => row.state === 'ready'),
    };
  })
  .sort((a, b) => b.failedAttempts - a.failedAttempts || a.providerId.localeCompare(b.providerId));

const capabilitySignals = {
  contradictions: groupedCapabilitySignals(contradictions, (row) => row.capability),
  transportFailures: groupedCapabilitySignals(transportFailures, (row) => row.capability),
  playbackFailures: groupedCapabilitySignals(playbackFailures, (row) => `${row.capability}\u0000${row.repairClass}`),
  slowExecutions: groupedCapabilitySignals(slowExecutions, (row) => row.capability),
  platformGaps: groupedCapabilitySignals(platformGaps, (row) => `${row.capability}\u0000${row.to}`),
  runtimeErrors: groupedCapabilitySignals(errors, (row) => row.capability),
  systemicEmpty: [...groupBy(systemicEmpty, (row) => row.capability).entries()]
    .filter(([, values]) => values.length >= 1)
    .map(([capability, values]) => ({
      capability, providers: values.map((row) => row.provider).sort(), providerCount: values.length,
      executions: values.reduce((sum, row) => sum + row.executions, 0), contexts: values.slice(0, 16),
    }))
    .sort((a, b) => b.providerCount - a.providerCount || b.executions - a.executions),
};

const summary = {
  schemaVersion: 3,
  generatedAt: new Date().toISOString(),
  fixtures: [...fixtureMap.keys()],
  clients: [...new Set([...executions.values()].map((row) => row.client))].sort(),
  clientsWithPlaybackEvidence: [...new Set(playbacks.map((row) => row.client))].sort(),
  providersObserved: [...new Set([...executions.values()].map((row) => row.provider))].length,
  executions: executions.size,
  nonEmptyExecutions: [...executions.values()].filter((row) => row.count > 0).length,
  runtimeErrors: errors.length,
  contradictions: contradictions.length,
  transportExpectedEmbeds: expectedEmbeds.length,
  transportFailures: transportFailures.length,
  playbackAttempts: playbacks.length,
  playbackReady: playbackReady.length,
  playbackFailures: playbackFailures.length,
  playbackReadyProviders: [...playbackProviders.values()].filter((row) => row.state === 'ready').length,
  playbackUnplayableProviders: [...playbackProviders.values()].filter((row) => row.state === 'unplayable').length,
  exoContainerUnsupported: exoContainerUnsupported.length,
  mpvOnly: mpvOnly.length,
  slowExecutions: slowExecutions.length,
  playerFeedback: {
    schemaVersion: 1,
    attempts: playbacks.length,
    ready: playbackReady.length,
    failures: playbackFailures.length,
    exoContainerUnsupported: exoContainerUnsupported.length,
    mpvOnly: mpvOnly.length,
    providers: playerProviderEvidence,
  },
  capabilityInventory,
  engineSignals: {
    repeatedContradictions,
    repeatedTransportFailures,
    repeatedPlaybackFailures,
    repeatedSlow,
    repeatedPlatformGaps,
    systemicEmpty,
    providerRuntimeErrors,
  },
  capabilitySignals,
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2) + '\n');
console.log(`FIELD_NATIVE_CORPUS_SUITE_SUMMARY ${JSON.stringify({
  providersObserved: summary.providersObserved,
  executions: summary.executions,
  contradictions: summary.contradictions,
  transportExpectedEmbeds: summary.transportExpectedEmbeds,
  transportFailures: summary.transportFailures,
  playbackAttempts: summary.playbackAttempts,
  playbackReady: summary.playbackReady,
  playbackFailures: summary.playbackFailures,
  exoContainerUnsupported: summary.exoContainerUnsupported,
  mpvOnly: summary.mpvOnly,
  runtimeErrors: summary.runtimeErrors,
  repeatedPlatformGaps: repeatedPlatformGaps.length,
  systemicEmpty: systemicEmpty.length,
  capabilitiesObserved: capabilityInventory.length,
})}`);
for (const [name, values] of Object.entries(summary.engineSignals)) {
  for (const row of values.slice(0, 30)) console.log(`FIELD_NATIVE_ENGINE_SIGNAL type=${name} data=${JSON.stringify(row)}`);
}
for (const [name, values] of Object.entries(summary.capabilitySignals)) {
  for (const row of values.slice(0, 30)) console.log(`FIELD_NATIVE_CAPABILITY_SIGNAL type=${name} data=${JSON.stringify(row)}`);
}
