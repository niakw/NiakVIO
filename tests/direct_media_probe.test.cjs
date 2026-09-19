'use strict';
const assert = require('node:assert/strict');
const { parseHls, probeDirectMedia } = require('../scripts/direct_media_probe.cjs');

function response(url, body, type = 'application/vnd.apple.mpegurl', status = 200) {
  return new Response(body, { status, headers: { 'content-type': type } });
}

function fakeGuard(map) {
  return async function guardedFetch(_fetchImpl, raw) {
    const url = String(raw);
    const item = map[url];
    if (item instanceof Error) throw item;
    if (!item) return response(url, 'not found', 'text/plain', 404);
    const result = response(url, item.body, item.type, item.status || 200);
    Object.defineProperty(result, 'url', { value: url });
    return result;
  };
}

(async () => {
  const masterUrl = 'https://media.test/master.m3u8';
  const videoUrl = 'https://media.test/video.m3u8';
  const audioUrl = 'https://media.test/audio.m3u8';
  const videoSeg = 'https://media.test/video.ts';
  const audioSeg = 'https://media.test/audio.aac';
  const master = '#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="fr",URI="audio.m3u8"\n#EXT-X-STREAM-INF:BANDWIDTH=2000000,AUDIO="aud"\nvideo.m3u8\n';
  const video = '#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nvideo.ts\n#EXT-X-ENDLIST\n';
  const audio = '#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\naudio.aac\n#EXT-X-ENDLIST\n';
  const parsed = parseHls(master, masterUrl);
  assert.equal(parsed.valid, true);
  assert.deepEqual(parsed.variants, [videoUrl]);
  assert.deepEqual(parsed.audio, [audioUrl]);
  assert.equal(parseHls(video, videoUrl).durationSeconds, 6);

  const guard = fakeGuard({
    [masterUrl]: { body: master },
    [videoUrl]: { body: video },
    [audioUrl]: { body: audio },
    [videoSeg]: { body: Buffer.from([0x47, 1, 2, 3]), type: 'video/mp2t' },
    [audioSeg]: { body: Buffer.from([1, 2, 3, 4]), type: 'audio/aac' },
  });
  const ok = await probeDirectMedia({ url: masterUrl, headers: {} }, { guardedFetch: guard, fetchImpl: async () => {}, timeoutMs: 1000 });
  assert.equal(ok.playable, true, JSON.stringify(ok));
  assert.equal(ok.kind, 'hls');
  assert.equal(ok.hls_external_audio_count, 1);
  assert.equal(ok.hls_audio_playable, true);
  assert.equal(ok.hls_variant_playable, true);
  assert.equal(ok.media_duration_seconds, 6);

  const headerOnly = await probeDirectMedia(
    { url: masterUrl, headers: {} },
    { guardedFetch: fakeGuard({ [masterUrl]: { body: '#EXTM3U\n' } }), fetchImpl: async () => {}, timeoutMs: 1000 },
  );
  assert.equal(headerOnly.playable, false);
  assert.equal(headerOnly.inconclusive, false);
  assert.equal(headerOnly.kind, 'hls_invalid_structure');

  const brokenAudio = await probeDirectMedia(
    { url: masterUrl, headers: {} },
    { guardedFetch: fakeGuard({
      [masterUrl]: { body: master },
      [videoUrl]: { body: video },
      [videoSeg]: { body: Buffer.from([0x47, 1, 2]), type: 'video/mp2t' },
      [audioUrl]: { body: '<html>bad audio</html>', type: 'text/html' },
    }), fetchImpl: async () => {}, timeoutMs: 1000 },
  );
  assert.equal(brokenAudio.playable, false);
  assert.equal(brokenAudio.hls_audio_playable, false);

  const timeout = new Error('network timeout');
  timeout.name = 'AbortError';
  const uncertain = await probeDirectMedia(
    { url: masterUrl, headers: {} },
    { guardedFetch: fakeGuard({ [masterUrl]: timeout }), fetchImpl: async () => {}, timeoutMs: 1000 },
  );
  assert.equal(uncertain.playable, false);
  assert.equal(uncertain.inconclusive, true);

  console.log('strict direct media HLS graph tests passed');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
