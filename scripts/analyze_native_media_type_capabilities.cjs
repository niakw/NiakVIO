#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { streamIdentity } = require('./nuvio_client_lab.cjs');
const { isReaderFailure, readerFailureClass } = require('./native_player_diagnostics.cjs');
const { assessNativeEvidence } = require('./native_evidence_completeness.cjs');

const root = path.resolve(__dirname, '..');

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
function routeKey(client, provider, requestType) {
  return `${client}\u0000${provider.toLowerCase()}\u0000${requestType.toLowerCase()}`;
}
function streamKey(route, index) { return `${route}\u0000${Number(index || 0)}`; }
function routeFields(f) {
  return {
    client: f.client || 'unknown',
    provider: decode(f.provider64).toLowerCase(),
    requestType: String(f.request_type || 'unknown').toLowerCase(),
    routeMode: String(f.route_mode || 'declared').toLowerCase(),
  };
}

function analyzeMediaTypeCapabilities(fixtureSlug, inputLogPaths) {
  const logPaths = inputLogPaths.map((file) => path.resolve(file));
  const config = JSON.parse(fs.readFileSync(path.join(root, '.github/triggers/nuvio-client-lab.json'), 'utf8'));
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
  const fixtureRow = (config.fixtures || []).find((row) => row && row.slug === fixtureSlug);
  if (!fixtureRow || !fixtureRow.fixture) throw new Error(`unknown corpus fixture: ${fixtureSlug}`);
  const fixture = fixtureRow.fixture;
  const expectedDurationSeconds = Number(fixture.expectedDurationMinutes || 0) * 60 || null;
  const minimumDurationRatio = Number(config.policy?.minimum_duration_ratio || 0.55);
  const maximumDurationRatio = Number(config.policy?.maximum_duration_ratio || 1.8);
  const manifestTypes = new Map((manifest.scrapers || []).filter(Boolean).map((row) => [
    String(row.id || '').toLowerCase(),
    new Set((row.supportedTypes || []).map((value) => String(value).toLowerCase())),
  ]));

  const evidence = assessNativeEvidence(logPaths);
  const routes = new Map();
  const rows = new Map();
  const players = new Map();
  const runtimeErrors = new Map();

  for (const input of logPaths) {
    if (!fs.existsSync(input)) continue;
    for (const raw of fs.readFileSync(input, 'utf8').split(/\r?\n/)) {
      const marker = raw.indexOf('FIELD_NATIVE_');
      if (marker < 0) continue;
      const line = raw.slice(marker).trim();
      const f = fields(line);
      if (f.fixture && f.fixture !== fixtureSlug) continue;
      if (line.startsWith('FIELD_NATIVE_RESULT ')) {
        const meta = routeFields(f);
        if (meta.routeMode !== 'capability_probe') continue;
        routes.set(routeKey(meta.client, meta.provider, meta.requestType), {
          ...meta,
          returned: Math.max(0, Number(f.count || 0) || 0),
        });
      } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
        const meta = routeFields(f);
        if (meta.routeMode !== 'capability_probe') continue;
        const host = decode(f.host64);
        const mediaHint = decode(f.media_hint64);
        rows.set(streamKey(routeKey(meta.client, meta.provider, meta.requestType), f.index), {
          ...meta,
          index: Number(f.index || 0),
          stream: {
            title: decode(f.title64), name: decode(f.name64), quality: decode(f.quality64),
            language: decode(f.language64), type: decode(f.type64), url: safeSyntheticUrl(host, mediaHint),
          },
        });
      } else if (line.startsWith('FIELD_NATIVE_PLAYER ')) {
        const meta = routeFields(f);
        if (meta.routeMode !== 'capability_probe') continue;
        const player = {
          ...meta,
          index: Number(f.index || 0), state: f.state || 'unknown', engine: f.engine || 'unknown',
          httpStatus: Number(f.http_status || 0), failureStage: f.failure_stage || 'unknown',
          durationSeconds: Number(f.duration_seconds || 0) || null,
          errorCode: decode(f.error_code64), errorClass: decode(f.error_class64),
        };
        player.failureClass = readerFailureClass(player);
        players.set(streamKey(routeKey(meta.client, meta.provider, meta.requestType), f.index), player);
      } else if (line.startsWith('FIELD_NATIVE_ERROR ')) {
        const meta = routeFields(f);
        if (meta.routeMode !== 'capability_probe') continue;
        const key = routeKey(meta.client, meta.provider, meta.requestType);
        runtimeErrors.set(key, (runtimeErrors.get(key) || 0) + 1);
      }
    }
  }

  function identityFor(row, player) {
    let identity = streamIdentity(row.stream, fixture);
    const duration = player?.durationSeconds || null;
    const ratio = expectedDurationSeconds && duration ? duration / expectedDurationSeconds : null;
    if (ratio != null && (ratio < minimumDurationRatio || ratio > maximumDurationRatio)) {
      identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };
    } else if (identity.status === 'unknown' && ratio != null) {
      identity = { status: 'match', reason: 'fixture_duration_match' };
    }
    return { ...identity, durationRatio: ratio };
  }

  const outcomes = [];
  const proposals = [];
  for (const [key, route] of routes) {
    const declared = manifestTypes.get(route.provider) || new Set();
    const declaredAlready = declared.has(route.requestType);
    const routeRows = [];
    const reasons = [];
    if (declaredAlready) reasons.push('probe_type_already_declared');
    if (route.returned <= 0) reasons.push('no_streams_returned');
    if ((runtimeErrors.get(key) || 0) > 0) reasons.push('runtime_error');

    let healthyPlayers = 0;
    let identityMatches = 0;
    let identityUnknown = 0;
    let identityContradictions = 0;
    for (let index = 0; index < route.returned; index += 1) {
      const row = rows.get(streamKey(key, index));
      const player = players.get(streamKey(key, index));
      if (!row) reasons.push(`missing_row:${index}`);
      if (!player) reasons.push(`missing_player:${index}`);
      if (!row || !player) continue;
      if (isReaderFailure(player)) {
        reasons.push(`reader_failure:${index}:${player.failureClass}`);
      } else {
        healthyPlayers += 1;
      }
      const identity = identityFor(row, player);
      if (identity.status === 'match') identityMatches += 1;
      else if (identity.status === 'contradiction') {
        identityContradictions += 1;
        reasons.push(`identity_contradiction:${index}:${identity.reason}`);
      } else {
        identityUnknown += 1;
        reasons.push(`identity_unproven:${index}:${identity.reason}`);
      }
      routeRows.push({ index, playerState: player.state, failureClass: player.failureClass, identity });
    }

    const proven = evidence.complete && !declaredAlready && route.returned > 0 &&
      healthyPlayers === route.returned && identityMatches === route.returned &&
      identityUnknown === 0 && identityContradictions === 0 &&
      (runtimeErrors.get(key) || 0) === 0 && reasons.length === 0;
    const outcome = {
      client: route.client,
      fixture: fixtureSlug,
      provider: route.provider,
      addType: route.requestType,
      declaredTypes: [...declared].sort(),
      returned: route.returned,
      healthyPlayers,
      identityMatches,
      identityUnknown,
      identityContradictions,
      proven,
      reasons: [...new Set(reasons)],
      streams: routeRows,
    };
    outcomes.push(outcome);
    if (proven) {
      proposals.push({
        provider: route.provider,
        addType: route.requestType,
        client: route.client,
        fixture: fixtureSlug,
        streamCount: route.returned,
        proof: 'all_returned_streams_reader_healthy_and_identity_matched',
        requiresCrossDeviceConfirmation: true,
        productionWritesAllowed: false,
      });
    }
  }

  return {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    fixture: fixtureSlug,
    evidenceComplete: evidence.complete,
    evidenceProblems: evidence.problems,
    capabilityRoutes: outcomes.length,
    provenCapabilities: proposals.length,
    outcomes: outcomes.sort((a, b) => a.provider.localeCompare(b.provider) || a.addType.localeCompare(b.addType) || a.client.localeCompare(b.client)),
    proposals: proposals.sort((a, b) => a.provider.localeCompare(b.provider) || a.addType.localeCompare(b.addType) || a.client.localeCompare(b.client)),
    policy: {
      productionWritesAllowed: false,
      manifestMutationAllowed: false,
      requireCompleteNativeEvidence: true,
      requireEveryReturnedStreamHealthy: true,
      requireEveryReturnedStreamIdentityMatch: true,
      requireCrossDeviceConfirmationBeforeManifestMutation: true,
    },
  };
}

