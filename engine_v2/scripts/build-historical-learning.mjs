#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const args = process.argv.slice(2);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const baselineConfig = readJson(resolveArg('--baseline-config', path.join(root, 'engine_v2/config/historical-audit-baselines.json')), {});
const baselineId = arg('--baseline-id') || baselineConfig.baselines?.[0]?.id;
const baseline = (baselineConfig.baselines || []).find((row) => row?.id === baselineId);
if (!baseline) throw new Error(`historical baseline not found: ${baselineId || '<none>'}`);

const baselineManifest = readJson(required('--baseline-manifest'), {});
const baselineHealth = readJson(required('--baseline-health'), {});
const currentManifest = readJson(resolveArg('--current-manifest', path.join(root, 'manifest.json')), {});
const currentHealth = readJson(required('--current-health'), {});
const repairReport = readJson(required('--repair-report'), {});
const output = resolveArg('--output', path.join(root, 'brain-learning-output/historical-training.json'));

const bManifest = manifestMap(baselineManifest);
const cManifest = manifestMap(currentManifest);
const bHealth = healthMap(baselineHealth);
const cHealth = healthMap(currentHealth);
const repair = repairMap(repairReport);
const quarantine = new Set(strings(baseline.quarantines).map(norm));
const recoveredReference = new Set(strings(baseline.recoveredProviders).map(norm));
const disabledReference = new Set(strings(baseline.disabledNonQuarantine).map(norm));
const ids = new Set([
  ...bManifest.keys(), ...cManifest.keys(), ...bHealth.keys(), ...cHealth.keys(), ...repair.keys(),
  ...quarantine, ...recoveredReference, ...disabledReference,
]);

const cases = [...ids].filter(Boolean).sort().map((providerId) => {
  const bm = bManifest.get(providerId) || emptyManifest(providerId);
  const cm = cManifest.get(providerId) || emptyManifest(providerId);
  const bh = bHealth.get(providerId) || emptyHealth(providerId);
  const ch = cHealth.get(providerId) || emptyHealth(providerId);
  const rp = repair.get(providerId) || emptyRepair(providerId);
  const baselineHealthy = healthy(bh);
  const currentHealthy = healthy(ch) || rp.accepted > 0 || rp.bestStreamsAfter > 0;
  const quarantineReference = quarantine.has(providerId);
  const recoveredAtBaseline = recoveredReference.has(providerId);
  const disabledNonQuarantineAtBaseline = disabledReference.has(providerId);
  const delta = classify({
    quarantineReference,
    recoveredAtBaseline,
    baselineHealthy,
    currentHealthy,
    baselineEnabled: bm.enabled,
    currentEnabled: cm.enabled,
    repair: rp,
  });
  const priority = priorityFor(delta);
  const trainingRole = roleFor(delta);
  return {
    providerId,
    delta,
    priority,
    trainingRole,
    historicalWeight: { critical: 100, high: 80, medium: 50, low: 10 }[priority] || 10,
    excelReference: {
      sourceRelease: baseline.release || null,
      finalResultAtBaseline: excelFinalResult({ quarantineReference, recoveredAtBaseline, disabledNonQuarantineAtBaseline, manifest: bm, health: bh }),
      recoveredAtBaseline,
      quarantineAtBaseline: quarantineReference,
      disabledNonQuarantineAtBaseline,
      activeAtBaseline: bm.enabled,
      diagnosticStatusAtBaseline: bh.status,
      streamsReturnedAtBaseline: bh.streamsReturned,
      streamsPlayableAtBaseline: bh.streamsPlayable,
      scoreAtBaseline: bh.score,
      failureClassesAtBaseline: bh.failureClasses,
    },
    baseline: {
      enabled: bm.enabled,
      version: bm.version,
      status: bh.status,
      streamsReturned: bh.streamsReturned,
      streamsPlayable: bh.streamsPlayable,
      score: bh.score,
      failureClasses: bh.failureClasses,
    },
    current: {
      enabled: cm.enabled,
      version: cm.version,
      status: ch.status,
      streamsReturned: ch.streamsReturned,
      streamsPlayable: ch.streamsPlayable,
      score: ch.score,
      failureClasses: ch.failureClasses,
    },
    sandboxRepair: rp,
  };
});

