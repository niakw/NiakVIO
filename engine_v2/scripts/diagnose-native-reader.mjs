#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import { BRAIN_CONTROL_PLANE_VERSION, planRepair } from '../src/repair-brain.mjs';
import { classifySystemicExtraction, extractionExecutionKey } from '../src/runtime-systemic.mjs';

const require = createRequire(import.meta.url);
const {
  readerFailureClass,
  readerFailureDomain,
  providerMutationEligible,
  readerSignature,
  isReaderFailure,
} = require('../../scripts/native_player_diagnostics.cjs');
const { assessNativeEvidence } = require('../../scripts/native_evidence_completeness.cjs');

const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const outputPath = outputIndex >= 0 && args[outputIndex + 1]
  ? path.resolve(args[outputIndex + 1])
  : path.resolve('targeted-reader-brain.json');
const logPaths = args.filter((value, index) => index !== outputIndex && index !== outputIndex + 1 && value !== '--output').map((value) => path.resolve(value));
const nonblockingSmoke = process.env.NIAKVIO_BRAIN_NONBLOCKING === '1';
const RUNTIME_ERROR_SENTINEL = '__NIAKVIO_RUNTIME_ERROR__';

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
function safeText(value, max = 420) {
  return String(value || '')
    .replace(/https?:\/\/\S+/gi, '<url>')
    .replace(/(?:(?:authorization|cookie|token|secret)\s*[:=]\s*)\S+/gi, 'credential=<redacted>')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}
function providerLoadFailureClass(reason) {
  const value = String(reason || '').trim().toLowerCase();
  if (value === 'missing_after_repository_install') return 'provider_repository_load_missing';
  if (value === 'metadata_mismatch' || value === 'metadata_or_code_mismatch') return 'provider_repository_metadata_mismatch';
  return 'provider_repository_load_error';
}
function providerLoadRepair(issue) {
  if (issue.failureClass === 'provider_repository_load_missing') {
    return {
      layer: 'repository',
      providerJsMutationAllowed: false,
      coreOrManifestProposalAllowed: true,
      actions: [
        'verify the provider filename is reachable from the exact pinned manifest SHA',
        'compare the official client platform filter and provider id reconstruction',
        'verify Nuvio downloaded and cached the provider code',
        'repair repository/Core loading before touching provider JS',
        're-run the same official repository installation on the affected device',
      ],
    };
  }
  if (issue.failureClass === 'provider_repository_metadata_mismatch') {
    return {
      layer: 'manifest_contract',
      providerJsMutationAllowed: false,
      coreOrManifestProposalAllowed: true,
      actions: [
        'diff canonical manifest enabled/types against the model reconstructed by Nuvio',
        'inspect manifest parser normalization and cached provider reconstruction',
        'repair manifest/Core adapter semantics instead of provider stream logic',
        're-run cross-device repository loading before publication',
      ],
    };
  }
  return {
    layer: 'repository',
    providerJsMutationAllowed: false,
    coreOrManifestProposalAllowed: true,
    actions: [
      'inspect the first observed repository/provider loading failure',
      'verify manifest download, provider download and cache reconstruction independently',
      'repair the loading layer before provider JS mutation',
      're-run official repository loading on the same device',
    ],
  };
}
function routeKey(row) {
  return `${String(row.provider || '').toLowerCase()}\u0000${row.requestType}\u0000${row.fixture}`;
}
function extractionSignature(row) {
  return `${row.requestType}:media_extraction_gap:${String(row.provider || '').toLowerCase()}:${row.fixture}`;
}
function runtimeExecutionKey(row) {
  return [
    String(row.client || 'unknown').trim().toLowerCase(),
    String(row.fixture || 'unknown'),
    String(row.provider || '').trim().toLowerCase(),
    String(row.requestType || 'unknown').trim().toLowerCase(),
  ].join('\u0000');
}

