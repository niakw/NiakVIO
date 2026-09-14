#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { guardedFetch } = require('./network_guard.cjs');
const { probeDirectMedia } = require('./direct_media_probe.cjs');

function safe(result) {
  const keep = [
    'playable', 'inconclusive', 'kind', 'status', 'hls_master',
    'hls_variant_playable', 'hls_segment_playable',
    'hls_external_audio_count', 'hls_audio_playable',
    'media_duration_seconds', 'media_duration_complete',
  ];
  const out = {};
  for (const key of keep) if (result && result[key] !== undefined) out[key] = result[key];
  return out;
}

(async () => {
  const input = process.argv[2];
  if (!input) throw new Error('usage: direct_media_probe_cli.cjs <stream-json>');
  const stream = JSON.parse(fs.readFileSync(path.resolve(input), 'utf8'));
  const result = await probeDirectMedia(stream, {
    guardedFetch,
    fetchImpl: globalThis.fetch,
    timeoutMs: 18000,
    maxRedirects: 5,
  });
  process.stdout.write(`DIRECT_MEDIA_PROOF=${JSON.stringify(safe(result))}\n`);
  process.exit(result?.playable ? 0 : (result?.inconclusive ? 3 : 2));
})().catch((error) => {
  process.stderr.write(`DIRECT_MEDIA_PROOF_ERROR=${String(error?.name || error?.code || 'Error')}\n`);
  process.exit(4);
});
