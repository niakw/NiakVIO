#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { REPAIR_RECIPES } from '../src/repair-brain.mjs';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const args = process.argv.slice(2);
const outputDir = resolveArg('--output-dir', path.join(root, 'engine_v2/learning'));
const repairPath = resolveArg('--repair-report', path.join(root, 'repair-report.json'));
const historicalPath = optionalArg('--historical-training');
const previousPath = optionalArg('--previous-state');
const nativeSummaryPath = optionalArg('--native-summary');
const portfolioPath = optionalArg('--provider-portfolio');
const overridesPath = resolveArg('--overrides', path.join(root, 'provider-overrides.json'));
fs.mkdirSync(outputDir, { recursive: true });

const overrides = readJson(overridesPath, {});
const repair = readJson(repairPath, {});
const diagnostics = readJson(path.join(root, 'diagnostics-report.json'), {});
const policy = readJson(path.join(root, 'engine_v2/config/brain-policy.json'), {});
const previous = previousPath ? readJson(previousPath, {}) : {};
const historical = historicalPath ? readJson(historicalPath, {}) : {};
const nativeSummary = nativeSummaryPath ? readJson(nativeSummaryPath, {}) : {};
const portfolio = portfolioPath ? readJson(portfolioPath, {}) : {};
const skills = overrides.runtime_repair?.learned_skills ?? {};
const plans = repair.brain?.plans ?? {};
const maxMemory = Number(policy.learningLab?.memoryMaxEntries || 1000);
const repeatedThreshold = Number(policy.learningLab?.maxRepeatedFailedProfile || 2);

const counts = new Map();
for (const row of Object.values(plans)) {
  const failureClass = String(row?.failureClass ?? 'unknown_failure');
  if (failureClass === 'healthy') continue;
  counts.set(failureClass, (counts.get(failureClass) ?? 0) + 1);
}
const trustedByFailure = new Map();
for (const skill of Object.values(skills)) {
  if (!skill || skill.autoApply !== true) continue;
  const key = String(skill.failureClass ?? skill.failure_class ?? 'unknown_failure');
  trustedByFailure.set(key, (trustedByFailure.get(key) ?? 0) + 1);
}

const experimentMemory = mergeExperimentMemory(previous.experimentMemory, repair, plans, maxMemory);
const proposals = [];
for (const [failureClass, count] of [...counts.entries()].sort((a, b) => b[1] - a[1])) {
  const recipes = REPAIR_RECIPES[failureClass] ?? REPAIR_RECIPES.unknown_failure;
  if (count >= 2 && (trustedByFailure.get(failureClass) ?? 0) === 0) {
    proposals.push({
      type: 'skill_candidate', priority: count >= 5 ? 'high' : 'medium', failureClass, evidenceCount: count,
      proposedSkill: {
        id: `learning-${failureClass}`,
        compose: recipes.map((row) => row.id).slice(0, 3),
        capabilities: [...new Set(recipes.flatMap((row) => row.capabilities ?? []))],
        execution: 'sandbox_only_until_cross-provider-proof',
      },
      reason: 'Repeated unresolved failure class without a trusted reusable skill.',
    });
  }
}

for (const row of experimentMemory.entries.filter((entry) => entry.successes === 0 && entry.consecutiveFailures >= repeatedThreshold).slice(0, 80)) {
  proposals.push({
    type: 'avoid_failed_profile',
    priority: row.consecutiveFailures >= repeatedThreshold + 1 ? 'high' : 'medium',
    providerId: row.providerId,
    failureClass: row.failureClass,
    profile: row.profile,
    signature: row.signature,
    evidenceCount: row.failures,
    reason: `The same sandbox profile failed ${row.consecutiveFailures} consecutive time(s) for this provider/signature. Collect different evidence or use another repair hypothesis before retrying it.`,
  });
}