const evidence = assessNativeEvidence(logPaths);
const readerRows = [];
const resultRows = [];
const providerLoadObservations = [];
const runtimeSentinelByKey = new Map();
for (const file of logPaths) {
  if (!fs.existsSync(file)) continue;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const loadAt = raw.indexOf('FIELD_NATIVE_PROVIDER_LOAD_ERROR ');
    if (loadAt >= 0) {
      const f = fields(raw.slice(loadAt).trim());
      const reason = safeText(f.reason || decode(f.error64) || 'unknown', 240);
      const failureClass = providerLoadFailureClass(reason);
      providerLoadObservations.push({
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64).toLowerCase(),
        reason,
        failureClass,
      });
    }

    const resultAt = raw.indexOf('FIELD_NATIVE_RESULT ');
    if (resultAt >= 0) {
      const f = fields(raw.slice(resultAt).trim());
      resultRows.push({
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64),
        requestType: String(f.request_type || 'unknown').toLowerCase(),
        routeMode: String(f.route_mode || 'declared').toLowerCase(),
        enabled: f.enabled === 'true',
        count: Math.max(0, Number(f.count ?? f.returned ?? 0) || 0),
      });
    }

    const rowAt = raw.indexOf('FIELD_NATIVE_ROW ');
  if (rowAt >= 0) {
    const f = fields(raw.slice(rowAt).trim());
    const type = decode(f.type64);
    const title = decode(f.title64);
    if (type === RUNTIME_ERROR_SENTINEL || title === RUNTIME_ERROR_SENTINEL) {
      const observation = {
        client: f.client || 'unknown',
        fixture: f.fixture || 'unknown',
        provider: decode(f.provider64),
        requestType: String(f.request_type || 'unknown').toLowerCase(),
        routeMode: String(f.route_mode || 'declared').toLowerCase(),
        index: Number(f.index || 0),
        state: 'runtime_error',
        failureClass: 'client_runtime_error',
        failureDomain: 'client_runtime',
        providerMutationEligible: false,
        failureStage: 'provider_runtime',
        httpStatus: 0,
        errorCode: 'RUNTIME_ERROR_SENTINEL',
        host: '',
        durationSeconds: null,
        loadBytes: 0,
        loadDurationMs: 0,
        observationLayer: 'runtime',
      };
      runtimeSentinelByKey.set(runtimeExecutionKey(observation), observation);
    }
  }

    const marker = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (marker < 0) continue;
    const f = fields(raw.slice(marker).trim());
    const row = {
      client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
      requestType: String(f.request_type || 'unknown').toLowerCase(),
      routeMode: String(f.route_mode || 'declared').toLowerCase(),
      index: Number(f.index || 0), state: f.state || 'unknown', engine: f.engine || 'unknown',
      httpStatus: Number(f.http_status || 0), failureStage: f.failure_stage || 'unknown',
      durationSeconds: Number(f.duration_seconds || 0) || null, host: decode(f.host64),
      errorClass: safeText(decode(f.error_class64), 180), errorCode: safeText(decode(f.error_code64), 120),
      exceptionChain: safeText(decode(f.exception_chain64), 800), responseHeaderNames: safeText(decode(f.response_header_names64), 360),
      loadBytes: Math.max(0, Number(f.load_bytes || 0) || 0),
      loadDurationMs: Math.max(0, Number(f.load_duration_ms || 0) || 0),
      mediaDataType: Number.isFinite(Number(f.media_data_type)) ? Number(f.media_data_type) : -1,
      trackType: Number.isFinite(Number(f.track_type)) ? Number(f.track_type) : -1,
    };
    row.failureClass = readerFailureClass(row);
    row.failureDomain = readerFailureDomain(row);
    row.providerMutationEligible = providerMutationEligible(row);
    row.signature = readerSignature({ ...row, requestType: row.requestType });
    readerRows.push(row);
  }
}

