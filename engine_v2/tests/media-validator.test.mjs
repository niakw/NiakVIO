import assert from "node:assert/strict";
import { validateMediaCandidate, validateMediaCandidates } from "../src/media-validator.mjs";

const requiredHeaders = {
  Referer: "https://player.example/watch",
  Origin: "https://player.example",
  Cookie: "session=a%2Fb",
  Authorization: "Bearer signed-token",
};

function response(body, status = 200, contentType = "application/vnd.apple.mpegurl") {
  return new Response(body, { status, headers: { "content-type": contentType } });
}

function binary(bytes = [0x47, 0x40, 0x00, 0x10]) {
  return response(new Uint8Array(bytes), 200, "application/octet-stream");
}

function assertPlaybackHeaders(headers, label) {
  const lower = Object.fromEntries(Object.entries(headers || {}).map(([key, value]) => [key.toLowerCase(), value]));
  for (const [key, value] of Object.entries(requiredHeaders)) {
    assert.equal(lower[key.toLowerCase()], value, `${label}: missing ${key}`);
  }
}

const masterUrl = "https://cdn.example/master.m3u8?token=master%2F1&sig=a%2Bb%3D";
const variant2160 = "https://cdn.example/v2160.m3u8?token=hi%2F1&sig=x%2By";
const variant1080 = "https://cdn.example/v1080.m3u8?token=ok%2F1&sig=q%2Br";
const keyUrl = "https://keys.example/aes.key?token=k%2F1&sig=k%2Bk";
const mapUrl = "https://cdn.example/init.mp4?token=map%2F1";
const segmentUrl = "https://segments.example/seg-001.m4s?token=s%2F1&sig=s%2Bs";
const audioUrl = "https://cdn.example/audio-fr.m3u8?token=audio%2F1";
const audioSegment = "https://cdn.example/audio-001.aac?token=aseg%2F1";
const subtitleUrl = "https://cdn.example/sub-fr.m3u8?token=sub%2F1";

const master = `#EXTM3U
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="fr",NAME="Français",DEFAULT=YES,URI="${audioUrl}"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="fr",NAME="Français",URI="${subtitleUrl}"
#EXT-X-STREAM-INF:BANDWIDTH=16000000,RESOLUTION=3840x2160,CODECS="hvc1.1.6.L120",AUDIO="aud",SUBTITLES="subs"
${variant2160}
#EXT-X-STREAM-INF:BANDWIDTH=6500000,RESOLUTION=1920x1080,CODECS="avc1.640028",AUDIO="aud",SUBTITLES="subs"
${variant1080}
`;
const broken2160 = `#EXTM3U
#EXT-X-TARGETDURATION:6
#EXTINF:6,
https://segments.example/2160.ts?token=broken%2F1
`;
const good1080 = `#EXTM3U
#EXT-X-TARGETDURATION:6
#EXT-X-KEY:METHOD=AES-128,URI="${keyUrl}"
#EXT-X-MAP:URI="init.mp4?token=map%2F1"
#EXTINF:6,
${segmentUrl}
#EXT-X-ENDLIST
`;
const audio = `#EXTM3U
#EXT-X-TARGETDURATION:6
#EXTINF:6,
${audioSegment}
#EXT-X-ENDLIST
`;
const subtitle = `#EXTM3U
#EXT-X-TARGETDURATION:6
#EXTINF:6,
sub-001.vtt?token=vtt%2F1
#EXT-X-ENDLIST
`;

const trace = [];
const chainFetch = async (input, init = {}) => {
  const url = String(input);
  trace.push({ url, headers: { ...(init.headers || {}) } });
  assertPlaybackHeaders(init.headers, url);
  if (url === masterUrl) return response(master);
  if (url === variant2160) return response(broken2160);
  if (url === "https://segments.example/2160.ts?token=broken%2F1") return response("denied", 403, "text/plain");
  if (url === variant1080) return response(good1080);
  if (url === keyUrl) return binary(new Array(16).fill(7));
  if (url === mapUrl) return binary([0, 0, 0, 24, 102, 116, 121, 112]);
  if (url === segmentUrl) return binary();
  if (url === audioUrl) return response(audio);
  if (url === audioSegment) return binary([0xff, 0xf1, 0x50, 0x80]);
  if (url === subtitleUrl) return response(subtitle);
  if (url === "https://cdn.example/sub-001.vtt?token=vtt%2F1") return response("WEBVTT\n", 200, "text/vtt");
  throw new Error(`unexpected URL ${url}`);
};

