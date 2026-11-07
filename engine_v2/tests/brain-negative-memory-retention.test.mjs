import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { retainBoundedBrainExperiments } from '../src/brain-negative-memory-retention.mjs';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const policy = JSON.parse(fs.readFileSync(path.join(repo, 'engine_v2/config/brain-policy.json'), 'utf8'));
const learnedCap = policy.learningLab?.memoryMaxEntries;
const productionCap = policy.production?.negativeExperimentMemory?.maxEntries;
assert.equal(learnedCap, 16000, 'Learning budget must cover 800-hub retained experiments');
assert.equal(learnedCap, productionCap, 'Learning and production memories must share a bounded capacity');

const rows = [];
// 800 independent providers with 12 negative observations each.
// They are older than a very active hub, reproducing hot-provider eviction
// under the old global recency-only 1000-row cap.
for (let provider = 0; provider < 800; provider += 1) {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    rows.push({
      providerId: 'hub-' + String(provider).padStart(4, '0'),
      signature: 'fixture-' + attempt,
      profile: 'strategy-' + attempt,
      experimentGeneration: 1,
      experimentVariant: attempt % 5,
      failures: 1,
      consecutiveFailures: 1,
      lastOutcome: 'rejected',
      executionObserved: true,
      lastSeenAt: '2026-01-01T00:' + String(attempt).padStart(2, '0') + ':00Z',
    });
  }
}
for (let attempt = 0; attempt < 18000; attempt += 1) {
  rows.push({
    providerId: 'hub-0000',
    signature: 'extra-hot-' + attempt,
    profile: 'search_contract_inference_v1',
    failures: 1,
    consecutiveFailures: 1,
    lastOutcome: 'rejected',
    executionObserved: true,
    lastSeenAt: '2026-11-07T12:00:00Z',
  });
}
const chosen = retainBoundedBrainExperiments(rows, {
  limit: learnedCap,
  minimumPerProvider: 12,
});
assert.equal(chosen.length, 16000, 'strict capacity must hold at catalogue scale');
const counts = new Map();
for (const row of chosen) {
  counts.set(row.providerId, (counts.get(row.providerId) ?? 0) + 1);
}
assert.equal(counts.size, 800, 'no provider may be evicted due to a hotter neighbor');
for (let provider = 0; provider < 800; provider += 1) {
  const id = 'hub-' + String(provider).padStart(4, '0');
  assert.ok(counts.get(id) >= 12, 'retained provenance lost for ' + id);
}
assert.deepEqual(
  retainBoundedBrainExperiments(chosen, { limit: learnedCap, minimumPerProvider: 12 }),
  chosen,
  'bounded persistence should be stable across repeated Learning runs',
);

// Under tighter budgets, use a deterministic round-robin rather than
// discarding the full evidence history of quieter providers.
const tight = retainBoundedBrainExperiments(rows, {
  limit: 800,
  minimumPerProvider: 12,
});
assert.equal(tight.length, 800);
assert.equal(new Set(tight.map(row => row.providerId)).size, 800);
assert.equal(retainBoundedBrainExperiments([], { limit: 16000 }).length, 0);
assert.equal(retainBoundedBrainExperiments(rows, { limit: Infinity }).length, 1000);
assert.equal(rows.length, 27600, 'retention must not mutate input evidence');

// These records are experiment memory, NOT media validation or publication.
console.log(JSON.stringify({
  schema: 'brain-provider-fair-negative-retention',
  providersPreserved: counts.size,
  entriesRetained: chosen.length,
  bounded: true,
  playbackProof: false,
  publicationAuthority: false,
}));
