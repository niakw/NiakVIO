#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { streamIdentity } = require('./nuvio_client_lab.cjs');
const { releaseIdentityGuard } = require('./native_fixture_identity_guard.cjs');
const { readerFailureClass, readerSignature, isReaderFailure } = require('./native_player_diagnostics.cjs');

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
  const strategy = String(patch.capability || (typeof configured === 'object' ? configured.strategy : configured) || manifestRow.capability || 'unknown');
  const allowEmbed = strategy === 'iframe_player' || (strategy === 'mixed_embed_resolver' && (manifestRow.supportsExternalPlayer === true || patch.preserve_embed_urls === true));
  return { strategy, allowEmbed };
}
function withPolicy(row) {
  const policy = providerPolicy(row.provider);
  return { ...row, capability: policy.strategy, allowEmbed: policy.allowEmbed };
}
function routeType(f) { return String(f.request_type || 'unknown').toLowerCase(); }
function routeMode(f) { return String(f.route_mode || 'declared').toLowerCase(); }
function isProbe(row) { return row.routeMode === 'capability_probe'; }
function streamKey(client, provider, requestType, index = 0) {
  return `${client}\u0000${provider}\u0000${requestType}\u0000${index}`;
}

const results = new Map();
const rows = [];
const transports = new Map();
const players = new Map();
const runtimeErrors = [];
const skippedProviders = [];
for (const input of logPaths) {
  if (!fs.existsSync(input)) continue;
  const text = fs.readFileSync(input, 'utf8');
  for (const raw of text.split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_');
    if (marker < 0) continue;
    const line = raw.slice(marker).trim();
    const f = fields(line);
    if (line.startsWith('FIELD_NATIVE_PROVIDER_SKIPPED ')) {
      skippedProviders.push(withPolicy({
        client: f.client || 'unknown', provider: decode(f.provider64), requestedType: f.requested_type || 'unknown',
        enabled: f.enabled === 'true', reason: f.reason || 'unknown', declaredTypes: decode(f.declared_types64),
      }));
    } else if (line.startsWith('FIELD_NATIVE_RESULT ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      const requestType = routeType(f);
      results.set(`${client}\u0000${provider}\u0000${requestType}`, withPolicy({
        client, provider, requestType, routeMode: routeMode(f), enabled: f.enabled === 'true',
        durationMs: Number(f.duration_ms || 0), count: Number(f.count || 0),
      }));
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      const host = decode(f.host64);
      const mediaHint = decode(f.media_hint64);
      rows.push(withPolicy({
        client: f.client || 'unknown', provider: decode(f.provider64), requestType: routeType(f), routeMode: routeMode(f),
        index: Number(f.index || 0), host, mediaHint,
        stream: {
          title: decode(f.title64), name: decode(f.name64), quality: decode(f.quality64), language: decode(f.language64),
          type: decode(f.type64), mediaHint, url: safeSyntheticUrl(host, mediaHint),
        },
      }));
    } else if (line.startsWith('FIELD_NATIVE_TRANSPORT ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      const requestType = routeType(f);
      const index = Number(f.index || 0);
      transports.set(streamKey(client, provider, requestType, index), withPolicy({
        client, provider, requestType, routeMode: routeMode(f), index,
        state: f.state || 'unknown', kind: f.kind || 'unknown', status: Number(f.status || 0),
        contentType: decode(f.content_type64), extm3u: f.extm3u === 'true', durationSeconds: Number(f.duration_seconds || 0) || null,
        host: decode(f.host64), mediaHint: decode(f.media_hint64),
      }));
    } else if (line.startsWith('FIELD_NATIVE_PLAYER ')) {
      const provider = decode(f.provider64);
      const client = f.client || 'unknown';
      const requestType = routeType(f);
      const index = Number(f.index || 0);
      const player = withPolicy({
        client, provider, requestType, routeMode: routeMode(f), index,
        state: f.state || 'unknown', engine: f.engine || 'unknown',
        httpStatus: Number(f.http_status || 0), failureStage: f.failure_stage || 'unknown',
        durationSeconds: Number(f.duration_seconds || 0) || null, host: decode(f.host64),
        errorClass: decode(f.error_class64), errorCode: decode(f.error_code64),
        exceptionChain: decode(f.exception_chain64), responseHeaderNames: decode(f.response_header_names64),
        loadBytes: Math.max(0, Number(f.load_bytes || 0) || 0),
        loadDurationMs: Math.max(0, Number(f.load_duration_ms || 0) || 0),
        mediaDataType: Number.isFinite(Number(f.media_data_type)) ? Number(f.media_data_type) : -1,
        trackType: Number.isFinite(Number(f.track_type)) ? Number(f.track_type) : -1,
      });
      player.failureClass = readerFailureClass(player);
      player.signature = readerSignature(player);
      players.set(streamKey(client, provider, requestType, index), player);
    } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
      runtimeErrors.push(withPolicy({
        client: f.client || 'unknown', provider: decode(f.provider64), requestType: routeType(f), routeMode: routeMode(f),
        durationMs: Number(f.duration_ms || 0), error: decode(f.error64),
      }));
    }
  }
}

const contradictions = [];
const matches = [];
const unknown = [];
for (const row of rows) {
  let identity = streamIdentity(row.stream, fixture);
  const releaseGuard = releaseIdentityGuard(row.stream, fixture);
  if (releaseGuard) {
    // A pre-existing hard contradiction (wrong title/episode) stays authoritative.
    // Otherwise the release collision guard may downgrade a title match to unknown,
    // or turn an explicit wrong release year into a contradiction.
    if (identity.status !== 'contradiction' || releaseGuard.status === 'contradiction') {
      identity = { status: releaseGuard.status, reason: releaseGuard.reason };
    }
  }
  const transport = transports.get(streamKey(row.client, row.provider, row.requestType, row.index));
  const player = players.get(streamKey(row.client, row.provider, row.requestType, row.index));
  const measuredDuration = player?.durationSeconds || transport?.durationSeconds || null;
  const durationRatio = expectedDurationSeconds && measuredDuration ? measuredDuration / expectedDurationSeconds : null;
  if (durationRatio != null && (durationRatio < minimumDurationRatio || durationRatio > maximumDurationRatio)) {
    identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };
  } else if (identity.status === 'unknown' && durationRatio != null && !releaseGuard?.preventDurationPromotion) {
    identity = { status: 'match', reason: 'fixture_duration_match' };
  }
  const record = {
    client: row.client, provider: row.provider, requestType: row.requestType, routeMode: row.routeMode,
    capability: row.capability, index: row.index, status: identity.status, reason: identity.reason,
    title: row.stream.title, name: row.stream.name, host: row.host || null, mediaHint: row.mediaHint || null, durationRatio,
    expectedYear: releaseGuard?.expectedYear || Number(fixture.year || 0) || null,
    observedYears: releaseGuard?.observedYears || [],
  };
  if (identity.status === 'contradiction') contradictions.push(record);
  else if (identity.status === 'match') matches.push(record);
  else unknown.push(record);
}