const counts = {};
for (const row of cases) counts[row.delta] = (counts[row.delta] || 0) + 1;
const payload = {
  schemaVersion: 2,
  generatedAt: new Date().toISOString(),
  baseline: {
    id: baseline.id,
    source: baseline.source,
    release: baseline.release,
    commit: baseline.commit,
    comparedCommit: baseline.comparedCommit || null,
    expectedProviderCount: Number(baseline.providers || 0),
    spreadsheetSnapshot: obj(baseline.spreadsheetSnapshot),
  },
  stats: {
    providers: cases.length,
    deltas: counts,
    unresolvedHighPriority: cases.filter((row) => ['critical', 'high'].includes(row.priority) && row.trainingRole === 'unresolved').length,
    positiveExamples: cases.filter((row) => row.trainingRole === 'positive').length,
    safetyReferences: cases.filter((row) => row.trainingRole === 'safety').length,
    recoveredReferenceRegressions: cases.filter((row) => row.delta === 'recovered_reference_regressed').length,
    recoveredReferenceConfirmed: cases.filter((row) => row.delta === 'recovered_reference_confirmed').length,
  },
  cases,
  privacy: 'Initial bootstrap retains structured spreadsheet classifications and aggregate counters plus coarse provider evidence from the audited Git snapshot; no raw URLs, tokens, cookies or headers are persisted.',
};
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(payload, null, 2) + '\n');
console.log(`FIELD_BRAIN_HISTORICAL providers=${payload.stats.providers} unresolved_high=${payload.stats.unresolvedHighPriority} positive=${payload.stats.positiveExamples} safety=${payload.stats.safetyReferences} recovered_regressed=${payload.stats.recoveredReferenceRegressions}`);

function manifestMap(data) {
  const map = new Map();
  for (const row of Array.isArray(data.scrapers) ? data.scrapers : []) {
    if (!row || typeof row !== 'object') continue;
    const id = norm(row.id ?? row.providerId ?? row.name);
    if (!id) continue;
    map.set(id, { id, enabled: row.enabled === true, version: scalar(row.version) });
  }
  return map;
}

function healthMap(data) {
  const rows = Array.isArray(data.providers) ? data.providers : (Array.isArray(data.results) ? data.results : []);
  const map = new Map();
  for (const row of rows) {
    if (!row || typeof row !== 'object') continue;
    const id = norm(row.id ?? row.provider_id ?? row.providerId ?? row.canonical_id ?? providerFromKey(row.key));
    if (!id) continue;
    const tests = Array.isArray(row.tests) ? row.tests : [];
    const evidence = obj(row.evidence);
    const streamsReturned = Math.max(
      num(row.streams), num(row.streams_returned), num(row.stream_count), num(evidence.streams_returned),
      ...tests.map((test) => Math.max(num(test?.stream_count), num(test?.streams_returned))),
    );
    const streamsPlayable = Math.max(
      num(row.streams_playable), num(row.playable_streams), num(evidence.streams_playable),
      ...tests.map((test) => num(test?.streams_playable)),
    );
    const failureClasses = [...new Set([
      ...strings(row.failure_classes ?? row.failureClasses),
      ...tests.map((test) => scalar(test?.failure_class)).filter(Boolean),
    ])].sort();
    const summary = {
      id,
      status: scalar(row.status ?? row.diagnostic_status ?? row.best_status ?? 'unknown'),
      score: num(row.score ?? row.max_score),
      streamsReturned,
      streamsPlayable,
      failureClasses,
    };
    const current = map.get(id);
    if (!current || healthQuality(summary) > healthQuality(current)) map.set(id, summary);
  }
  return map;
}

function repairMap(report) {
  const map = new Map();
  const plans = obj(report.brain?.plans);
  const ensure = (parentKey) => {
    const plan = obj(plans[parentKey]);
    const id = norm(plan.providerId || providerFromKey(parentKey));
    if (!id) return null;
    if (!map.has(id)) map.set(id, emptyRepair(id));
    const row = map.get(id);
    if (plan.failureClass) row.failureClasses = [...new Set([...row.failureClasses, String(plan.failureClass)])].sort();
    if (plan.signature) row.signatures = [...new Set([...row.signatures, String(plan.signature)])].sort();
    return row;
  };
  for (const round of Array.isArray(report.rounds) ? report.rounds : []) {
    for (const attempt of Array.isArray(round?.attempts) ? round.attempts : []) {
      if (!attempt || typeof attempt !== 'object') continue;
      const row = ensure(String(attempt.parent_key || ''));
      if (!row) continue;
      row.attempts += 1;
      if (attempt.profile) row.profilesAttempted = [...new Set([...row.profilesAttempted, String(attempt.profile)])].sort();
      row.bestStreamsBefore = Math.max(row.bestStreamsBefore, num(attempt.baseline_streams_playable), num(attempt.baseline_streams_returned));
    }
    for (const accepted of Array.isArray(round?.accepted) ? round.accepted : []) {
      const row = ensure(String(accepted?.parent_key || ''));
      if (!row) continue;
      row.accepted += 1;
      if (accepted?.profile) row.acceptedProfiles = [...new Set([...row.acceptedProfiles, String(accepted.profile)])].sort();
      row.bestStreamsAfter = Math.max(row.bestStreamsAfter, num(accepted?.streams_playable), num(accepted?.streams_returned));
    }
    for (const rejected of Array.isArray(round?.rejected) ? round.rejected : []) {
      const row = ensure(String(rejected?.parent_key || ''));
      if (!row) continue;
      row.rejected += 1;
      if (rejected?.profile) row.rejectedProfiles = [...new Set([...row.rejectedProfiles, String(rejected.profile)])].sort();
      if (rejected?.reason) row.rejectionReasons = [...new Set([...row.rejectionReasons, sanitize(rejected.reason)])].filter(Boolean).sort();
      row.bestStreamsAfter = Math.max(row.bestStreamsAfter, num(rejected?.streams_playable), num(rejected?.streams_returned));
    }
  }
  return map;
}