const historicalTargets = (historical.cases || [])
  .filter((item) => item && item.trainingRole === 'unresolved' && ['critical', 'high'].includes(item.priority))
  .sort((a, b) => priorityScore(b.priority) - priorityScore(a.priority) || String(a.providerId).localeCompare(String(b.providerId)))
  .slice(0, 160)
  .map((row) => ({ providerId: String(row.providerId || '').toLowerCase(), priority: row.priority, delta: row.delta }));
for (const target of historicalTargets.slice(0, 80)) {
  const source = (historical.cases || []).find((row) => String(row?.providerId || '').toLowerCase() === target.providerId) || {};
  proposals.push({
    type: 'historical_provider_repair_target', priority: target.priority, providerId: target.providerId,
    historicalDelta: target.delta,
    failureClasses: source.sandboxRepair?.failureClasses ?? source.current?.failureClasses ?? [],
    attemptedProfiles: source.sandboxRepair?.profilesAttempted ?? [],
    reason: target.delta === 'regressed'
      ? 'Provider had stronger evidence in the 5.20.63 audit baseline and is now a regression target.'
      : 'Provider remains unresolved after current sandbox diagnosis/repair attempts.',
  });
}

const nativeRepairTargets = (portfolio.providers || [])
  .filter((item) => item && item.recommendation === 'repair_runtime_or_transport')
  .sort((a, b) => Number(b.score || 0) - Number(a.score || 0))
  .map((row) => String(row.provider || '').toLowerCase()).filter(Boolean).slice(0, 200);
for (const row of (portfolio.providers || [])
  .filter((item) => item && ['repair_runtime_or_transport', 'quarantine_unsafe'].includes(item.recommendation))
  .sort((a, b) => Number(b.score || 0) - Number(a.score || 0)).slice(0, 80)) {
  proposals.push({
    type: row.recommendation === 'quarantine_unsafe' ? 'native_safety_target' : 'native_cross_device_repair_target',
    priority: row.recommendation === 'quarantine_unsafe' ? 'critical' : 'high',
    providerId: String(row.provider || '').toLowerCase(),
    runtimeErrors: Number(row.runtimeErrors || 0), transportFailures: Number(row.transportFailures || 0),
    identityContradictions: Number(row.identityContradictions || 0), catalogueCoverageRate: Number(row.catalogueCoverageRate || 0),
    reason: row.recommendation === 'quarantine_unsafe'
      ? 'Official native-client corpus observed an identity contradiction; keep safety gating until new proof exists.'
      : 'Official native-client corpus observed a runtime/transport defect that should feed the next sandbox repair cycle.',
  });
}

// Reader evidence has precedence over generic transport labels because it is the
// closest observation to what a human sees after pressing Play on the real OS.
const readerSignals = Array.isArray(nativeSummary.readerFailureSignals) ? nativeSummary.readerFailureSignals : [];
for (const row of readerSignals.slice(0, 80)) {
  const failureClass = String(row?.failureClass || 'unknown_failure');
  const recipes = REPAIR_RECIPES[failureClass] ?? REPAIR_RECIPES.unknown_failure;
  proposals.push({
    type: 'native_reader_failure_class',
    priority: Number(row?.occurrences || 0) >= 5 ? 'critical' : 'high',
    failureClass,
    evidenceCount: Number(row?.occurrences || 0),
    providers: Array.isArray(row?.providers) ? row.providers.slice(0, 24) : [],
    clients: Array.isArray(row?.clients) ? row.clients.slice(0, 8) : [],
    proposedSkill: {
      id: `native-reader-${failureClass}`,
      compose: recipes.map((recipe) => recipe.id).slice(0, 3),
      capabilities: [...new Set(recipes.flatMap((recipe) => recipe.capabilities ?? []))],
      execution: 'targeted_native_reader_then_sandbox',
    },
    reason: `Official native readers observed ${Number(row?.occurrences || 0)} ${failureClass} failure(s). Prefer reader-causal repair before generic provider mutation.`,
  });
}

