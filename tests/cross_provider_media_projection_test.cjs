'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync(require.resolve('../scripts/health_check.mjs'), 'utf8');
const expression = source.match(/host_results: (probes\s*\.filter[\s\S]*?)\,\n\s*response_categories:/);
assert.ok(expression, 'test the production probe projection');
const project = new Function('probes', 'return (' + expression[1] + ');');
const facts = { host: 'media.example', category: 'playable', http_status: 206, kind: 'mp4',
  playback_verified: true, payload_verified: true, direct_signature_verified: true,
  content_identity_status: 'match', content_identity_reason: 'fixture_duration_match',
  duration_identity_mismatch: false, media_duration_seconds: 1440,
  expected_duration_seconds: 1440, duration_identity_authoritative: true,
  bytes_sampled: 32768, short_vod_preview: false,
  variant_reachable: null, segment_reachable: null,
  audio_manifest_reachable: null, audio_segment_reachable: null,
  url: 'PRIVATE_ADDRESS', headers: { Cookie: 'PRIVATE_COOKIE' }, body: 'PRIVATE_BODY' };
const actual = project([facts])[0];
for (const key of ['media_duration_seconds', 'expected_duration_seconds', 'bytes_sampled',
  'direct_signature_verified', 'duration_identity_authoritative', 'short_vod_preview']) {
  assert.equal(actual[key], facts[key]);
}
assert.ok(!JSON.stringify(actual).includes('PRIVATE'));
const hls = project([{ ...facts, kind: 'hls', variant_reachable: true, segment_reachable: true,
  audio_manifest_reachable: true, audio_segment_reachable: true }])[0];
for (const key of ['variant_reachable', 'segment_reachable', 'audio_manifest_reachable', 'audio_segment_reachable']) {
  assert.equal(hls[key], true);
}
assert.equal(project([{ ...facts, media_duration_seconds: NaN }])[0].media_duration_seconds, null);
console.log('Cross-provider media projection preserves measured duration/segments without private inputs');