function classify({ quarantineReference, recoveredAtBaseline, baselineHealthy, currentHealthy, baselineEnabled, currentEnabled, repair }) {
  if (quarantineReference && currentEnabled && currentHealthy) return 'safety_recovered_with_new_proof';
  if (quarantineReference && currentEnabled && !currentHealthy) return 'safety_regression';
  if (quarantineReference) return 'safety_quarantine_reference';
  if (recoveredAtBaseline && !currentHealthy) return 'recovered_reference_regressed';
  if (recoveredAtBaseline && currentHealthy) return 'recovered_reference_confirmed';
  if (baselineHealthy && !currentHealthy) return 'regressed';
  if (!baselineHealthy && currentHealthy) return 'recovered';
  if (currentHealthy) return 'stable_healthy';
  if (repair.attempts > 0 && repair.accepted === 0) return currentEnabled ? 'persistent_unresolved' : 'disabled_unresolved';
  if (baselineEnabled && !currentEnabled) return 'disabled_without_fresh_proof';
  return 'unresolved_no_fresh_proof';
}

function priorityFor(delta) {
  if (['safety_regression', 'regressed', 'recovered_reference_regressed'].includes(delta)) return 'critical';
  if (['persistent_unresolved', 'disabled_without_fresh_proof', 'disabled_unresolved'].includes(delta)) return 'high';
  if (['recovered', 'safety_recovered_with_new_proof', 'unresolved_no_fresh_proof'].includes(delta)) return 'medium';
  return 'low';
}

function roleFor(delta) {
  if (delta.startsWith('safety_') && delta !== 'safety_recovered_with_new_proof') return 'safety';
  if (['recovered', 'stable_healthy', 'safety_recovered_with_new_proof', 'recovered_reference_confirmed'].includes(delta)) return 'positive';
  return 'unresolved';
}

function excelFinalResult({ quarantineReference, recoveredAtBaseline, disabledNonQuarantineAtBaseline, manifest, health }) {
  if (quarantineReference) return 'QUARANTAINE';
  if (recoveredAtBaseline) return 'RÉCUPÉRÉ / ACTIF';
  if (disabledNonQuarantineAtBaseline || !manifest.enabled) return 'DÉSACTIVÉ';
  if (healthy(health)) return 'ACTIF / FLUX OBSERVÉ';
  return 'ACTIF À INVESTIGUER';
}

function healthy(row) {
  return row.streamsPlayable > 0 || String(row.status).toLowerCase() === 'healthy';
}
function healthQuality(row) {
  return (row.streamsPlayable > 0 ? 1_000_000 : 0) + statusRank(row.status) * 10_000 + row.score * 100 + row.streamsReturned;
}
function statusRank(status) {
  return ({ healthy: 9, degraded: 7, reachable: 6, no_streams: 5, blocked: 4, unavailable: 3, provider_unreachable: 2, runtime_error: 1, excluded: 0 })[String(status || '').toLowerCase()] || 0;
}
function emptyManifest(id) { return { id, enabled: false, version: null }; }
function emptyHealth(id) { return { id, status: 'unknown', score: 0, streamsReturned: 0, streamsPlayable: 0, failureClasses: [] }; }
function emptyRepair(id) {
  return { id, attempts: 0, accepted: 0, rejected: 0, failureClasses: [], signatures: [], profilesAttempted: [], acceptedProfiles: [], rejectedProfiles: [], rejectionReasons: [], bestStreamsBefore: 0, bestStreamsAfter: 0 };
}
function providerFromKey(value) {
  const raw = String(value || '').split('::', 1)[0];
  const parts = raw.split(':');
  return parts.length > 1 ? parts.slice(1).join(':') : raw;
}
function norm(value) { return String(value ?? '').trim().toLowerCase(); }
function scalar(value) { return value == null || value === '' ? null : String(value); }
function strings(value) { return Array.isArray(value) ? value.map((item) => String(item ?? '')).filter(Boolean) : (value == null || value === '' ? [] : [String(value)]); }
function num(value) { const n = Number(value); return Number.isFinite(n) ? Math.max(0, n) : 0; }
function obj(value) { return value && typeof value === 'object' && !Array.isArray(value) ? value : {}; }
function sanitize(value) { return String(value ?? '').replace(/https?:\/\/\S+/gi, '<url>').replace(/\s+/g, ' ').trim().slice(0, 240); }
function arg(name) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; }
function required(name) { const value = arg(name); if (!value) throw new Error(`missing ${name}`); return path.resolve(value); }
function resolveArg(name, fallback) { return path.resolve(arg(name) || fallback); }
function readJson(file, fallback) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } }
