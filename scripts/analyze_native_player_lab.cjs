#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const fixture = String(process.argv[2] || '').trim();
const logPath = String(process.argv[3] || '').trim();
const outputDir = path.resolve(process.argv[4] || path.dirname(logPath || '.'));
if (!fixture || !logPath) {
  console.error('usage: node scripts/analyze_native_player_lab.cjs <fixture> <log> [output-dir]');
  process.exit(2);
}
const text = fs.existsSync(logPath) ? fs.readFileSync(logPath, 'utf8') : '';
const lines = text.split(/\r?\n/).filter(Boolean);
const attempts = [];
const providers = new Map();
let begin = false;
let end = false;

for (const raw of lines) {
  const line = raw.slice(raw.indexOf('FIELD_'));
  if (!line.startsWith('FIELD_')) continue;
  if (line.startsWith('FIELD_PLAYER_LAB_BEGIN ')) begin = true;
  if (line.startsWith('FIELD_PLAYER_LAB_END ')) end = true;
  if (line.startsWith('FIELD_PLAYER_ATTEMPT ')) {
    const row = parseFields(line);
    const provider = decode64(row.provider64).toLowerCase();
    if (!provider) continue;
    const attempt = {
      provider,
      index: number(row.index),
      sourceStatus: number(row.source_status),
      sourceSignature: clean(row.signature),
      contentType: decode64(row.content_type64),
      sourceHost: decode64(row.host64),
      finalHost: decode64(row.final_host64),
      acceptsRanges: row.ranges === 'true',
      exo: {
        state: clean(row.exo_state),
        code: number(row.exo_code),
        codeName: clean(row.exo_name),
        mimeType: decode64(row.exo_mime64),
        cause: sanitizeCause(decode64(row.exo_cause64)),
      },
      mpv: {
        state: clean(row.mpv_state),
        codeName: clean(row.mpv_name),
        cause: sanitizeCause(decode64(row.mpv_cause64)),
      },
      repairClass: clean(row.repair_class) || 'player_runtime_gap',
    };
    attempts.push(attempt);
  }
  if (line.startsWith('FIELD_PLAYER_PROVIDER ')) {
    const row = parseFields(line);
    const provider = decode64(row.provider64).toLowerCase();
    if (!provider) continue;
    providers.set(provider, {
      provider,
      state: clean(row.state),
      streams: number(row.streams),
      repairClass: clean(row.repair_class) || null,
      runtimeError: row.error64 ? sanitizeCause(decode64(row.error64)) : null,
    });
  }
}

const byRepairClass = countBy(attempts, (row) => row.repairClass);
const byExoCode = countBy(attempts.filter((row) => row.exo.code), (row) => `${row.exo.code}:${row.exo.codeName || 'UNKNOWN'}`);
const providerRows = [...providers.values()].sort((a, b) => a.provider.localeCompare(b.provider));
const summary = {
  schemaVersion: 1,
  fixture,
  generatedAt: new Date().toISOString(),
  complete: begin && end,
  providersObserved: providerRows.length,
  providersWithRows: providerRows.filter((row) => !['empty', 'runtime_error'].includes(row.state)).length,
  exoReadyProviders: providerRows.filter((row) => row.state === 'exo_ready').length,
  mpvOnlyProviders: providerRows.filter((row) => row.state === 'mpv_only').length,
  unplayableProviders: providerRows.filter((row) => row.state === 'unplayable').length,
  runtimeErrorProviders: providerRows.filter((row) => row.state === 'runtime_error').length,
  attempts: attempts.length,
  byRepairClass,
  byExoCode,
  providers: providerRows,
};

const repairEvidence = {
  schemaVersion: 1,
  generatedAt: summary.generatedAt,
  fixture,
  source: 'official-nuviotv-player-lab',
  policy: {
    productionWritesAllowed: false,
    rawUrlsPersisted: false,
    headerValuesPersisted: false,
  },
  providers: providerRows.map((provider) => {
    const rows = attempts.filter((row) => row.provider === provider.provider);
    return {
      providerId: provider.provider,
      state: provider.state,
      repairClass: provider.repairClass || dominant(rows.map((row) => row.repairClass)) || 'unknown_failure',
      exoCodes: [...new Set(rows.map((row) => row.exo.code).filter(Boolean))],
      exoCodeNames: [...new Set(rows.map((row) => row.exo.codeName).filter(Boolean))],
      sourceSignatures: [...new Set(rows.map((row) => row.sourceSignature).filter(Boolean))],
      sourceStatuses: [...new Set(rows.map((row) => row.sourceStatus).filter(Boolean))],
      mpvRecovered: rows.some((row) => row.mpv.state === 'ready'),
      exoReady: rows.some((row) => row.exo.state === 'ready'),
      evidenceCount: rows.length,
    };
  }),
};

fs.mkdirSync(outputDir, { recursive: true });
const summaryPath = path.join(outputDir, `player-lab-summary-${fixture}.json`);
const repairPath = path.join(outputDir, `player-repair-evidence-${fixture}.json`);
fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2) + '\n');
fs.writeFileSync(repairPath, JSON.stringify(repairEvidence, null, 2) + '\n');
console.log(`FIELD_PLAYER_LAB_ANALYSIS fixture=${fixture} complete=${summary.complete} attempts=${summary.attempts} exo_ready=${summary.exoReadyProviders} mpv_only=${summary.mpvOnlyProviders} unplayable=${summary.unplayableProviders}`);
if (!summary.complete) process.exit(1);

function parseFields(line) {
  const out = {};
  for (const token of line.trim().split(/\s+/).slice(1)) {
    const at = token.indexOf('=');
    if (at <= 0) continue;
    out[token.slice(0, at)] = token.slice(at + 1);
  }
  return out;
}
function decode64(value) {
  if (!value) return '';
  try { return Buffer.from(String(value).replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8'); }
  catch { return ''; }
}
function number(value) { const n = Number(value); return Number.isFinite(n) ? n : 0; }
function clean(value) { return String(value || '').replace(/[^A-Za-z0-9_.:-]/g, '').slice(0, 120); }
function sanitizeCause(value) {
  return String(value || '')
    .replace(/https?:\/\/\S+/gi, '<url>')
    .replace(/(?:(?:authorization|cookie|token|secret)\s*[:=]\s*)\S+/gi, 'credential=<redacted>')
    .replace(/\s+/g, ' ').trim().slice(0, 700);
}
function countBy(rows, keyFn) {
  const out = {};
  for (const row of rows) { const key = keyFn(row); out[key] = (out[key] || 0) + 1; }
  return Object.fromEntries(Object.entries(out).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])));
}
function dominant(values) {
  const counts = countBy(values.filter(Boolean), (value) => value);
  return Object.keys(counts)[0] || null;
}
