#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { streamIdentity } = require('./nuvio_client_lab.cjs');

function usage() {
  process.stderr.write('usage: node scripts/analyze_native_corpus_results.cjs <fixture-slug> <log> [log ...]\n');
  process.exit(64);
}

const [, , fixtureSlug, ...logPaths] = process.argv;
if (!fixtureSlug || !logPaths.length) usage();

const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, '.github/triggers/nuvio-client-lab.json'), 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
const overrides = JSON.parse(fs.readFileSync(path.join(root, 'provider-overrides.json'), 'utf8'));
const fixtureRow = (config.fixtures || []).find((row) => row && row.slug === fixtureSlug);
if (!fixtureRow || !fixtureRow.fixture) throw new Error(`unknown corpus fixture: ${fixtureSlug}`);
const fixture = fixtureRow.fixture;
const minimumDurationRatio = Number(config.policy?.minimum_duration_ratio || 0.55);
const maximumDurationRatio = Number(config.policy?.maximum_duration_ratio || 1.8);
const expectedDurationSeconds = Number(fixture.expectedDurationMinutes || 0) * 60 || null;
const manifestMap = new Map(
  (manifest.scrapers || [])
    .filter((row) => row && typeof row === 'object')
    .map((row) => [String(row.id || '').toLowerCase(), row]),
);
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
  let match;
  while ((match = re.exec(line)) !== null) out[match[1]] = match[2];
  return out;
}

function safeSyntheticUrl(host, mediaHint) {
  if (!host || !mediaHint) return '';
  return `https://${host}/${encodeURIComponent(mediaHint)}`;
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

function withPolicy(row) {
  const policy = providerPolicy(row.provider);
  return { ...row, capability: policy.strategy, allowEmbed: policy.allowEmbed };
}

function key(client, provider, index = 0) {
  return `${client}\u0000${provider}\u0000${Number(index || 0)}`;
}
function providerKey(client, provider) {
  return `${client}\u0000${provider}`;
}

const results = new Map();
const rows = [];
const transports = new Map();
const playbacks = [];
const playbackProviders = new Map();
const runtimeErrors = [];
for (const input of logPaths) {
  if (!fs.existsSync(input)) continue;
  const text = fs.readFileSync(input, 'utf8');
  for (const raw of text.split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    if (line.startsWith('FIELD_NATIVE_RESULT ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      results.set(providerKey(client, provider), withPolicy({
        client,
        provider,
        enabled: f.enabled === 'true',
        durationMs: Number(f.duration_ms || 0),
        count: Number(f.count || 0),
      }));
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      const host = decode(f.host64);
      const mediaHint = decode(f.media_hint64);
      rows.push(withPolicy({
        client: f.client || 'unknown',
        provider: decode(f.provider64),
        index: Number(f.index || 0),
        host,
        mediaHint,
        stream: {
          title: decode(f.title64),
          name: decode(f.name64),
          quality: decode(f.quality64),
          language: decode(f.language64),
          type: decode(f.type64),
          url: safeSyntheticUrl(host, mediaHint),
        },
      }));
    } else if (line.startsWith('FIELD_NATIVE_TRANSPORT ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      const index = Number(f.index || 0);
      transports.set(key(client, provider, index), withPolicy({
        client,
        provider,
        index,
        state: f.state || 'unknown',
        kind: f.kind || 'unknown',
        status: Number(f.status || 0),
        contentType: decode(f.content_type64),
        extm3u: f.extm3u === 'true',
        durationSeconds: Number(f.duration_seconds || 0) || null,
        host: decode(f.host64),
        mediaHint: decode(f.media_hint64),
      }));
    } else if (line.startsWith('FIELD_NATIVE_PLAYBACK ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      playbacks.push(withPolicy({
        client,
        provider,
        index: Number(f.index || 0),
        state: f.state || 'error',
        engine: f.engine || 'none',
        repairClass: f.repair_class || 'player_runtime_gap',
        sourceStatus: Number(f.source_status || 0),
        sourceSignature: f.signature || 'unknown',
        acceptsRanges: f.ranges === 'true',
        contentType: decode(f.content_type64),
        finalHost: decode(f.final_host64),
        exoState: f.exo_state || 'unknown',
        exoCode: Number(f.exo_code || 0),
        exoName: f.exo_name || '',
        exoCause: decode(f.exo_cause64),
        retryMime: decode(f.retry_mime64),
        mpvState: f.mpv_state || 'not_needed',
        mpvName: f.mpv_name || '',
        mpvCause: decode(f.mpv_cause64),
      }));
    } else if (line.startsWith('FIELD_NATIVE_PLAYBACK_PROVIDER ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      playbackProviders.set(providerKey(client, provider), withPolicy({
        client,
        provider,
        state: f.state || 'unplayable',
      }));
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      runtimeErrors.push(withPolicy({
        client: f.client || 'unknown',
        provider: decode(f.provider64),
        durationMs: Number(f.duration_ms || 0),
        error: decode(f.error64),
      }));
    }
  }
}