const providerReaderFailures = Array.isArray(nativeSummary.providerReaderFailures) ? nativeSummary.providerReaderFailures : [];
for (const row of providerReaderFailures.slice(0, 120)) {
  const classes = isRecord(row?.failureClasses) ? row.failureClasses : {};
  const dominant = Object.entries(classes).sort((a, b) => Number(b[1]) - Number(a[1]))[0]?.[0] || 'unknown_failure';
  proposals.push({
    type: 'native_reader_provider_target',
    priority: dominant === 'short_media' || dominant === 'playback_http_access' ? 'critical' : 'high',
    providerId: String(row?.provider || '').toLowerCase(),
    failureClass: dominant,
    evidenceCount: Number(row?.occurrences || 0),
    readerFailureClasses: classes,
    clients: Array.isArray(row?.clients) ? row.clients.slice(0, 8) : [],
    fixtures: Array.isArray(row?.fixtures) ? row.fixtures.slice(0, 16) : [],
    reason: `Native player failure for this provider is causally classified as ${dominant}; retest the same provider/fixture/reader before broad repair.`,
  });
}

const repeatedReaderFailures = Array.isArray(nativeSummary.engineSignals?.repeatedReaderFailures)
  ? nativeSummary.engineSignals.repeatedReaderFailures : [];
for (const row of repeatedReaderFailures.slice(0, 80)) {
  proposals.push({
    type: 'native_reader_repeated_signature', priority: 'critical',
    providerId: String(row?.provider || '').toLowerCase(), failureClass: String(row?.failureClass || 'unknown_failure'),
    evidenceCount: Number(row?.occurrences || 0),
    reason: 'The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.',
  });
}

const unknown = counts.get('unknown_failure') ?? 0;
if (unknown >= 3) proposals.push({
  type: 'instrumentation_proposal', priority: 'high', target: 'evidence pipeline',
  reason: `${unknown} unresolved observations still lack a causal stage classification.`,
  proposal: 'Add stage evidence before adding another repair mutation; never use a generic provider fallback as diagnosis.',
});
const drift = counts.get('runtime_contract_drift') ?? 0;
if (drift > 0) proposals.push({
  type: 'core_proposal', priority: 'high', target: 'runtime contract adapter',
  reason: `${drift} runtime-contract drift observation(s).`,
  proposal: 'Re-audit official Nuvio device contracts and propose a core adapter change; production core remains immutable until reviewed.',
});

const payload = {
  schemaVersion: 3,
  generatedAt: new Date().toISOString(),
  brain: policy.identity ?? { name: 'NiakVIO Brain' },
  mode: 'learning_lab',
  publicationAllowed: false,
  productionWritesAllowed: false,
  sandboxExecutedProviders: true,
  proposals: dedupeProposals(proposals),
  learnedSkillCount: Object.keys(skills).length,
  unresolvedFailureCounts: Object.fromEntries(counts),
  diagnosticsAvailable: Boolean(Object.keys(diagnostics).length),
  experimentMemory,
  historicalTraining: { baseline: historical.baseline ?? null, stats: historical.stats ?? {}, targets: historicalTargets },
  nativeFeedback: {
    providersObserved: Number(nativeSummary.providersObserved || portfolio.observedProviders || 0),
    executions: Number(nativeSummary.executions || 0),
    contradictions: Number(nativeSummary.contradictions || 0),
    transportFailures: Number(nativeSummary.transportFailures || 0),
    nativeReaderObserved: Number(nativeSummary.nativeReaderObserved || 0),
    nativeReaderFailures: Number(nativeSummary.nativeReaderFailures || 0),
    readerFailureClasses: isRecord(nativeSummary.readerFailureClasses) ? nativeSummary.readerFailureClasses : {},
    runtimeErrors: Number(nativeSummary.runtimeErrors || 0),
    repairPriorityProviders: [...new Set([
      ...nativeRepairTargets,
      ...providerReaderFailures.map((row) => String(row?.provider || '').toLowerCase()).filter(Boolean),
    ])].slice(0, 240),
  },
  privacy: 'No raw URLs, tokens, header values, cookies, private notes or spreadsheet text are copied into persistent Brain learning state.',
};