const recoveredFallback = await validateMediaCandidate({
  url: masterUrl,
  type: "hls",
  quality: "4K",
  headers: requiredHeaders,
}, { fetchImpl: chainFetch, timeoutMs: 1500, maxHlsVariants: 4 });
assert.equal(recoveredFallback.playable, true, recoveredFallback.reason);
assert.equal(recoveredFallback.effectiveHeight, 1080);
assert.match(String(recoveredFallback.codecs), /avc1/i);
assert.equal(recoveredFallback.fallbackCount, 1);
assert.equal(recoveredFallback.chain.segment, undefined);
assert.equal(recoveredFallback.child.segment.url, segmentUrl);
assert.equal(recoveredFallback.child.key.url, keyUrl);
assert.equal(recoveredFallback.child.map.url, mapUrl);
assert.equal(recoveredFallback.chain.audio.playable, true);
assert.equal(recoveredFallback.chain.subtitles.playable, true);
for (const exact of [masterUrl, variant2160, variant1080, keyUrl, mapUrl, segmentUrl, audioUrl, audioSegment, subtitleUrl]) {
  assert(trace.some((row) => row.url === exact), `signed/explicit URL changed or was not fetched: ${exact}`);
}

async function validateSingleResourceFailure(tag, body, failingUrl) {
  const playlistUrl = `https://failure.example/${tag}.m3u8?token=${tag}%2F1`;
  const seen = [];
  const fetchImpl = async (input, init = {}) => {
    const url = String(input);
    seen.push(url);
    assertPlaybackHeaders(init.headers, `${tag}:${url}`);
    if (url === playlistUrl) return response(body);
    if (url === failingUrl) return response("forbidden", 403, "text/plain");
    if (/\.key(?:\?|$)/.test(url)) return binary(new Array(16).fill(1));
    if (/init\.mp4/.test(url)) return binary([0, 0, 0, 20]);
    return binary();
  };
  const value = await validateMediaCandidate({ url: playlistUrl, type: "hls", headers: requiredHeaders }, { fetchImpl, timeoutMs: 1500 });
  assert.equal(value.playable, false, `${tag} unexpectedly playable`);
  assert.equal(value.reason, `hls-${tag}-http-403`);
  assert(seen.includes(failingUrl));
}

await validateSingleResourceFailure(
  "key",
  `#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="https://failure.example/denied.key?token=k%2F2"\n#EXTINF:6,\nhttps://failure.example/seg.ts\n`,
  "https://failure.example/denied.key?token=k%2F2",
);
await validateSingleResourceFailure(
  "map",
  `#EXTM3U\n#EXT-X-MAP:URI="https://failure.example/init.mp4?token=m%2F2"\n#EXTINF:6,\nhttps://failure.example/seg.m4s\n`,
  "https://failure.example/init.mp4?token=m%2F2",
);
await validateSingleResourceFailure(
  "segment",
  `#EXTM3U\n#EXTINF:6,\nhttps://failure.example/denied.ts?token=s%2F2\n`,
  "https://failure.example/denied.ts?token=s%2F2",
);

const opaque = await validateMediaCandidate({ url: "https://opaque.example/play?id=1", headers: requiredHeaders }, {
  timeoutMs: 1500,
  fetchImpl: async (input, init = {}) => {
    assertPlaybackHeaders(init.headers, "opaque");
    const url = String(input);
    if (url.includes("play?id=1")) return response("#EXTM3U\n#EXTINF:6,\nseg.ts\n");
    if (url === "https://opaque.example/seg.ts") return binary();
    throw new Error(url);
  },
});
assert.equal(opaque.playable, true);
assert.equal(opaque.format, "hls");