const expectedEmbeds = [...transports.values()].filter((row) => row.state === 'dead' && row.kind === 'html' && row.allowEmbed).map((row) => ({ ...row, state: 'embed' }));
const allTransportFailures = [...transports.values()].filter((row) => (row.state === 'dead' || row.state === 'error') && !(row.state === 'dead' && row.kind === 'html' && row.allowEmbed));
const transportFailures = allTransportFailures.filter((row) => !isProbe(row));
const capabilityTransportFailures = allTransportFailures.filter(isProbe);
const transportUnknown = [...transports.values()].filter((row) => row.state === 'unknown' && !isProbe(row));
const transportOk = [...transports.values()].filter((row) => row.state === 'ok' && !isProbe(row));
const allReaderFailures = [...players.values()].filter(isReaderFailure);
const readerFailures = allReaderFailures.filter((row) => !isProbe(row));
const capabilityReaderFailures = allReaderFailures.filter(isProbe);
const readerHealthy = [...players.values()].filter((row) => !isProbe(row) && !isReaderFailure(row));
const capabilityReaderHealthy = [...players.values()].filter((row) => isProbe(row) && !isReaderFailure(row));
const declaredRuntimeErrors = runtimeErrors.filter((row) => !isProbe(row));
const capabilityRuntimeErrors = runtimeErrors.filter(isProbe);
const declaredContradictions = contradictions.filter((row) => !isProbe(row));
const capabilityContradictions = contradictions.filter(isProbe);
const capabilityMatches = matches.filter(isProbe);
const capabilityUnknown = unknown.filter(isProbe);
const slow = [...results.values()].filter((row) => !isProbe(row) && row.durationMs >= 30000).sort((a, b) => b.durationMs - a.durationMs);
const nonEmpty = [...results.values()].filter((row) => !isProbe(row) && row.count > 0);
const empty = [...results.values()].filter((row) => !isProbe(row) && row.count === 0);
const capabilityExecutions = [...results.values()].filter(isProbe);
const allObservedRows = [...results.values(), ...runtimeErrors, ...skippedProviders];
const clients = [...new Set(allObservedRows.map((row) => row.client))].sort();
const providers = [...new Set(allObservedRows.map((row) => row.provider).filter(Boolean))].sort();
const readerFailureClasses = Object.fromEntries([...new Set(readerFailures.map((row) => row.failureClass))].sort().map((cls) => [cls, readerFailures.filter((row) => row.failureClass === cls).length]));

