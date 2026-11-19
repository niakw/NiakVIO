#!/usr/bin/env node
'use strict';

// Real corpus analyzer and production player gate must agree: READY and a
// plausible duration without nonzero video dimensions is not decoded media.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const fixture = 'jujutsu-kaisen-s01e01';
const collection = path.join(root, 'scripts/analyze_native_corpus_collection.cjs');
const player = path.join(root, 'scripts/gate_native_player_reached.cjs');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'niakvio-native-gate-'));

function run(extraPlayerFields) {
  const log = path.join(temp, 'native.log');
  fs.writeFileSync(log, [
    `FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=${fixture} providers=1`,
    `FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=${fixture} provider64=RlJFTkNILU1BTkdB enabled=true logical_type=anime request_type=anime route_mode=declared`,
    `FIELD_NATIVE_RESULT client=tv fixture=${fixture} provider64=RlJFTkNILU1BTkdB request_type=anime route_mode=declared enabled=true duration_ms=12583 count=2`,
    `FIELD_NATIVE_PLAYER client=tv fixture=${fixture} provider64=RlJFTkNILU1BTkdB request_type=anime route_mode=declared index=0 state=ready engine=nuvio-tv-production production_surface=true duration_seconds=1435.007 failure_stage=none ${extraPlayerFields}`,
    `FIELD_NATIVE_CORPUS_END client=tv fixture=${fixture} errors=0`,
    '',
  ].join('\n'), 'utf8');

  const observed = spawnSync(process.execPath, [collection, fixture, log], {
    cwd: root, encoding: 'utf8', timeout: 30000,
  });
  const authoritative = spawnSync(process.execPath, [player, log], {
    cwd: root, encoding: 'utf8', timeout: 30000,
    env: { ...process.env, NIAKVIO_NATIVE_PLAYER_GATE_BLOCKING: '1' },
  });
  assert.equal(observed.error, undefined, observed.stderr);
  assert.equal(authoritative.error, undefined, authoritative.stderr);
  return {
    observed,
    authoritative,
    collectionOutput: observed.stdout + observed.stderr,
    playerOutput: authoritative.stdout + authoritative.stderr,
  };
}

try {
  const undecoded = run('video_width=0 video_height=0 audio_track_count=0');
  assert.match(undecoded.collectionOutput, /player_terminals=1 media_verified=0/);
  assert.match(undecoded.collectionOutput, /zero_media_verified:tv:jujutsu-kaisen-s01e01/);
  assert.notEqual(undecoded.observed.status, 0);
  assert.match(undecoded.playerOutput, /playback_verified=0/);
  assert.notEqual(undecoded.authoritative.status, 0);

  const decodedFormat = run('video_width=1280 video_height=720 audio_track_count=1');
  assert.match(decodedFormat.collectionOutput, /player_terminals=1 media_verified=1/);
  assert.equal(decodedFormat.observed.status, 0, decodedFormat.collectionOutput);
  assert.match(decodedFormat.playerOutput, /playback_verified=1/);
  assert.equal(decodedFormat.authoritative.status, 0, decodedFormat.playerOutput);

  // A valid video format with an explicit playback error is not media proof.
  const failed = run('video_width=1280 video_height=720 audio_track_count=1 failure_stage=media_source');
  assert.match(failed.collectionOutput, /media_verified=0/);
  assert.match(failed.playerOutput, /playback_verified=0/);
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
console.log('Native collection media format gate agrees with production player gate');
