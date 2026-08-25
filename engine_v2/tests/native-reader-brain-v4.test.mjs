import assert from 'node:assert/strict';
import { BRAIN_CONTROL_PLANE_VERSION, classifyFailure, planRepair } from '../src/repair-brain.mjs';
import { classifySystemicExtraction } from '../src/runtime-systemic.mjs';

assert.equal(BRAIN_CONTROL_PLANE_VERSION, 4);

const cases = [
  [{ stages: { reader: { attempted: true, state: 'error', httpStatus: 403, failureStage: 'http_access' } } }, 'playback_http_access', 'replay-native-request-context'],
  [{ stages: { reader: { attempted: true, state: 'error', httpStatus: 404, failureStage: 'http_gone' } } }, 'playback_http_gone', 'refresh-terminal-media-candidate'],
  [{ stages: { reader: { attempted: true, state: 'error', httpStatus: 429, failureStage: 'http_rate_limit' } } }, 'playback_rate_limited', 'respect-media-rate-limit'],
  [{ stages: { reader: { attempted: true, state: 'timeout', failureStage: 'timeout' } } }, 'playback_timeout', 'diagnose-native-reader-timeout'],
  [{ stages: { reader: { attempted: true, state: 'error', failureStage: 'dns' } } }, 'playback_dns', 'repair-media-host-resolution'],
  [{ stages: { reader: { attempted: true, state: 'error', failureStage: 'tls' } } }, 'playback_tls', 'repair-media-tls-path'],
  [{ stages: { reader: { attempted: true, state: 'error', failureStage: 'parser' } } }, 'playback_parser', 'resolve-real-media-not-wrapper'],
  [{ stages: { reader: { attempted: true, state: 'error', failureStage: 'decoder' } } }, 'playback_decoder', 'rerank-reader-compatible-encoding'],
  [{ stages: { reader: { attempted: true, state: 'error', failureStage: 'io' } } }, 'playback_io', 'repair-reader-io-contract'],
  [{ stages: { reader: { attempted: true, state: 'short_media', failureStage: 'duration_identity' } } }, 'short_media', 'reject-short-or-preview-media'],
];

for (const [evidence, failureClass, recipe] of cases) {
  assert.equal(classifyFailure(evidence), failureClass, failureClass);
  const plan = planRepair(evidence, { maxHypotheses: 3 });
  assert.equal(plan.failureClass, failureClass);
  assert.equal(plan.hypotheses[0]?.id, recipe, `${failureClass} recipe`);
}

assert.equal(classifyFailure({ stages: { reader: { attempted: true, state: 'ready' } } }), 'healthy');
assert.equal(classifyFailure({ stages: { reader: { observed: true, failureClass: 'playback_parser' } } }), 'playback_parser');

const legacy = { invoked: true, stages: { media: { attempted: true, found: true }, validation: { attempted: true, playable: false, playableCount: 0, statuses: [403] } } };
assert.equal(classifyFailure(legacy), 'playback_context_gap');

const desktopZeros = ['cineby', 'videasy', 'purstream'].map((provider) => ({
  client: 'macos', fixture: 'sinners-2025', provider, requestType: 'movie',
  routeMode: 'declared', enabled: true, count: 0,
}));
const systemic = classifySystemicExtraction(desktopZeros);
assert.equal(systemic.systemicGroups.length, 1);
assert.equal(systemic.systemicGroups[0].providerCount, 3);
assert.equal(systemic.systemicGroups[0].failureClass, 'runtime_contract_drift');
assert.equal(systemic.systemicGroups[0].failureDomain, 'client_runtime');
assert.equal(systemic.systemicGroups[0].providerMutationEligible, false);
assert.equal(systemic.systemicExecutionKeys.size, 3);

const oneProvider = classifySystemicExtraction(desktopZeros.slice(0, 1));
assert.equal(oneProvider.systemicGroups.length, 0, 'one empty provider remains provider-level evidence');

const healthyPeers = desktopZeros.slice(0, 2).map((row) => ({ ...row, client: 'tv', count: 2 }));
const peerConfirmed = classifySystemicExtraction([...desktopZeros.slice(0, 2), ...healthyPeers]);
assert.equal(peerConfirmed.systemicGroups.length, 1);
assert.equal(peerConfirmed.systemicGroups[0].confidence, 'confirmed_by_healthy_peers');
assert.deepEqual(peerConfirmed.systemicGroups[0].healthyPeerProviders, ['cineby', 'videasy']);

console.log('Brain v4 native reader causality + systemic runtime tests passed');
