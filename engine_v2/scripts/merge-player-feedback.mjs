#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const statePath = required('--state');
const evidencePath = required('--player-evidence');
const outputPath = optional('--output') || statePath;
const state = readJson(statePath);
const evidence = readJson(evidencePath);
const rows = Array.isArray(evidence.providers) ? evidence.providers.filter(isRecord) : [];

const sanitized = rows.map((row) => ({
  providerId: cleanId(row.providerId),
  state: clean(row.state, 48),
  failureClass: clean(row.repairClass || 'unknown_failure', 96),
  exoCodes: uniqueNumbers(row.exoCodes),
  exoCodeNames: uniqueStrings(row.exoCodeNames, 80),
  sourceSignatures: uniqueStrings(row.sourceSignatures, 80),
  sourceStatuses: uniqueNumbers(row.sourceStatuses),
  mpvRecovered: row.mpvRecovered === true,
  exoReady: row.exoReady === true,
  evidenceCount: nonNegative(row.evidenceCount),
})).filter((row) => row.providerId);

const counts = {};
for (const row of sanitized) {
  if (row.exoReady) continue;
  counts[row.failureClass] = (counts[row.failureClass] || 0) + 1;
}

const playerProposals = sanitized
  .filter((row) => !row.exoReady && row.state !== 'empty')
  .map((row) => ({
    type: 'native_player_repair_target',
    priority: priorityFor(row),
    providerId: row.providerId,
    failureClass: row.failureClass,
    exoCodes: row.exoCodes,
    exoCodeNames: row.exoCodeNames,
    sourceSignatures: row.sourceSignatures,
    sourceStatuses: row.sourceStatuses,
    mpvRecovered: row.mpvRecovered,
    evidenceCount: row.evidenceCount,
    reason: reasonFor(row),
  }));

const existing = Array.isArray(state.proposals) ? state.proposals : [];
state.proposals = dedupe([...existing, ...playerProposals]).slice(0, 400);
state.playerFeedback = {
  schemaVersion: 1,
  fixture: clean(evidence.fixture, 96),
  source: 'official-nuviotv-player-lab',
  providersObserved: sanitized.length,
  exoReadyProviders: sanitized.filter((row) => row.exoReady).length,
  mpvOnlyProviders: sanitized.filter((row) => row.mpvRecovered && !row.exoReady).length,
  unplayableProviders: sanitized.filter((row) => !row.exoReady && !row.mpvRecovered && row.state !== 'empty').length,
  failureCounts: counts,
  repairPriorityProviders: sanitized
    .filter((row) => !row.exoReady && row.state !== 'empty')
    .map((row) => row.providerId),
};
state.unresolvedFailureCounts = mergeCounts(state.unresolvedFailureCounts, counts);
state.privacy = 'No raw URLs, tokens, header values, cookies, private notes or spreadsheet text are copied into persistent Brain learning state.';

fs.writeFileSync(outputPath, JSON.stringify(state, null, 2) + '\n');
console.log(`FIELD_BRAIN_PLAYER_FEEDBACK fixture=${state.playerFeedback.fixture} providers=${state.playerFeedback.providersObserved} exo_ready=${state.playerFeedback.exoReadyProviders} mpv_only=${state.playerFeedback.mpvOnlyProviders} unplayable=${state.playerFeedback.unplayableProviders}`);

function required(name) {
  const value = optional(name);
  if (!value) throw new Error(`missing ${name}`);
  return value;
}
function optional(name) {
  const at = args.indexOf(name);
  return at >= 0 ? args[at + 1] : null;
}
function readJson(file) {
  const value = JSON.parse(fs.readFileSync(path.resolve(file), 'utf8'));
  if (!isRecord(value)) throw new Error(`${file}: expected object`);
  return value;
}
function isRecord(value) { return value && typeof value === 'object' && !Array.isArray(value); }
function clean(value, limit) { return String(value || '').replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, limit); }
function cleanId(value) { return clean(value, 128).toLowerCase(); }
function nonNegative(value) { const n = Number(value); return Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0; }
function uniqueNumbers(values) { return [...new Set((Array.isArray(values) ? values : []).map(Number).filter(Number.isFinite))].slice(0, 20); }
function uniqueStrings(values, limit) { return [...new Set((Array.isArray(values) ? values : []).map((value) => clean(value, limit)).filter(Boolean))].slice(0, 20); }
function priorityFor(row) {
  if (row.failureClass === 'playback_context_gap' && row.sourceStatuses.some((code) => [401, 403, 407, 429, 451].includes(code))) return 'critical';
  if (row.failureClass === 'media_extraction_gap' || row.failureClass === 'player_container_unsupported') return 'high';
  if (row.failureClass === 'player_engine_compatibility_gap') return 'high';
  return 'medium';
}
function reasonFor(row) {
  if (row.failureClass === 'player_engine_compatibility_gap') return 'The official NuvioTV ExoPlayer path failed while MPV parsed the same provider output. Prefer another provider source compatible with both engines when available; do not guess headers without HTTP evidence.';
  if (row.failureClass === 'player_container_unsupported') return 'The official NuvioTV reader reported an unsupported container on the provider output. Re-resolve the terminal player/media chain and test alternate sources before changing headers or codecs.';
  if (row.failureClass === 'media_extraction_gap') return 'The provider returned content that did not prove to be terminal media in the official player lab. Repair the player/embed extraction chain before publication.';
  if (row.failureClass === 'playback_context_gap') return 'The official player evidence indicates an HTTP/session context failure. Preserve the exact scoped playback context from the provider player chain.';
  return `Official NuvioTV player evidence classified this provider as ${row.failureClass}. Use the reader evidence before another mutation.`;
}
function mergeCounts(base, extra) {
  const out = isRecord(base) ? { ...base } : {};
  for (const [key, value] of Object.entries(extra)) out[key] = Number(out[key] || 0) + Number(value || 0);
  return out;
}
function dedupe(rows) {
  const seen = new Set();
  const out = [];
  for (const row of rows) {
    const key = [row.type || '', row.providerId || '', row.failureClass || '', row.profile || '', row.target || ''].join('::');
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(row);
  }
  return out;
}
