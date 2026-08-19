#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const { readerFailureClass, readerSignature, isReaderFailure } = require('./native_player_diagnostics.cjs');

const logs = process.argv.slice(2);
if (!logs.length) {
  process.stderr.write('usage: node scripts/gate_native_reader_result.cjs <log> [log ...]\n');
  process.exit(64);
}

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

const rows = [];
let readable = 0;
for (const file of logs) {
  if (!fs.existsSync(file)) continue;
  readable += 1;
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const marker = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (marker < 0) continue;
    const f = fields(raw.slice(marker).trim());
    const row = {
      client: f.client || 'unknown', fixture: f.fixture || 'unknown', provider: decode(f.provider64),
      index: Number(f.index || 0), state: f.state || 'unknown', engine: f.engine || 'unknown',
      httpStatus: Number(f.http_status || 0), failureStage: f.failure_stage || 'unknown',
      durationSeconds: Number(f.duration_seconds || 0) || null, host: decode(f.host64),
      errorClass: decode(f.error_class64), errorCode: decode(f.error_code64),
      exceptionChain: decode(f.exception_chain64), responseHeaderNames: decode(f.response_header_names64),
    };
    row.failureClass = readerFailureClass(row);
    row.signature = readerSignature(row);
    rows.push(row);
  }
}

if (readable === 0) {
  console.error('FIELD_NATIVE_READER_GATE state=infra_error reason=no_readable_log');
  process.exit(2);
}
if (rows.length === 0) {
  console.error('FIELD_NATIVE_READER_GATE state=infra_error reason=missing_native_reader_evidence');
  process.exit(2);
}

const failures = rows.filter(isReaderFailure);
const healthy = rows.filter((row) => !isReaderFailure(row));
console.log(`FIELD_NATIVE_READER_GATE state=${failures.length ? 'failed' : 'passed'} observed=${rows.length} healthy=${healthy.length} failures=${failures.length}`);
for (const row of failures.slice(0, 40)) {
  // All fields are already sanitized or structural. Never print raw stream URLs or request values here.
  console.log(`FIELD_NATIVE_READER_GATE_FAILURE ${JSON.stringify({
    client: row.client, fixture: row.fixture, provider: row.provider, index: row.index,
    failureClass: row.failureClass, httpStatus: row.httpStatus, failureStage: row.failureStage,
    errorCode: row.errorCode, errorClass: row.errorClass, host: row.host,
    durationSeconds: row.durationSeconds, signature: row.signature,
    exceptionChain: row.exceptionChain, responseHeaderNames: row.responseHeaderNames,
  })}`);
}
process.exit(failures.length ? 1 : 0);