const runtimeSentinelObservations = [...runtimeSentinelByKey.values()];
const brainReaderRows = readerRows.filter((row) => !runtimeSentinelByKey.has(runtimeExecutionKey(row)));
const runtimeSentinelReaderRows = readerRows.filter((row) => runtimeSentinelByKey.has(runtimeExecutionKey(row)));
const brainResultRows = resultRows.filter((row) => !runtimeSentinelByKey.has(runtimeExecutionKey(row)));

const declaredRows = brainReaderRows.filter((row) => row.routeMode !== 'capability_probe');
const capabilityRows = brainReaderRows.filter((row) => row.routeMode === 'capability_probe');
const failures = declaredRows.filter(isReaderFailure);
const providerEligibleFailures = failures.filter((row) => row.providerMutationEligible);
const clientRuntimeFailures = [
  ...failures.filter((row) => !row.providerMutationEligible),
  ...runtimeSentinelObservations,
];
const declaredHealthy = declaredRows.filter((row) => !isReaderFailure(row));
const capabilityFailures = capabilityRows.filter(isReaderFailure);
const capabilityHealthy = capabilityRows.filter((row) => !isReaderFailure(row));

const declaredResultRows = brainResultRows.filter((row) => row.routeMode !== 'capability_probe');
const capabilityResultRows = brainResultRows.filter((row) => row.routeMode === 'capability_probe');
const enabledDeclaredResults = declaredResultRows.filter((row) => row.enabled);
const extractionFailures = enabledDeclaredResults.filter((row) => row.count === 0);
const extractionHealthy = enabledDeclaredResults.filter((row) => row.count > 0);
const ignoredDisabledExtractionFailures = declaredResultRows.filter((row) => !row.enabled && row.count === 0);
const systemicExtraction = classifySystemicExtraction(enabledDeclaredResults);
const systemicExtractionKeys = systemicExtraction.systemicExecutionKeys;
const systemicExtractionFailures = extractionFailures.filter((row) => systemicExtractionKeys.has(extractionExecutionKey(row)));
const providerExtractionFailures = extractionFailures.filter((row) => !systemicExtractionKeys.has(extractionExecutionKey(row)));

