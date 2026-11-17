#!/usr/bin/env node
'use strict';

/**
 * Release-certification gate for real multi-audio playback evidence.
 *
 * Ordinary native diagnostics may legitimately observe no multi-audio media.
 * Exact release certification may not claim the feature without at least one
 * transport-proven multi-audio HLS master whose audio tracks remain exposed by
 * the production player.
 */

const fs = require('node:fs');
const path = require('node:path');
const { assessNativeEvidence } = require('./native_evidence_completeness.cjs');

const args = process.argv.slice(2);
let client = 'unknown';
const logs = [];
for (let i = 0; i < args.length; i += 1) {
  if (args[i] === '--client') {
    client = String(args[++i] || '').trim() || 'unknown';
    continue;
  }
  logs.push(path.resolve(args[i]));
}
if (!logs.length) {
  console.error('Usage: gate_native_multi_audio_coverage.cjs --client <label> <native-log> [...]');
  process.exit(2);
}
for (const file of logs) {
  if (!fs.existsSync(file) || fs.statSync(file).size <= 0) {
    console.error(`FIELD_NATIVE_MULTI_AUDIO_COVERAGE status=fail client=${client} reason=missing_log file=${file}`);
    process.exit(2);
  }
}

const assessment = assessNativeEvidence(logs);
const expected = Number(assessment?.stats?.multiAudioExpected || 0);
const verified = Number(assessment?.stats?.multiAudioVerified || 0);
const audioProblems = (assessment?.problems || []).filter((row) =>
  String(row).startsWith('multi_audio_player_')
);

if (expected < 1) {
  console.error(
    `FIELD_NATIVE_MULTI_AUDIO_COVERAGE status=unproven client=${client} expected=0 verified=0 logs=${logs.length}`
  );
  process.exit(3);
}
if (audioProblems.length || verified < expected) {
  console.error(
    `FIELD_NATIVE_MULTI_AUDIO_COVERAGE status=fail client=${client} expected=${expected} verified=${verified} ` +
    `problems=${audioProblems.slice(0, 12).join(';') || 'verification_gap'}`
  );
  process.exit(4);
}
console.log(
  `FIELD_NATIVE_MULTI_AUDIO_COVERAGE status=verified client=${client} expected=${expected} verified=${verified} logs=${logs.length}`
);
