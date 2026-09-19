import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const script = path.join(repo, 'engine_v2/scripts/learning-lab.mjs');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-learning-test-'));
const out = path.join(tmp, 'out');
const repair = path.join(tmp, 'repair.json');
const previous = path.join(tmp, 'previous.json');
const historical = path.join(tmp, 'historical.json');
const portfolio = path.join(tmp, 'portfolio.json');
const overrides = path.join(tmp, 'overrides.json');

write(repair, {
  brain: { plans: { 'published:foo': { providerId: 'foo', failureClass: 'search_gap', signature: 'sig-foo' } } },
  rounds: [{
    attempts: [{ parent_key: 'published:foo', repair_key: 'r1', profile: 'adaptive_runtime_recovery', status: 'generated' }],
    accepted: [],
    rejected: [{ parent_key: 'published:foo', repair_key: 'r1', profile: 'adaptive_runtime_recovery', reason: 'no improvement' }],
  }],
});
const readerMemory = {
  schemaVersion: 1,
  updatedAt: '2026-08-18T00:00:00Z',
  importedOutcomesThisRun: 1,
  entries: [{
    providerId: 'moviesdrive', fixture: 'sinners-2025', failureClass: 'playback_http_access',
    skill: 'global_media_enrichment_v1', attempts: 2, successes: 1, failures: 1, inconclusive: 0,
    consecutiveFailures: 0, lastOutcome: 'accepted', lastReason: 'fresh_native_reader_proof_green', lastSeenAt: '2026-08-18T00:00:00Z',
  }],
  skillStats: [{
    skill: 'global_media_enrichment_v1', attempts: 2, successes: 1, failures: 1, inconclusive: 0,
    provenProviderCount: 1, failedProviderCount: 0, provenProviders: ['moviesdrive'], failedProviders: [], maturity: 'promising',
  }],
  readerBacklog: {
    schemaVersion: 1,
    updatedAt: '2026-08-18T00:00:00Z',
    lastRunId: '12345',
    importedRunIds: ['12345'],
    importedEvidenceIds: ['abc123'],
    openCount: 1,
    resolvedCount: 0,
    externalCandidateOpenCount: 1,
    entries: [{
      id: 'reader-bug-1', client: 'tv', providerId: 'moviesdrive', fixture: 'sinners-2025',
      requestType: 'movie', failureClass: 'playback_http_access', layer: 'playback_transport',
      scope: 'external_or_context', status: 'open', externalCandidate: true, providerJsMutationAllowed: false,
      occurrences: 2, consecutiveFailures: 2, healthyRetests: 0,
      firstSeenAt: '2026-08-18T00:00:00Z', lastSeenAt: '2026-08-18T00:00:00Z', resolvedAt: null,
      lastRunId: '12345', lastOutcome: 'failure', lastReason: 'playback_http_access',
      hypotheses: ['replay-native-request-context'],
    }],
  },
};
write(previous, {
  learnedSkills: {
    'search_gap:adaptive_runtime_recovery': {
      id: 'search_gap:adaptive_runtime_recovery',
      failureClass: 'search_gap',
      profile: 'adaptive_runtime_recovery',
      actions: ['apply validated adaptive_runtime_recovery strategy for search_gap'],
      capabilities: ['search', 'routes'],
      providers: ['legacy-provider'],
      successCount: 2,
      failureCount: 0,
      validated: true,
      confidence: 1,
      maturity: 'candidate',
      autoApply: false,
      lastValidatedMode: 'learning',
    },
  },
  experimentMemory: { entries: [{
    providerId: 'foo', providerVersion: '*', signature: 'sig-foo', failureClass: 'search_gap', profile: 'adaptive_runtime_recovery',
    attempts: 1, successes: 0, failures: 1, consecutiveFailures: 1, lastOutcome: 'rejected', lastReason: 'no improvement', lastSeenAt: '2026-08-16T00:00:00Z',
  }] },
  nativeReaderRepairMemory: readerMemory,
  nativeFeedback: { readerRepairAccepted: 3, readerRepairRejected: 2, readerRepairInconclusive: 1 },
});
write(historical, {
  baseline: { id: 'excel-provider-audit-5.20.63', release: '5.20.63' },
  stats: { unresolvedHighPriority: 1 },
  cases: [{ providerId: 'foo', trainingRole: 'unresolved', priority: 'high', delta: 'persistent_unresolved', sandboxRepair: { failureClasses: ['search_gap'], profilesAttempted: ['adaptive_runtime_recovery'] } }],
});
write(portfolio, {
  observedProviders: 1,
  providers: [{ provider: 'foo', recommendation: 'repair_runtime_or_transport', runtimeErrors: 1, transportFailures: 0, identityContradictions: 0, catalogueCoverageRate: 0.2, score: 10 }],
});
write(overrides, { runtime_repair: { learned_skills: {
  'search_gap:adaptive_runtime_recovery': {
    id: 'search_gap:adaptive_runtime_recovery',
    failureClass: 'search_gap',
    profile: 'adaptive_runtime_recovery',
    actions: ['apply validated adaptive_runtime_recovery strategy for search_gap'],
    capabilities: ['search', 'parser'],
    providers: ['foo'],
    successCount: 3,
    failureCount: 0,
    validated: true,
    confidence: 1,
    maturity: 'trusted',
    autoApply: true,
    lastValidatedMode: 'learning',
  },
} } });

const result = spawnSync(process.execPath, [script,
  '--output-dir', out,
  '--repair-report', repair,
  '--previous-state', previous,
  '--historical-training', historical,
  '--provider-portfolio', portfolio,
  '--overrides', overrides,
], { cwd: repo, encoding: 'utf8' });
assert.equal(result.status, 0, result.stderr);
const latest = JSON.parse(fs.readFileSync(path.join(out, 'latest.json'), 'utf8'));
const entry = latest.experimentMemory.entries.find((row) => row.providerId === 'foo' && row.profile === 'adaptive_runtime_recovery');
assert.ok(entry, 'negative-memory entry missing');
assert.equal(entry.failures, 2);
assert.equal(entry.consecutiveFailures, 2);
assert.ok(latest.proposals.some((row) => row.type === 'avoid_failed_profile' && row.providerId === 'foo'));
assert.ok(latest.proposals.some((row) => row.type === 'historical_provider_repair_target' && row.providerId === 'foo'));
assert.ok(latest.proposals.some((row) => row.type === 'native_cross_device_repair_target' && row.providerId === 'foo'));
assert.deepEqual(latest.nativeReaderRepairMemory, readerMemory, 'daily Brain learning must preserve repair memory and reader backlog');
assert.equal(latest.nativeReaderRepairMemory.readerBacklog.openCount, 1);
assert.equal(latest.nativeFeedback.readerRepairAccepted, 3);
assert.equal(latest.nativeFeedback.readerRepairRejected, 2);
assert.equal(latest.nativeFeedback.readerRepairInconclusive, 1);
assert.equal(latest.productionWritesAllowed, false);
assert.equal(latest.publicationAllowed, false);
const learned = latest.learnedSkills['search_gap:adaptive_runtime_recovery'];
assert.ok(learned, 'positive learned skill memory missing');
assert.deepEqual(learned.providers.sort(), ['foo', 'legacy-provider']);
assert.equal(learned.successCount, 3);
assert.equal(learned.maturity, 'trusted');
assert.equal(learned.autoApply, true);
assert.ok(learned.capabilities.includes('parser'));
assert.equal(latest.learnedSkillCount, 1);
console.log('learning lab positive/negative memory, native-reader-memory and backlog preservation tests passed');

function write(file, value) {
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n');
}