const contradictions = [];
const matches = [];
const unknown = [];
for (const row of rows) {
  let identity = streamIdentity(row.stream, fixture);
  const transport = transports.get(key(row.client, row.provider, row.index));
  const durationRatio = expectedDurationSeconds && transport?.durationSeconds
    ? transport.durationSeconds / expectedDurationSeconds
    : null;
  if (row.index === 0 && durationRatio != null && (durationRatio < minimumDurationRatio || durationRatio > maximumDurationRatio)) {
    identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };
  } else if (row.index === 0 && identity.status === 'unknown' && durationRatio != null) {
    identity = { status: 'match', reason: 'fixture_duration_match' };
  }
  const record = {
    client: row.client,
    provider: row.provider,
    capability: row.capability,
    index: row.index,
    status: identity.status,
    reason: identity.reason,
    title: row.stream.title,
    name: row.stream.name,
    host: row.host || null,
    mediaHint: row.mediaHint || null,
    durationRatio,
  };
  if (identity.status === 'contradiction') contradictions.push(record);
  else if (identity.status === 'match') matches.push(record);
  else unknown.push(record);
}

const expectedEmbeds = [...transports.values()]
  .filter((row) => row.state === 'dead' && row.kind === 'html' && row.allowEmbed)
  .map((row) => ({
    client: row.client,
    provider: row.provider,
    index: row.index,
    capability: row.capability,
    state: 'embed',
    kind: row.kind,
    status: row.status,
    contentType: row.contentType,
    host: row.host || null,
    mediaHint: row.mediaHint || null,
  }));
const transportFailures = [...transports.values()]
  .filter((row) => (row.state === 'dead' || row.state === 'error') && !(row.state === 'dead' && row.kind === 'html' && row.allowEmbed))
  .map((row) => ({
    client: row.client,
    provider: row.provider,
    index: row.index,
    capability: row.capability,
    state: row.state,
    kind: row.kind,
    status: row.status,
    contentType: row.contentType,
    host: row.host || null,
    mediaHint: row.mediaHint || null,
  }));
const transportUnknown = [...transports.values()].filter((row) => row.state === 'unknown');
const transportOk = [...transports.values()].filter((row) => row.state === 'ok');
const playbackReady = playbacks.filter((row) => row.state === 'ready');
const playbackFailures = playbacks.filter((row) => row.state !== 'ready');
const exoContainerUnsupported = playbackFailures.filter((row) => row.exoName === 'ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED');
const mpvOnly = playbackReady.filter((row) => row.engine === 'mpv');
const playerRepairClasses = {};
for (const row of playbackFailures) playerRepairClasses[row.repairClass] = (playerRepairClasses[row.repairClass] || 0) + 1;
const slow = [...results.values()].filter((row) => row.durationMs >= 30000).sort((a, b) => b.durationMs - a.durationMs);
const nonEmpty = [...results.values()].filter((row) => row.count > 0);
const empty = [...results.values()].filter((row) => row.count === 0);
const clients = [...new Set([...results.values()].map((row) => row.client))].sort();
const providers = [...new Set([...results.values()].map((row) => row.provider))].sort();
const clientsWithPlayback = [...new Set(playbacks.map((row) => row.client))].sort();
const playbackReadyProviders = [...playbackProviders.values()].filter((row) => row.state === 'ready');
const playbackUnplayableProviders = [...playbackProviders.values()].filter((row) => row.state === 'unplayable');

const summary = {
  fixture: fixtureSlug,
  title: fixture.title,
  tmdbId: fixture.tmdbId,
  clients,
  clientsWithPlayback,
  providerCount: providers.length,
  executions: results.size,
  nonEmpty: nonEmpty.length,
  empty: empty.length,
  runtimeErrors: runtimeErrors.length,
  identityMatches: matches.length,
  identityUnknown: unknown.length,
  identityContradictions: contradictions.length,
  transportOk: transportOk.length,
  transportExpectedEmbeds: expectedEmbeds.length,
  transportUnknown: transportUnknown.length,
  transportFailures: transportFailures.length,
  playbackAttempts: playbacks.length,
  playbackReady: playbackReady.length,
  playbackFailures: playbackFailures.length,
  playbackReadyProviders: playbackReadyProviders.length,
  playbackUnplayableProviders: playbackUnplayableProviders.length,
  exoContainerUnsupported: exoContainerUnsupported.length,
  mpvOnly: mpvOnly.length,
  playerRepairClasses,
  durationEvidence: [...transports.values()].filter((row) => row.durationSeconds != null).length,
  slowProviders: slow.length,
};

console.log(`FIELD_NATIVE_CORPUS_ANALYSIS ${JSON.stringify(summary)}`);
for (const row of contradictions.slice(0, 80)) console.log(`FIELD_NATIVE_CONTRADICTION ${JSON.stringify(row)}`);
for (const row of expectedEmbeds.slice(0, 80)) console.log(`FIELD_NATIVE_EXPECTED_EMBED ${JSON.stringify(row)}`);
for (const row of transportFailures.slice(0, 80)) console.log(`FIELD_NATIVE_TRANSPORT_FAILURE ${JSON.stringify(row)}`);
for (const row of playbackFailures.slice(0, 160)) console.log(`FIELD_NATIVE_PLAYBACK_FAILURE ${JSON.stringify(row)}`);
for (const row of mpvOnly.slice(0, 80)) console.log(`FIELD_NATIVE_PLAYER_ENGINE_COMPAT ${JSON.stringify(row)}`);
for (const row of runtimeErrors.slice(0, 80)) console.log(`FIELD_NATIVE_RUNTIME_ERROR ${JSON.stringify(row)}`);
for (const row of slow.slice(0, 80)) console.log(`FIELD_NATIVE_SLOW ${JSON.stringify(row)}`);

if (runtimeErrors.length || contradictions.length || transportFailures.length || playbackFailures.length) process.exitCode = 1;
