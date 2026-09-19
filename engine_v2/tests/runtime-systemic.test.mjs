import assert from 'node:assert/strict';
import {
  classifySystemicExtraction,
  extractionExecutionKey,
} from '../src/runtime-systemic.mjs';

function result({ client, provider, count, fixture = 'fixture-a', requestType = 'tv' }) {
  return {
    client,
    fixture,
    provider,
    requestType,
    routeMode: 'declared',
    enabled: true,
    count,
  };
}

// Regression: a large number of independent zero-stream providers on one client
// is not proof of a shared runtime failure. This was the retry-39 false positive
// that promoted most TV/anime extraction failures to runtime_contract_drift.
{
  const rows = [
    result({ client: 'tv', provider: 'alpha', count: 0 }),
    result({ client: 'tv', provider: 'beta', count: 0 }),
    result({ client: 'tv', provider: 'gamma', count: 0 }),
    result({ client: 'tv', provider: 'delta', count: 0 }),
  ];
  const classified = classifySystemicExtraction(rows);
  assert.equal(classified.systemicGroups.length, 0);
  assert.equal(classified.systemicExecutionKeys.size, 0);
}

// A client/runtime drift remains actionable when independent clients prove that
// at least two of the exact same provider routes are healthy.
{
  const tvAlpha = result({ client: 'tv', provider: 'alpha', count: 0 });
  const tvBeta = result({ client: 'tv', provider: 'beta', count: 0 });
  const rows = [
    tvAlpha,
    tvBeta,
    result({ client: 'desktop', provider: 'alpha', count: 2 }),
    result({ client: 'desktop', provider: 'beta', count: 1 }),
  ];
  const classified = classifySystemicExtraction(rows);
  assert.equal(classified.systemicGroups.length, 1);
  assert.equal(classified.systemicGroups[0].failureClass, 'runtime_contract_drift');
  assert.equal(classified.systemicGroups[0].failureDomain, 'client_runtime');
  assert.equal(classified.systemicGroups[0].confidence, 'confirmed_by_healthy_peers');
  assert.equal(classified.systemicGroups[0].healthyPeerProviderCount, 2);
  assert.equal(classified.systemicExecutionKeys.has(extractionExecutionKey(tvAlpha)), true);
  assert.equal(classified.systemicExecutionKeys.has(extractionExecutionKey(tvBeta)), true);
}

// One isolated healthy route is not enough to relabel a whole failed group as a
// client runtime regression.
{
  const rows = [
    result({ client: 'tv', provider: 'alpha', count: 0 }),
    result({ client: 'tv', provider: 'beta', count: 0 }),
    result({ client: 'tv', provider: 'gamma', count: 0 }),
    result({ client: 'desktop', provider: 'alpha', count: 1 }),
  ];
  const classified = classifySystemicExtraction(rows);
  assert.equal(classified.systemicGroups.length, 0);
  assert.equal(classified.systemicExecutionKeys.size, 0);
}

console.log('runtime-systemic.test.mjs: ok');