const summary = {
  fixture: fixtureSlug, title: fixture.title, tmdbId: fixture.tmdbId, clients,
  providerCount: providers.length,
  executions: [...results.values()].filter((row) => !isProbe(row)).length,
  capabilityExecutions: capabilityExecutions.length,
  skippedUnsupported: skippedProviders.length,
  nonEmpty: nonEmpty.length, empty: empty.length,
  runtimeErrors: declaredRuntimeErrors.length,
  capabilityRuntimeErrors: capabilityRuntimeErrors.length,
  identityMatches: matches.filter((row) => !isProbe(row)).length,
  identityUnknown: unknown.filter((row) => !isProbe(row)).length,
  identityContradictions: declaredContradictions.length,
  capabilityIdentityMatches: capabilityMatches.length,
  capabilityIdentityUnknown: capabilityUnknown.length,
  capabilityIdentityContradictions: capabilityContradictions.length,
  transportOk: transportOk.length,
  transportExpectedEmbeds: expectedEmbeds.filter((row) => !isProbe(row)).length,
  transportUnknown: transportUnknown.length,
  transportFailures: transportFailures.length,
  capabilityTransportFailures: capabilityTransportFailures.length,
  nativeReaderObserved: [...players.values()].filter((row) => !isProbe(row)).length,
  nativeReaderHealthy: readerHealthy.length,
  nativeReaderFailures: readerFailures.length,
  capabilityReaderObserved: [...players.values()].filter(isProbe).length,
  capabilityReaderHealthy: capabilityReaderHealthy.length,
  capabilityReaderFailures: capabilityReaderFailures.length,
  readerFailureClasses,
  durationEvidence: rows.filter((row) => {
    if (isProbe(row)) return false;
    const key = streamKey(row.client, row.provider, row.requestType, row.index);
    return Boolean(players.get(key)?.durationSeconds || transports.get(key)?.durationSeconds);
  }).length,
  readerLoadErrorEvidence: [...players.values()].filter((row) => !isProbe(row) && (row.loadDurationMs > 0 || row.loadBytes > 0 || row.httpStatus > 0)).length,
  slowProviders: slow.length,
};

console.log(`FIELD_NATIVE_CORPUS_ANALYSIS ${JSON.stringify(summary)}`);
for (const row of declaredContradictions.slice(0, 80)) console.log(`FIELD_NATIVE_CONTRADICTION ${JSON.stringify(row)}`);
for (const row of expectedEmbeds.filter((entry) => !isProbe(entry)).slice(0, 80)) console.log(`FIELD_NATIVE_EXPECTED_EMBED ${JSON.stringify(row)}`);
for (const row of transportFailures.slice(0, 80)) console.log(`FIELD_NATIVE_TRANSPORT_FAILURE ${JSON.stringify(row)}`);
for (const row of readerFailures.slice(0, 120)) console.log(`FIELD_NATIVE_PLAYER_FAILURE ${JSON.stringify(row)}`);
for (const row of declaredRuntimeErrors.slice(0, 80)) console.log(`FIELD_NATIVE_RUNTIME_ERROR ${JSON.stringify(row)}`);
for (const row of slow.slice(0, 80)) console.log(`FIELD_NATIVE_SLOW ${JSON.stringify(row)}`);

for (const row of capabilityMatches.slice(0, 160)) console.log(`FIELD_NATIVE_CAPABILITY_PROBE_IDENTITY_MATCH ${JSON.stringify(row)}`);
for (const row of capabilityContradictions.slice(0, 160)) console.log(`FIELD_NATIVE_CAPABILITY_PROBE_CONTRADICTION ${JSON.stringify(row)}`);
for (const row of capabilityReaderFailures.slice(0, 160)) console.log(`FIELD_NATIVE_CAPABILITY_PROBE_PLAYER_FAILURE ${JSON.stringify(row)}`);
for (const row of capabilityRuntimeErrors.slice(0, 160)) console.log(`FIELD_NATIVE_CAPABILITY_PROBE_RUNTIME_ERROR ${JSON.stringify(row)}`);

// Capability probes are discovery evidence. Their failures never turn a healthy
// declared provider contract into a regression. Only published-route anomalies
// affect this analyzer's status.
if (declaredRuntimeErrors.length || declaredContradictions.length || transportFailures.length || readerFailures.length) process.exitCode = 1;
