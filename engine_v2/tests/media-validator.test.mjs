import assert from "node:assert/strict";
import { validateMediaCandidate, validateMediaCandidates } from "../src/media-validator.mjs";

const calls = [];
const fetchImpl = async (url, options = {}) => {
  calls.push({ url: String(url), headers: options.headers ?? {} });
  if (String(url) === "https://cdn.example/master.m3u8") {
    return new Response("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\nvariant.m3u8\n", {
      status: 200,
      headers: { "content-type": "application/vnd.apple.mpegurl" },
    });
  }
  if (String(url) === "https://cdn.example/variant.m3u8") {
    return new Response("#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment0.ts\n", {
      status: 200,
      headers: { "content-type": "application/vnd.apple.mpegurl" },
    });
  }
  if (String(url) === "https://cdn.example/fake.m3u8") {
    return new Response("<!doctype html><html><body>blocked</body></html>", {
      status: 200,
      headers: { "content-type": "text/html" },
    });
  }
  if (String(url) === "https://cdn.example/movie.mp4") {
    return new Response(new Uint8Array([0, 0, 0, 24, 102, 116, 121, 112, 105, 115, 111, 109]), {
      status: 206,
      headers: { "content-type": "video/mp4", "content-length": "12" },
    });
  }
  if (String(url) === "https://cdn.example/blocked.m3u8") {
    return new Response("Forbidden", { status: 403, headers: { "content-type": "text/plain" } });
  }
  throw new Error(`unexpected url ${url}`);
};

const hls = await validateMediaCandidate({
  url: "https://cdn.example/master.m3u8",
  headers: { Referer: "https://player.example/", Origin: "https://player.example" },
}, { fetchImpl });
assert.equal(hls.playable, true);
assert.equal(hls.status, 200);
assert.equal(hls.child.playable, true);
assert.equal(calls[0].headers.Referer, "https://player.example/");
assert.equal(calls[0].headers.Origin, "https://player.example");
assert.equal(calls[0].headers.Range, "bytes=0-262143");

const fake = await validateMediaCandidate({ url: "https://cdn.example/fake.m3u8" }, { fetchImpl });
assert.equal(fake.playable, false);
assert.equal(fake.reason, "invalid-hls-body");

const mp4 = await validateMediaCandidate({ url: "https://cdn.example/movie.mp4" }, { fetchImpl });
assert.equal(mp4.playable, true);
assert.equal(mp4.status, 206);

const blocked = await validateMediaCandidate({ url: "https://cdn.example/blocked.m3u8" }, { fetchImpl });
assert.equal(blocked.playable, false);
assert.equal(blocked.reason, "http-403");

const batch = await validateMediaCandidates([
  { url: "https://cdn.example/blocked.m3u8" },
  { url: "https://cdn.example/movie.mp4" },
], { fetchImpl, maxCandidates: 2 });
assert.equal(batch.playable, true);
assert.equal(batch.playableCount, 1);
assert.equal(batch.results.length, 2);

console.log("engine v2 media validator tests passed");
