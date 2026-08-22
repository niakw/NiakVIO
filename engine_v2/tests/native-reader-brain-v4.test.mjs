import assert from 'node:assert/strict';
import { BRAIN_CONTROL_PLANE_VERSION, classifyFailure, planRepair } from '../src/repair-brain.mjs';

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

console.log('Brain v4 native reader causality tests passed');
