#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const GATE = path.join(ROOT, 'scripts', 'gate_native_multi_audio_coverage.cjs');
const ANDROID = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'native-mobile-android-reader.yml'), 'utf8');
const DESKTOP = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'native-desktop-reader-acceptance.yml'), 'utf8');
const RELEASE = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'release-candidate-validation.yml'), 'utf8');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-multi-audio-gate-'));

for (const [name, workflow] of [['android', ANDROID], ['desktop', DESKTOP]]) {
  assert.match(workflow, /certify_multi_audio:/, `${name} workflow must expose release certification input`);
  assert.match(workflow, /gate_native_multi_audio_coverage\.cjs/, `${name} workflow must execute strict multi-audio gate`);
  assert.match(workflow, /inputs\.certify_multi_audio/, `${name} gate must remain opt-in outside release certification`);
}
assert.match(RELEASE, /native-mobile-android-reader\.yml -F 'inputs\[certify_multi_audio\]=true'/);
assert.match(RELEASE, /native-mobile-ios-reader\.yml -f 'inputs\[mode\]=full' -F 'inputs\[certify_multi_audio\]=true'/);
assert.match(RELEASE, /native-desktop-reader-acceptance\.yml -F 'inputs\[certify_multi_audio\]=true'/);

function b64(value) {
  return Buffer.from(String(value || ''), 'utf8').toString('base64url');
}

function run(name, playerCount, transportCount, playerLanguages = '', transportLanguages = '') {
  const file = path.join(tmp, `${name}.log`);
  const rows = [
    'FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie',
    'FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider=test request_type=movie returned=1',
    'FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=sinners-2025 provider=test request_type=movie index=0',
    `FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ready audio_track_count=${playerCount} audio_track_languages64=${b64(playerLanguages)}`,
    `FIELD_NATIVE_TRANSPORT client=tv fixture=sinners-2025 provider=test request_type=movie index=0 state=ok kind=hls audio_track_count=${transportCount} audio_track_languages64=${b64(transportLanguages)}`,
  ];
  fs.writeFileSync(file, rows.join('\n') + '\n');
  return spawnSync(process.execPath, [GATE, '--client', 'tv', file], { encoding: 'utf8' });
}

try {
  const absent = run('absent', 1, 1);
  assert.notEqual(absent.status, 0, absent.stdout + absent.stderr);
  assert.match(absent.stderr, /status=unproven/);

  const collapsed = run('collapsed', 1, 2, 'en', 'en,fr');
  assert.notEqual(collapsed.status, 0, collapsed.stdout + collapsed.stderr);
  assert.match(collapsed.stderr, /status=fail/);
  assert.match(collapsed.stderr, /expected=1 verified=0/);

  const languageCollapsed = run('language-collapsed', 2, 2, 'en', 'en,fr');
  assert.notEqual(languageCollapsed.status, 0, languageCollapsed.stdout + languageCollapsed.stderr);
  assert.match(languageCollapsed.stderr, /multi_audio_language_observation_missing/);

  const noLanguageWitness = run('no-language-witness', 2, 2, 'en,fr', '');
  assert.notEqual(noLanguageWitness.status, 0, noLanguageWitness.stdout + noLanguageWitness.stderr);
  assert.match(noLanguageWitness.stderr, /reason=no_distinct_language_witness/);

  const preserved = run('preserved', 2, 2, 'en,fr', 'en,fr');
  assert.equal(preserved.status, 0, preserved.stdout + preserved.stderr);
  assert.match(preserved.stdout, /status=verified/);
  assert.match(preserved.stdout, /expected=1 verified=1/);
  assert.match(preserved.stdout, /language_expected=1 language_verified=1/);

  console.log('native multi-audio release coverage gate tests passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
