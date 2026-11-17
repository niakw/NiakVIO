#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const GATE = path.join(ROOT, 'scripts', 'gate_native_provider_provenance.cjs');
const ANDROID = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'native-mobile-android-reader.yml'), 'utf8');
const IOS = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'native-mobile-ios-reader.yml'), 'utf8');
const DESKTOP = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'native-desktop-reader-acceptance.yml'), 'utf8');
const RELEASE = fs.readFileSync(path.join(ROOT, '.github', 'workflows', 'release-candidate-validation.yml'), 'utf8');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-provider-provenance-'));

for (const [name, workflow] of [['android', ANDROID], ['ios', IOS], ['desktop', DESKTOP]]) {
  assert.match(workflow, /certify_provenance:/, name + ' workflow must expose provenance certification input');
  assert.match(workflow, /gate_native_provider_provenance\.cjs/, name + ' workflow must execute provenance gate');
  assert.match(workflow, /inputs\.certify_provenance/, name + ' gate must remain release opt-in');
}
assert.match(RELEASE, /native-mobile-android-reader\.yml .*inputs\[certify_provenance\]=true/);
assert.match(RELEASE, /native-mobile-ios-reader\.yml .*inputs\[certify_provenance\]=true/);
assert.match(RELEASE, /native-desktop-reader-acceptance\.yml .*inputs\[certify_provenance\]=true/);

function b64(value) {
  return Buffer.from(String(value || ''), 'utf8').toString('base64url');
}

function runGeneric(name, expected, logical, title) {
  const file = path.join(tmp, name + '.log');
  fs.writeFileSync(
    file,
    'FIELD_NATIVE_ROW client=mobile fixture=interstellar provider64=' + b64(expected) +
      ' index=0 title64=' + b64(title) +
      ' name64=' + b64(title) +
      ' logical_provider64=' + b64(logical) + '\n'
  );
  return spawnSync(process.execPath, [GATE, '--client', 'mobile', file], { encoding: 'utf8' });
}

function runIos(name, expected, logical, title) {
  const file = path.join(tmp, name + '.log');
  fs.writeFileSync(
    file,
    'FIELD_NATIVE_IOS_ROW ' + JSON.stringify({
      fixture: 'interstellar',
      provider: expected,
      logicalProvider: logical,
      title,
      name: title,
    }) + '\n'
  );
  return spawnSync(process.execPath, [GATE, '--client', 'ios', file], { encoding: 'utf8' });
}

try {
  const mismatch = runGeneric('mismatch', 'purstream', 'other-provider', 'Purstream · Vidmoly - 1080p');
  assert.equal(mismatch.status, 4, mismatch.stdout + mismatch.stderr);
  assert.match(mismatch.stderr, /ownership_mismatches=1/);

  const noWitness = runGeneric('no-witness', 'purstream', 'purstream', 'Purstream - 1080p');
  assert.equal(noWitness.status, 3, noWitness.stdout + noWitness.stderr);
  assert.match(noWitness.stderr, /no_visible_external_provenance_witness/);

  const verified = runGeneric('verified', 'purstream', 'purstream', 'Purstream · Vidmoly - 1080p');
  assert.equal(verified.status, 0, verified.stdout + verified.stderr);
  assert.match(verified.stdout, /status=verified/);
  assert.match(verified.stdout, /external_witnesses=1/);

  const iosMismatch = runIos('ios-mismatch', 'purstream', 'other-provider', 'Purstream · Vidmoly - 1080p');
  assert.equal(iosMismatch.status, 4, iosMismatch.stdout + iosMismatch.stderr);

  const iosVerified = runIos('ios-verified', 'purstream', 'purstream', 'Purstream · Vidmoly - 1080p');
  assert.equal(iosVerified.status, 0, iosVerified.stdout + iosVerified.stderr);

  console.log('native provider provenance gate tests passed');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}
