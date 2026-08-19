#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import { BRAIN_CONTROL_PLANE_VERSION, planRepair } from '../src/repair-brain.mjs';

const require = createRequire(import.meta.url);
const { readerFailureClass, readerSignature, isReaderFailure } = require('../../scripts/native_player_diagnostics.cjs');

const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const outputPath = outputIndex >= 0 && args[outputIndex + 1]
  ? path.resolve(args[outputIndex + 1])
  : path.resolve('targeted-reader-brain.json');
const logPaths = args.filter((value, index) => index !== outputIndex && index !== outputIndex + 1 && value !== '--output').map((value) => path.resolve(value));

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

const readerRows = [];
for (const file of logPaths) {
  if (!fs.existsSync(file)) continue;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (marker < 0) continue;
    const f = fields(raw.slice(marker).trim());
    const row = {
      client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
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
    row.signature = readerSignature(row);
    readerRows.push(row);
  }
}

const failures = readerRows.filter(isReaderFailure);
const plans = failures.map((row) => {
  const evidence = {
    invoked: true,
    signature: row.signature,
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
  const plan = planRepair(evidence, { signature: row.signature, maxHypotheses: 3 });
  return {
    provider: String(row.provider || '').toLowerCase(), client: row.client, fixture: row.fixture, index: row.index,
    state: row.state, failureClass: row.failureClass, failureStage: row.failureStage,
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
});

const grouped = new Map();
for (const plan of plans) {
  const key = `${plan.provider}\u0000${plan.failureClass}`;
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key).push(plan);
}
const priorities = [...grouped.values()]
  .map((rows) => ({
    provider: rows[0].provider,
    failureClass: rows[0].failureClass,
    occurrences: rows.length,
    clients: [...new Set(rows.map((row) => row.client))].sort(),
    fixtures: [...new Set(rows.map((row) => row.fixture))].sort(),
    firstHypothesis: rows[0].hypotheses[0]?.id || null,
    signatures: [...new Set(rows.map((row) => row.signature))].slice(0, 12),
  }))
  .sort((a, b) => b.occurrences - a.occurrences || a.provider.localeCompare(b.provider));

const payload = {
  schemaVersion: 2,
  generatedAt: new Date().toISOString(),
  brainVersion: BRAIN_CONTROL_PLANE_VERSION,
  readerObserved: readerRows.length,
  readerHealthy: readerRows.length - failures.length,
  readerFailures: failures.length,
  readerLoadErrorEvidence: readerRows.filter((row) => row.loadDurationMs > 0 || row.loadBytes > 0 || row.httpStatus > 0).length,
  plans,
  priorities,
  policy: {
    productionWritesAllowed: false,
    publicationAllowed: false,
    requireFreshNativeReaderProofAfterRepair: true,
  },
  privacy: 'No raw URLs, query tokens, cookie values, authorization values or response-header values are persisted.',
};
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2) + '\n');
console.log(`FIELD_NATIVE_READER_BRAIN observed=${payload.readerObserved} healthy=${payload.readerHealthy} failures=${payload.readerFailures} load_error_evidence=${payload.readerLoadErrorEvidence} priorities=${priorities.length}`);
for (const priority of priorities.slice(0, 40)) console.log(`FIELD_NATIVE_READER_BRAIN_PRIORITY ${JSON.stringify(priority)}`);
if (readerRows.length === 0) process.exitCode = 2;
