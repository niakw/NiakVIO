'use strict';

const fs = require('node:fs');

const paths = process.argv.slice(2);
if (!paths.length) {
  console.error('usage: node gate_native_player_reached.cjs <log> [log...]');
  process.exit(2);
}

const RUNTIME_ERROR_SENTINEL = '__NIAKVIO_RUNTIME_ERROR__';

function fields(line) {
  const out = new Map();
  for (const token of line.trim().split(/\s+/).slice(1)) {
    const index = token.indexOf('=');
    if (index <= 0) continue;
    out.set(token.slice(0, index), token.slice(index + 1));
  }
  return out;
}

function decode(value) {
  if (!value) return '';
  let text = String(value).replace(/-/g, '+').replace(/_/g, '/');
  while (text.length % 4) text += '=';
  try { return Buffer.from(text, 'base64').toString('utf8'); } catch { return ''; }
}

function executionKey(parsed) {
  return [
    parsed.get('client') || 'unknown',
    parsed.get('fixture') || 'unknown',
    parsed.get('provider64') || parsed.get('provider') || 'unknown',
    parsed.get('request_type') || 'unknown',
  ].join('\u0000');
}

let readable = 0;
let terminalEvidence = 0;
let productionPlayerReached = 0;
let rejectedSetup = 0;
const byClient = new Map();
const structuralFailures = [];
const executed = new Set();
const runtimeSentinels = new Set();

for (const file of paths) {
  if (!fs.existsSync(file)) continue;
  readable += 1;
  const text = fs.readFileSync(file, 'utf8');
  const state = {
    file,
    begin: false,
    end: false,
    expected: 0,
    observed: new Set(),
    executions: new Set(),
    players: 0,
    placeholder: false,
  };

  for (const raw of text.split(/\r?\n/)) {
    const nativeAt = raw.indexOf('FIELD_NATIVE_');
    if (nativeAt < 0) continue;
    const line = raw.slice(nativeAt).trim();
    const parsed = fields(line);

    if (line.startsWith('FIELD_NATIVE_SMOKE_DIAGNOSTIC_PLACEHOLDER ')) {
      state.placeholder = true;
    } else if (line.startsWith('FIELD_NATIVE_CORPUS_BEGIN ')) {
      state.begin = true;
      state.expected = Math.max(state.expected, Number(parsed.get('providers') || 0) || 0);
    } else if (line.startsWith('FIELD_NATIVE_CORPUS_END ')) {
      state.end = true;
    } else if (
      line.startsWith('FIELD_NATIVE_RESULT ') ||
      line.startsWith('FIELD_NATIVE_ERROR ') ||
      line.startsWith('FIELD_NATIVE_PROVIDER_SKIPPED ')
    ) {
      const provider = parsed.get('provider64') || parsed.get('provider') || '';
      if (provider) state.observed.add(provider);
      if (line.startsWith('FIELD_NATIVE_RESULT ') || line.startsWith('FIELD_NATIVE_ERROR ')) {
        const key = executionKey(parsed);
        state.executions.add(key);
        executed.add(key);
      }
    } else if (line.startsWith('FIELD_NATIVE_ROW ')) {
      const type = decode(parsed.get('type64'));
      const title = decode(parsed.get('title64'));
      if (type === RUNTIME_ERROR_SENTINEL || title === RUNTIME_ERROR_SENTINEL) {
        runtimeSentinels.add(executionKey(parsed));
      }
    }

    if (!line.startsWith('FIELD_NATIVE_PLAYER ')) continue;
    state.players += 1;
    terminalEvidence += 1;
    const client = parsed.get('client') || 'unknown';
    const engine = parsed.get('engine') || '';
    const failureStage = parsed.get('failure_stage') || '';
    const errorCode = parsed.get('error_code') || '';
    const isProduction = /-production$/i.test(engine);
    const isSetupOnly = failureStage === 'player_setup' || errorCode === 'NO_LAUNCH_INTENT';
    if (!isProduction || isSetupOnly) {
      if (isSetupOnly) rejectedSetup += 1;
      continue;
    }
    productionPlayerReached += 1;
    byClient.set(client, Number(byClient.get(client) || 0) + 1);
  }

  if (state.placeholder) structuralFailures.push(`${file}:diagnostic_placeholder`);
  if (!state.begin) structuralFailures.push(`${file}:missing_begin`);
  if (!state.end) structuralFailures.push(`${file}:missing_end`);
  if (state.expected <= 0) structuralFailures.push(`${file}:invalid_expected_provider_count`);
  else if (state.observed.size < state.expected) {
    structuralFailures.push(`${file}:incomplete_provider_traversal:${state.observed.size}/${state.expected}`);
  }
  if (state.executions.size === 0) structuralFailures.push(`${file}:zero_provider_executions`);
  if (state.players === 0) structuralFailures.push(`${file}:zero_media_verified`);
}

if (!readable) {
  console.error('FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=no_readable_logs terminal=0 production=0 setup_rejected=0 blocking=true owner=lab_infra');
  process.exit(3);
}

if (structuralFailures.length) {
  console.error(
    `FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=incomplete_native_evidence ` +
    `terminal=${terminalEvidence} production=${productionPlayerReached} setup_rejected=${rejectedSetup} ` +
    `problems=${structuralFailures.length} blocking=true owner=lab_infra`
  );
  for (const problem of structuralFailures.slice(0, 40)) {
    console.error(`FIELD_NATIVE_PLAYER_REACH_INFRA_ERROR ${problem}`);
  }
  process.exit(5);
}

const executedCount = executed.size;
const sentinelCount = runtimeSentinels.size;
const sentinelRatio = executedCount ? sentinelCount / executedCount : 0;
const systemicRuntimeFailure = sentinelCount > 0 && (
  sentinelCount === executedCount || (sentinelCount >= 3 && sentinelRatio >= 0.75)
);
if (systemicRuntimeFailure) {
  console.error(
    `FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=systemic_provider_runtime_error ` +
    `runtime_sentinels=${sentinelCount} executions=${executedCount} ratio=${sentinelRatio.toFixed(3)} ` +
    `terminal=${terminalEvidence} production=${productionPlayerReached} blocking=true owner=runtime_contract`
  );
  process.exit(6);
}

if (!productionPlayerReached) {
  // A route with complete runtime/reader evidence but no successful production-player
  // reach remains Brain evidence by default. Structural/runtime-contract failures above
  // are always blocking; callers may separately make playback outcome strict.
  const blocking = process.env.NIAKVIO_NATIVE_PLAYER_GATE_BLOCKING === '1';
  console.error(
    `FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=production_player_never_reached ` +
    `terminal=${terminalEvidence} production=0 setup_rejected=${rejectedSetup} ` +
    `runtime_sentinels=${sentinelCount} executions=${executedCount} ` +
    `blocking=${blocking} owner=brain`
  );
  if (blocking) process.exit(4);
  process.exit(0);
}
const clients = [...byClient.entries()].map(([client, count]) => `${client}:${count}`).join(',');
console.log(
  `FIELD_NATIVE_PLAYER_REACH_GATE status=pass terminal=${terminalEvidence} ` +
  `production=${productionPlayerReached} setup_rejected=${rejectedSetup} clients=${clients} ` +
  `runtime_sentinels=${sentinelCount} executions=${executedCount} blocking=false owner=brain`
);