function main() {
  const argv = process.argv.slice(2);
  const outputIndex = argv.indexOf('--output');
  let outputPath = '';
  if (outputIndex >= 0) {
    outputPath = argv[outputIndex + 1] || '';
    argv.splice(outputIndex, 2);
  }
  const fixtureSlug = argv.shift();
  const logPaths = argv;
  if (!fixtureSlug || !logPaths.length) {
    console.error('usage: node scripts/analyze_native_media_type_capabilities.cjs <fixture> [--output report.json] <log> [log ...]');
    process.exit(64);
  }
  const payload = analyzeMediaTypeCapabilities(fixtureSlug, logPaths);
  if (outputPath) {
    const resolved = path.resolve(outputPath);
    fs.mkdirSync(path.dirname(resolved), { recursive: true });
    fs.writeFileSync(resolved, JSON.stringify(payload, null, 2) + '\n');
  }
  console.log(`FIELD_NATIVE_MEDIA_CAPABILITY evidence_complete=${payload.evidenceComplete} routes=${payload.capabilityRoutes} proven=${payload.provenCapabilities}`);
  for (const proposal of payload.proposals.slice(0, 80)) console.log(`FIELD_NATIVE_MEDIA_CAPABILITY_PROVEN ${JSON.stringify(proposal)}`);
  for (const outcome of payload.outcomes.filter((row) => !row.proven).slice(0, 80)) {
    console.log(`FIELD_NATIVE_MEDIA_CAPABILITY_NOT_PROVEN ${JSON.stringify({ provider: outcome.provider, addType: outcome.addType, client: outcome.client, reasons: outcome.reasons })}`);
  }
  if (!payload.evidenceComplete) process.exitCode = 2;
}

if (require.main === module) main();
module.exports = { analyzeMediaTypeCapabilities };