const readerPlans = evidence.complete ? providerEligibleFailures.map((row) => {
  const failureEvidence = {
    invoked: true,
    signature: row.signature,
    request: { mediaType: row.requestType },
    stages: {
      reader: {
        attempted: true,
        observed: true,
        state: row.state,
        failureClass: row.failureClass,
        failureStage: row.failureStage,
        httpStatus: row.httpStatus,
        errorCode: row.errorCode,
        errorClass: row.errorClass,
        durationSeconds: row.durationSeconds,
        loadBytes: row.loadBytes,
        loadDurationMs: row.loadDurationMs,
        mediaDataType: row.mediaDataType,
        trackType: row.trackType,
      },
    },
  };
  const plan = planRepair(failureEvidence, { signature: row.signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: row.index,
    state: row.state, failureClass: row.failureClass, failureDomain: row.failureDomain,
    providerMutationEligible: true, failureStage: row.failureStage,
    httpStatus: row.httpStatus, errorCode: row.errorCode, errorClass: row.errorClass,
    host: row.host, durationSeconds: row.durationSeconds,
    loadBytes: row.loadBytes, loadDurationMs: row.loadDurationMs,
    mediaDataType: row.mediaDataType, trackType: row.trackType,
    signature: row.signature, action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];

const extractionPlans = evidence.complete ? providerExtractionFailures.map((row) => {
  const signature = extractionSignature(row);
  const failureEvidence = {
    invoked: true,
    signature,
    request: { mediaType: row.requestType },
    stages: { media: { attempted: true, found: false } },
  };
  const plan = planRepair(failureEvidence, { signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: 'empty', failureClass: plan.failureClass, failureDomain: 'provider_extraction',
    providerMutationEligible: true, failureStage: 'media_extraction',
    httpStatus: 0, errorCode: '', errorClass: '', host: '', durationSeconds: null,
    loadBytes: 0, loadDurationMs: 0, mediaDataType: -1, trackType: -1, returnedCount: 0,
    signature, action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];
const systemicExtractionPlans = evidence.complete ? systemicExtractionFailures.map((row) => {
  const signature = `${row.requestType}:runtime_contract_drift:${String(row.client || 'unknown').toLowerCase()}:${row.fixture}`;
  const plan = planRepair({
    invoked: true,
    contractDrift: true,
    signature,
    request: { mediaType: row.requestType },
  }, { signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
    requestType: row.requestType, routeMode: row.routeMode, index: -1,
    state: 'empty', failureClass: 'runtime_contract_drift', failureDomain: 'client_runtime',
    providerMutationEligible: false, coreOrManifestProposalAllowed: true,
    failureStage: 'provider_runtime_compat', returnedCount: 0, signature,
    action: plan.action, exitReason: plan.exitReason,
    hypotheses: plan.hypotheses.map((hypothesis) => ({
      id: hypothesis.id,
      capabilities: [...(hypothesis.capabilities || [])],
      actions: [...(hypothesis.actions || [])],
    })),
  };
}) : [];
const plans = [...readerPlans, ...extractionPlans];

const providerLoadIssues = evidence.complete ? providerLoadObservations.map((row) => ({
  ...row,
  ...providerLoadRepair(row),
})) : [];

const playerHealthyByRoute = new Map();
for (const row of declaredHealthy) {
  const key = routeKey(row);
  if (!playerHealthyByRoute.has(key)) playerHealthyByRoute.set(key, new Set());
  playerHealthyByRoute.get(key).add(row.client);
}
const extractionHealthyByRoute = new Map();
for (const row of extractionHealthy) {
  const key = routeKey(row);
  if (!extractionHealthyByRoute.has(key)) extractionHealthyByRoute.set(key, new Set());
  extractionHealthyByRoute.get(key).add(row.client);
}
const consensusGrouped = new Map();
for (const plan of plans) {
  const key = `${plan.provider}\u0000${plan.requestType}\u0000${plan.fixture}\u0000${plan.failureClass}`;
  if (!consensusGrouped.has(key)) consensusGrouped.set(key, { plan, clients: new Set() });
  consensusGrouped.get(key).clients.add(plan.client);
}
const crossClientProviderFailures = [...consensusGrouped.values()].filter(({ plan, clients }) => {
  const key = routeKey(plan);
  const healthy = plan.failureClass === 'media_extraction_gap'
    ? extractionHealthyByRoute.get(key)
    : playerHealthyByRoute.get(key);
  return clients.size >= 2 && !(healthy?.size > 0);
});
const providerLearningAllowed = evidence.complete && crossClientProviderFailures.length > 0;

const grouped = new Map();
for (const plan of plans) {
  const key = `${plan.provider}\u0000${plan.requestType}\u0000${plan.failureClass}`;
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key).push(plan);
}
const priorities = [...grouped.values()]
  .map((rows) => ({
    provider: rows[0].provider,
    requestType: rows[0].requestType,
    failureClass: rows[0].failureClass,
    occurrences: rows.length,
    clients: [...new Set(rows.map((row) => row.client))].sort(),
    fixtures: [...new Set(rows.map((row) => row.fixture))].sort(),
    firstHypothesis: rows[0].hypotheses[0]?.id || null,
    signatures: [...new Set(rows.map((row) => row.signature))].slice(0, 12),
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.provider.localeCompare(b.provider));

const loadGrouped = new Map();
for (const issue of providerLoadIssues) {
  const key = `${issue.provider}\u0000${issue.failureClass}`;
  if (!loadGrouped.has(key)) loadGrouped.set(key, []);
  loadGrouped.get(key).push(issue);
}
const providerLoadPriorities = [...loadGrouped.values()]
  .map((rows) => ({
    provider: rows[0].provider,
    failureClass: rows[0].failureClass,
    layer: rows[0].layer,
    occurrences: rows.length,
    clients: [...new Set(rows.map((row) => row.client))].sort(),
    fixtures: [...new Set(rows.map((row) => row.fixture))].sort(),
    providerJsMutationAllowed: false,
    coreOrManifestProposalAllowed: evidence.complete,
    actions: rows[0].actions,
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.provider.localeCompare(b.provider));

const playerObservations = brainReaderRows.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: row.index,
  state: row.state, failureClass: row.failureClass, failureDomain: row.failureDomain,
  providerMutationEligible: row.providerMutationEligible, failureStage: row.failureStage,
  httpStatus: row.httpStatus, errorCode: row.errorCode, host: row.host,
  durationSeconds: row.durationSeconds, loadBytes: row.loadBytes, loadDurationMs: row.loadDurationMs,
  observationLayer: 'player',
}));
const extractionObservations = providerExtractionFailures.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: -1,
  state: 'empty', failureClass: 'media_extraction_gap', failureDomain: 'provider_extraction',
  providerMutationEligible: true, failureStage: 'media_extraction',
  httpStatus: 0, errorCode: '', host: '', durationSeconds: null, loadBytes: 0, loadDurationMs: 0,
  returnedCount: 0, observationLayer: 'extraction',
}));
const systemicExtractionObservations = systemicExtractionFailures.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, index: -1,
  state: 'empty', failureClass: 'runtime_contract_drift', failureDomain: 'client_runtime',
  providerMutationEligible: false, failureStage: 'provider_runtime_compat',
  httpStatus: 0, errorCode: '', host: '', durationSeconds: null, loadBytes: 0, loadDurationMs: 0,
  returnedCount: 0, observationLayer: 'runtime',
}));
const extractionHealthyObservations = extractionHealthy.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, routeMode: row.routeMode, returnedCount: row.count,
  observationLayer: 'extraction', state: 'non_empty', failureClass: 'healthy',
}));
const observations = [...playerObservations, ...extractionObservations, ...systemicExtractionObservations, ...runtimeSentinelObservations];
const providerMap = new Map();
function ensureProviderOutcome(provider) {
  const key = String(provider || '').toLowerCase();
  if (!providerMap.has(key)) {
    providerMap.set(key, {
      provider: key, observed: 0, healthy: 0, failures: 0,
      providerEligibleFailures: 0, clientRuntimeFailures: 0,
      extractionExecutions: 0, extractionHealthy: 0, extractionFailures: 0,
      capabilityProbes: 0, capabilityHealthy: 0, capabilityFailures: 0,
      loadFailures: 0, loadFailureClasses: {},
      failureClasses: {}, clients: new Set(), fixtures: new Set(), requestTypes: new Set(),
    });
  }
  return providerMap.get(key);
}
for (const row of playerObservations) {
  const current = ensureProviderOutcome(row.provider);
  current.observed += 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
  if (row.routeMode === 'capability_probe') {
    current.capabilityProbes += 1;
    if (row.failureClass === 'healthy') current.capabilityHealthy += 1;
    else current.capabilityFailures += 1;
  } else if (row.failureClass === 'healthy') {
    current.healthy += 1;
  } else {
    current.failures += 1;
    if (row.providerMutationEligible) current.providerEligibleFailures += 1;
    else current.clientRuntimeFailures += 1;
    current.failureClasses[row.failureClass] = Number(current.failureClasses[row.failureClass] || 0) + 1;
  }
}
for (const row of enabledDeclaredResults) {
  const current = ensureProviderOutcome(row.provider);
  current.extractionExecutions += 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
  if (row.count > 0) current.extractionHealthy += 1;
  else {
    current.extractionFailures += 1;
    current.failures += 1;
    if (systemicExtractionKeys.has(extractionExecutionKey(row))) {
      current.clientRuntimeFailures += 1;
      current.failureClasses.runtime_contract_drift = Number(current.failureClasses.runtime_contract_drift || 0) + 1;
    } else {
      current.providerEligibleFailures += 1;
      current.failureClasses.media_extraction_gap = Number(current.failureClasses.media_extraction_gap || 0) + 1;
    }
  }
}
for (const row of runtimeSentinelObservations) {
  const current = ensureProviderOutcome(row.provider);
  current.observed += 1;
  current.failures += 1;
  current.clientRuntimeFailures += 1;
  current.failureClasses.client_runtime_error = Number(current.failureClasses.client_runtime_error || 0) + 1;
  current.clients.add(row.client);
  current.fixtures.add(row.fixture);
  current.requestTypes.add(row.requestType);
}
for (const issue of providerLoadIssues) {
  const current = ensureProviderOutcome(issue.provider);
  current.loadFailures += 1;
  current.loadFailureClasses[issue.failureClass] = Number(current.loadFailureClasses[issue.failureClass] || 0) + 1;
  current.clients.add(issue.client);
  current.fixtures.add(issue.fixture);
}
const providerOutcomes = [...providerMap.values()].map((row) => ({
  provider: row.provider,
  observed: row.observed,
  healthy: row.healthy,
  failures: row.failures,
  providerEligibleFailures: row.providerEligibleFailures,
  clientRuntimeFailures: row.clientRuntimeFailures,
  extractionExecutions: row.extractionExecutions,
  extractionHealthy: row.extractionHealthy,
  extractionFailures: row.extractionFailures,
  capabilityProbes: row.capabilityProbes,
  capabilityHealthy: row.capabilityHealthy,
  capabilityFailures: row.capabilityFailures,
  loadFailures: row.loadFailures,
  loadFailureClasses: row.loadFailureClasses,
  failureClasses: row.failureClasses,
  clients: [...row.clients].sort(),
  fixtures: [...row.fixtures].sort(),
  requestTypes: [...row.requestTypes].sort(),
})).sort((a, b) => b.loadFailures - a.loadFailures || b.failures - a.failures || a.provider.localeCompare(b.provider));

