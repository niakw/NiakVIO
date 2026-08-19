import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const script = path.join(root, 'engine_v2/scripts/diagnose-native-reader.mjs');
const b64 = (value) => Buffer.from(String(value)).toString('base64url');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-reader-brain-'));
try {
  const log = path.join(tmp, 'tv-native-corpus-sinners-2025.log');
  const output = path.join(tmp, 'brain.json');
  fs.writeFileSync(log, [
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} index=0 state=error engine=media3 http_status=403 failure_stage=http_access duration_seconds=0 host64=${b64('zip.example')} error_class64=${b64('PlaybackException')} error_code64=${b64('ERROR_CODE_IO_BAD_HTTP_STATUS')} exception_chain64=${b64('InvalidResponseCodeException')} response_header_names64=${b64('content-type,date')}`,
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('MOVIESDRIVE')} index=1 state=short_media engine=media3 http_status=0 failure_stage=duration_identity duration_seconds=20 host64=${b64('media.example')} error_class64=${b64('')} error_code64=${b64('')} exception_chain64=${b64('')} response_header_names64=${b64('')}`,
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64=${b64('PURSTREAM')} index=0 state=ready engine=media3 http_status=0 failure_stage=none duration_seconds=8220 host64=${b64('media.example')} error_class64=${b64('')} error_code64=${b64('')} exception_chain64=${b64('')} response_header_names64=${b64('')}`,
  ].join('\n') + '\n');
  const run = spawnSync(process.execPath, [script, '--output', output, log], { cwd: root, encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr);
  const data = JSON.parse(fs.readFileSync(output, 'utf8'));
  assert.equal(data.brainVersion, 4);
  assert.equal(data.readerObserved, 3);
  assert.equal(data.readerHealthy, 1);
  assert.equal(data.readerFailures, 2);
  const access = data.plans.find((row) => row.failureClass === 'playback_http_access');
  assert.ok(access);
  assert.equal(access.httpStatus, 403);
  assert.equal(access.hypotheses[0].id, 'replay-native-request-context');
  const short = data.plans.find((row) => row.failureClass === 'short_media');
  assert.ok(short);
  assert.equal(short.durationSeconds, 20);
  assert.equal(short.hypotheses[0].id, 'reject-short-or-preview-media');
  assert.equal(data.policy.requireFreshNativeReaderProofAfterRepair, true);
  assert.match(data.privacy, /No raw URLs/);
  assert.match(run.stdout, /FIELD_NATIVE_READER_BRAIN/);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log('targeted native reader Brain diagnosis tests passed');