const html = await validateMediaCandidate({ url: "https://opaque.example/fake.m3u8", headers: requiredHeaders }, {
  timeoutMs: 1500,
  fetchImpl: async (_input, init = {}) => {
    assertPlaybackHeaders(init.headers, "html");
    return response("<!doctype html><html>blocked</html>", 200, "text/html");
  },
});
assert.equal(html.playable, false);
assert.equal(html.reason, "hls-invalid-body");

const rankingFetch = async (input) => {
  const url = String(input);
  if (url === "https://rank.example/flaky.m3u8") return response(`#EXTM3U\n#EXT-X-STREAM-INF:RESOLUTION=3840x2160,CODECS="hvc1.1.6.L120"\nhi.m3u8\n#EXT-X-STREAM-INF:RESOLUTION=3840x2160,CODECS="hvc1.1.6.L120"\nbackup.m3u8\n`);
  if (url === "https://rank.example/hi.m3u8") return response("no", 403, "text/plain");
  if (url === "https://rank.example/backup.m3u8") return response("#EXTM3U\n#EXTINF:6,\nbackup.ts\n");
  if (url === "https://rank.example/backup.ts") return binary();
  if (url === "https://rank.example/stable.m3u8") return response(`#EXTM3U\n#EXT-X-STREAM-INF:RESOLUTION=1920x1080,CODECS="avc1.640028"\nstable-child.m3u8\n`);
  if (url === "https://rank.example/stable-child.m3u8") return response("#EXTM3U\n#EXTINF:6,\nstable.ts\n");
  if (url === "https://rank.example/stable.ts") return binary();
  if (url === "https://rank.example/healthy4k.m3u8") return response(`#EXTM3U\n#EXT-X-STREAM-INF:RESOLUTION=3840x2160,CODECS="hvc1.1.6.L120"\nhealthy4k-child.m3u8\n`);
  if (url === "https://rank.example/healthy4k-child.m3u8") return response("#EXTM3U\n#EXTINF:6,\nhealthy4k.ts\n");
  if (url === "https://rank.example/healthy4k.ts") return binary();
  throw new Error(url);
};
const ranked = await validateMediaCandidates([
  { url: "https://rank.example/flaky.m3u8", type: "hls", quality: "2160p" },
  { url: "https://rank.example/stable.m3u8", type: "hls", quality: "1080p" },
], { fetchImpl: rankingFetch, timeoutMs: 1500, maxCandidates: 3 });
assert.equal(ranked.rankedResults[0].candidate.url, "https://rank.example/stable.m3u8");
assert(ranked.rankedResults[0].rankScore > ranked.rankedResults[1].rankScore);

const healthy4k = await validateMediaCandidates([
  { url: "https://rank.example/stable.m3u8", type: "hls", quality: "1080p" },
  { url: "https://rank.example/healthy4k.m3u8", type: "hls", quality: "2160p" },
], { fetchImpl: rankingFetch, timeoutMs: 1500 });
assert.equal(healthy4k.rankedResults[0].candidate.url, "https://rank.example/healthy4k.m3u8");

console.log("engine v2 deep media validator tests passed");

const { ResolverCore } = await import("../src/resolver-core.mjs");
const resolver = new ResolverCore({
  mediaValidator: async (candidates) => ({
    playable: true,
    playableCount: 2,
    results: candidates.map((candidate) => ({ candidate, validation: { playable: true, status: 200 } })),
    rankedResults: [
      { candidate: candidates[1], validation: { playable: true, status: 200 }, rankScore: 11380 },
      { candidate: candidates[0], validation: { playable: true, status: 200 }, rankScore: 10360 },
    ],
  }),
});
const resolved = await resolver.resolve({
  provider: { id: "rank-test" },
  request: { title: "Ranking", mediaType: "movie" },
  adapter: {
    pipeline: ["media", "validation"],
    media: async () => [
      { url: "https://rank.example/flaky.m3u8", quality: "2160p" },
      { url: "https://rank.example/stable.m3u8", quality: "1080p" },
    ],
  },
});
assert.equal(resolved.streams[0].url, "https://rank.example/stable.m3u8");