const capabilityProbes = capabilityRows.map((row) => ({
  provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture,
  requestType: row.requestType, index: row.index,
  state: row.state, healthy: !isReaderFailure(row), failureClass: row.failureClass,
  failureDomain: row.failureDomain, providerMutationEligible: false,
  failureStage: row.failureStage, httpStatus: row.httpStatus,
  durationSeconds: row.durationSeconds,
  promotionEligibleFromReaderAlone: false,
}));

const payload = {
  schemaVersion: 5,
  generatedAt: new Date().toISOString(),
  brainVersion: BRAIN_CONTROL_PLANE_VERSION,
  evidenceComplete: evidence.complete,
  evidenceProblems: evidence.problems,
  evidenceStats: evidence.stats,
  readerObserved: readerRows.length,
  runtimeErrorSentinelObserved: runtimeSentinelObservations.length,
  runtimeErrorSentinelReaderRowsExcluded: runtimeSentinelReaderRows.length,
  readerDeclaredObserved: declaredRows.length,
  readerHealthy: declaredHealthy.length,
  readerFailures: failures.length,
  providerEligibleReaderFailures: providerEligibleFailures.length,
  clientRuntimeReaderFailures: clientRuntimeFailures.length,
  extractionResultObserved: enabledDeclaredResults.length,
  extractionHealthy: extractionHealthy.length,
  extractionFailures: extractionFailures.length,
  providerExtractionFailures: providerExtractionFailures.length,
  clientRuntimeExtractionFailures: systemicExtractionFailures.length,
  systemicExtractionGroups: systemicExtraction.systemicGroups.length,
  ignoredDisabledExtractionFailures: ignoredDisabledExtractionFailures.length,
  capabilityResultObserved: capabilityResultRows.length,
  crossClientProviderFailureGroups: crossClientProviderFailures.length,
  capabilityProbeObserved: capabilityRows.length,
  capabilityProbeHealthy: capabilityHealthy.length,
  capabilityProbeFailures: capabilityFailures.length,
  providerLoadObservedFailures: providerLoadObservations.length,
  providerLoadActionableFailures: providerLoadIssues.length,
  readerLoadErrorEvidence: brainReaderRows.filter((row) => row.loadDurationMs > 0 || row.loadBytes > 0 || row.httpStatus > 0).length,
  observations,
  extractionHealthyObservations,
  systemicExtractionGroups: systemicExtraction.systemicGroups,
  clientRuntimeExtractionPlans: systemicExtractionPlans,
  providerLoadObservations,
  providerLoadIssues,
  providerOutcomes,
  capabilityProbes,
  plans,
  priorities,
  providerLoadPriorities,
  policy: {
    evidenceUsable: evidence.complete,
    learningAllowed: providerLearningAllowed,
    providerLearningAllowed,
    repairPlanningAllowed: providerLearningAllowed,
    providerMutationRequiresCrossClientConsensus: true,
    clientRuntimeFailureLearningAllowed: false,
    clientRuntimeExtractionLearningAllowed: false,
    coreRuntimeCompatibilityProposalAllowed: evidence.complete && systemicExtractionFailures.length > 0,
    runtimeErrorSentinelLearningAllowed: false,
    repositoryLearningAllowed: evidence.complete && providerLoadIssues.length > 0,
    providerLoadJsMutationAllowed: false,
    coreOrManifestLoadProposalAllowed: evidence.complete && providerLoadIssues.length > 0,
    capabilityLearningAllowed: false,
    capabilityPromotionRequiresIdentityProof: true,
    disabledProviderExtractionLearningAllowed: false,
    productionWritesAllowed: false,
    publicationAllowed: false,
    requireFreshNativeReaderProofAfterRepair: true,
    nonblockingSmoke,
  },
  privacy: 'No raw URLs, query tokens, cookie values, authorization values or response-header values are persisted.',
};
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2) + '\n');
console.log(
  `FIELD_NATIVE_READER_BRAIN evidence_complete=${payload.evidenceComplete} observed=${payload.readerObserved} ` +
  `declared=${payload.readerDeclaredObserved} healthy=${payload.readerHealthy} failures=${payload.readerFailures} ` +
  `provider_eligible_failures=${payload.providerEligibleReaderFailures} extraction_failures=${payload.extractionFailures} ` +
  `provider_extraction_failures=${payload.providerExtractionFailures} systemic_extraction_failures=${payload.clientRuntimeExtractionFailures} ` +
  `client_runtime_failures=${payload.clientRuntimeReaderFailures} runtime_sentinels=${payload.runtimeErrorSentinelObserved} ` +
  `cross_client_provider_groups=${payload.crossClientProviderFailureGroups} ` +
  `provider_load_failures=${payload.providerLoadActionableFailures} capability_probes=${payload.capabilityProbeObserved} ` +
  `capability_probe_healthy=${payload.capabilityProbeHealthy} capability_probe_failures=${payload.capabilityProbeFailures} ` +
  `priorities=${priorities.length} provider_load_priorities=${providerLoadPriorities.length} provider_outcomes=${providerOutcomes.length} ` +
  `nonblocking_smoke=${nonblockingSmoke}`
);
if (!evidence.complete) {
  for (const problem of evidence.problems.slice(0, 80)) console.log(`FIELD_NATIVE_READER_BRAIN_EVIDENCE_INCOMPLETE ${problem}`);
}
for (const priority of providerLoadPriorities.slice(0, 40)) console.log(`FIELD_NATIVE_READER_BRAIN_LOAD_PRIORITY ${JSON.stringify(priority)}`);
for (const priority of priorities.slice(0, 40)) console.log(`FIELD_NATIVE_READER_BRAIN_PRIORITY ${JSON.stringify(priority)}`);
if (!evidence.complete && !nonblockingSmoke) process.exitCode = 2;