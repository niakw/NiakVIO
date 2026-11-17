#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const GATE = path.join(ROOT, 'scripts', 'gate_native_multi_audio_coverage.cjs');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-multi-audio-gate-'));

function run(name, playerCount, transportCount) {
  const file = path.join(tmp, `${name}.log`);
  const rows = [
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready audio_track_count=${playerCount}`,
    `FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=${transportCount}`,
  ];
  fs.writeFileSync(file, rows.join('\n') + '\n');
  return spawnSync(process.execPath, [GATE, '--client', 'tv', file], { encoding: 'utf8' });
}

try {
  const absent = run('absent', 1, 1);
  assert.notEqual(absent.status, 0, absent.stdout + absent.stderr);
  assert.match(absent.stderr, /status=unproven/);

  const collapsed = run('collapsed', 1, 2);
  assert.notEqual(collapsed.status, 0, collapsed.stdout + collapsed.stderr);
  assert.match(collapsed.stderr, /status=fail/);
  assert.match(collapsed.stderr, /expected=1 verified=0/);

  const preserved = run('preserved', 2, 2);
  assert.equal(preserved.status, 0, preserved.stdout + preserved.stderr);
  assert.match(preserved.stdout, /status=verified/);
  assert.match(preserved.stdout, /expected=1 verified=1/);

  console.log('native multi-audio release coverage gate tests passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