fs.writeFileSync(path.join(outputDir, 'latest.json'), JSON.stringify(payload, null, 2) + '\n');
fs.writeFileSync(path.join(outputDir, 'latest.md'), renderMarkdown(payload));
console.log(`FIELD_BRAIN_LEARNING proposals=${payload.proposals.length} skills=${payload.learnedSkillCount} memory=${payload.experimentMemory.entries.length} historical_high=${Number(payload.historicalTraining.stats?.unresolvedHighPriority || 0)} native_repair=${payload.nativeFeedback.repairPriorityProviders.length} reader_failures=${payload.nativeFeedback.nativeReaderFailures}`);

function mergeExperimentMemory(previousMemory, report, planMap, limit) {
  const map = new Map();
  const previousEntries = Array.isArray(previousMemory?.entries) ? previousMemory.entries : [];
  for (const raw of previousEntries) {
    const row = sanitizeMemoryEntry(raw);
    if (row) map.set(memoryKey(row), row);
  }
  for (const round of Array.isArray(report.rounds) ? report.rounds : []) {
    const acceptedByRepair = new Map((round?.accepted || []).filter(isRecord).map((row) => [String(row.repair_key || ''), row]));
    const rejectedByRepair = new Map((round?.rejected || []).filter(isRecord).map((row) => [String(row.repair_key || ''), row]));
    for (const attempt of Array.isArray(round?.attempts) ? round.attempts : []) {
      if (!isRecord(attempt) || String(attempt.status || '') !== 'generated') continue;
      const parentKey = String(attempt.parent_key || '');
      const plan = isRecord(planMap[parentKey]) ? planMap[parentKey] : {};
      const providerId = String(plan.providerId || providerFromKey(parentKey)).toLowerCase();
      const profile = String(attempt.profile || '');
      const signature = String(plan.signature || plan.failureClass || 'unknown_failure');
      if (!providerId || !profile || !signature) continue;
      const key = memoryKey({ providerId, providerVersion: '*', signature, profile });
      const next = map.get(key) || {
        providerId, providerVersion: '*', signature, failureClass: String(plan.failureClass || 'unknown_failure'), profile,
        attempts: 0, successes: 0, failures: 0, consecutiveFailures: 0, lastOutcome: null, lastReason: null, lastSeenAt: null,
      };
      next.attempts += 1;
      const repairKey = String(attempt.repair_key || '');
      const accepted = acceptedByRepair.get(repairKey);
      const rejected = rejectedByRepair.get(repairKey);
      if (accepted) {
        next.successes += 1; next.consecutiveFailures = 0; next.lastOutcome = 'accepted';
        next.lastReason = sanitizeReason(accepted.reason || 'validated_improvement');
      } else if (rejected) {
        next.failures += 1; next.consecutiveFailures += 1; next.lastOutcome = 'rejected';
        next.lastReason = sanitizeReason(rejected.reason || 'no_validated_improvement');
      } else {
        next.lastOutcome = 'generated_without_terminal_outcome';
      }
      next.lastSeenAt = new Date().toISOString();
      map.set(key, next);
    }
  }
  const entries = [...map.values()].map(sanitizeMemoryEntry).filter(Boolean)
    .sort((a, b) => String(b.lastSeenAt || '').localeCompare(String(a.lastSeenAt || '')) || b.failures - a.failures)
    .slice(0, Math.max(1, Number(limit || 1000)));
  return { schemaVersion: 1, updatedAt: new Date().toISOString(), entries };
}
function sanitizeMemoryEntry(raw) {
  if (!isRecord(raw)) return null;
  const providerId = String(raw.providerId || '').trim().toLowerCase().slice(0, 128);
  const signature = String(raw.signature || '').trim().slice(0, 160);
  const profile = String(raw.profile || '').trim().slice(0, 96);
  if (!providerId || !signature || !profile) return null;
  return {
    providerId, providerVersion: String(raw.providerVersion || '*').trim().slice(0, 64) || '*', signature,
    failureClass: String(raw.failureClass || 'unknown_failure').trim().slice(0, 96), profile,
    attempts: nonNegative(raw.attempts), successes: nonNegative(raw.successes), failures: nonNegative(raw.failures),
    consecutiveFailures: nonNegative(raw.consecutiveFailures),
    lastOutcome: raw.lastOutcome ? String(raw.lastOutcome).slice(0, 48) : null,
    lastReason: raw.lastReason ? sanitizeReason(raw.lastReason) : null,
    lastSeenAt: raw.lastSeenAt ? String(raw.lastSeenAt).slice(0, 48) : null,
  };
}
function memoryKey(row) { return `${row.providerId}::${row.providerVersion || '*'}::${row.signature}::${row.profile}`; }
function providerFromKey(value) { const raw = String(value || '').split('::', 1)[0]; const parts = raw.split(':'); return parts.length > 1 ? parts.slice(1).join(':') : raw; }
function sanitizeReason(value) { return String(value || '').replace(/https?:\/\/\S+/gi, '<url>').replace(/(?:(?:token|authorization|cookie|secret)\s*[:=]\s*)\S+/gi, 'credential=<redacted>').replace(/\s+/g, ' ').trim().slice(0, 240); }
function nonNegative(value) { const n = Number(value); return Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0; }
function priorityScore(value) { return ({ critical: 4, high: 3, medium: 2, low: 1 })[String(value)] || 0; }
function dedupeProposals(rows) {
  const seen = new Set(); const out = [];
  for (const row of rows) {
    const key = [row.type, row.providerId || '', row.failureClass || '', row.profile || '', row.historicalDelta || '', row.target || ''].join('::');
    if (seen.has(key)) continue;
    seen.add(key); out.push(row);
  }
  return out.slice(0, 300);
}
function renderMarkdown(data) {
  const lines = [
    `# ${data.brain?.name ?? 'NiakVIO Brain'} — Learning Lab`, '',
    'Daily sandbox execution and sanitized cross-day memory. Nothing in this report publishes a provider or manifest to production automatically.', '',
    `Generated: ${data.generatedAt}`, '',
    `Learned skills observed: **${data.learnedSkillCount}**`,
    `Negative-memory entries: **${data.experimentMemory.entries.length}**`,
    `Historical high/critical unresolved: **${Number(data.historicalTraining.stats?.unresolvedHighPriority || 0)}**`,
    `Native repair-priority providers: **${data.nativeFeedback.repairPriorityProviders.length}**`,
    `Native reader failures: **${data.nativeFeedback.nativeReaderFailures}**`, '',
    '## Highest-priority proposals', '',
  ];
  const ordered = [...data.proposals].sort((a, b) => priorityScore(b.priority) - priorityScore(a.priority));
  if (!ordered.length) lines.push('No new proposal this run.');
  ordered.slice(0, 100).forEach((proposal, index) => {
    lines.push(`### ${index + 1}. ${proposal.type} — ${proposal.priority || 'low'}`, '');
    if (proposal.providerId) lines.push(`Provider: \`${proposal.providerId}\``);
    if (proposal.failureClass) lines.push(`Failure class: \`${proposal.failureClass}\``);
    if (proposal.profile) lines.push(`Profile: \`${proposal.profile}\``);
    lines.push(proposal.reason || '');
    if (proposal.proposal) lines.push('', proposal.proposal);
    if (proposal.proposedSkill) lines.push('', `Candidate composition: \`${proposal.proposedSkill.compose.join(' → ')}\``);
    lines.push('');
  });
  lines.push('## Privacy', '', data.privacy, '');
  return lines.join('\n');
}
function isRecord(value) { return Boolean(value) && typeof value === 'object' && !Array.isArray(value); }
function arg(name) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; }
function optionalArg(name) { const value = arg(name); return value ? path.resolve(value) : null; }
function resolveArg(name, fallback) { return path.resolve(arg(name) || fallback); }
function readJson(file, fallback) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } }
