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
write(previous, {
  experimentMemory: { entries: [{
    providerId: 'foo', providerVersion: '*', signature: 'sig-foo', failureClass: 'search_gap', profile: 'adaptive_runtime_recovery',
    attempts: 1, successes: 0, failures: 1, consecutiveFailures: 1, lastOutcome: 'rejected', lastReason: 'no improvement', lastSeenAt: '2026-08-16T00:00:00Z',
  }] },
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
write(overrides, { runtime_repair: { learned_skills: {} } });

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
assert.equal(latest.productionWritesAllowed, false);
assert.equal(latest.publicationAllowed, false);
console.log('learning lab negative-memory tests passed');

function write(file, value) {
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n');
}
