import assert from "node:assert/strict";
import {
  adaptRequestForDevice,
  normalizeMediaType,
  normalizeProviderMediaType,
  normalizeResolveRequest,
  normalizeStreamCandidate,
  normalizeProviderSpec,
} from "../src/contracts.mjs";

// External/client aliases are accepted only at the request boundary.
assert.equal(normalizeMediaType("series"), "tv");
assert.equal(normalizeMediaType("show"), "tv");
assert.equal(normalizeMediaType("other"), "tv");
assert.equal(normalizeMediaType("anime"), "anime");

// Provider/manifests use one global vocabulary only.
assert.equal(normalizeProviderMediaType("movie"), "movie");
assert.equal(normalizeProviderMediaType("tv"), "tv");
assert.equal(normalizeProviderMediaType("anime"), "anime");
for (const alias of ["series", "serie", "show", "other"]) {
  assert.throws(() => normalizeProviderMediaType(alias), /provider media type must be canonical/);
}

const breakingBad = normalizeResolveRequest({
  tmdbId: "1396",
  mediaType: "series",
  title: "Breaking Bad",
  season: 1,
  episode: 1,
  device: "desktop",
});
assert.equal(breakingBad.mediaType, "tv");
assert.equal(breakingBad.season, 1);
assert.equal(breakingBad.episode, 1);

for (const device of ["mobile", "desktop", "tv"]) {
  const adapted = adaptRequestForDevice(breakingBad, device);
  assert.equal(adapted.call, "getStreams");
  assert.deepEqual(adapted.args, ["1396", "tv", 1, 1]);
  assert.equal(adapted.canonical.device, device);
}

const anime = adaptRequestForDevice({
  tmdbId: "95479",
  mediaType: "anime",
  title: "Jujutsu Kaisen",
  season: 1,
  episode: 1,
}, "mobile");
assert.deepEqual(anime.args, ["95479", "anime", 1, 1]);

const interstellar = adaptRequestForDevice({
  tmdbId: "157336",
  mediaType: "movie",
  title: "Interstellar",
}, "tv");
assert.deepEqual(interstellar.args, ["157336", "movie", undefined, undefined]);

const stream = normalizeStreamCandidate({
  title: "VF 4K",
  url: "https://media.example/stream.m3u8?token=A%2FB&expires=1785885619&sig=x%2By%3D",
  quality: "4K",
  language: "fr",
  behaviorHints: { proxyHeaders: { request: {
    Referer: "https://proxy-player.example/",
    Cookie: "session=proxy",
    Authorization: "Bearer proxy",
  } } },
  requestHeaders: {
    origin: "https://request.example",
    cookie: "session=request",
  },
  headers: {
    referer: "https://player.example/",
    Origin: "https://player.example",
    COOKIE: "session=explicit",
  },
  subtitles: [{
    url: "https://sub.example/fr.vtt?token=sub%2F1",
    language: "fr",
    behaviorHints: { proxyHeaders: { request: { Referer: "https://subtitle.example/" } } },
  }],
}, { providerId: "example" });
assert.equal(stream.provider, "example");
assert.equal(stream.url, "https://media.example/stream.m3u8?token=A%2FB&expires=1785885619&sig=x%2By%3D");
assert.equal(stream.quality, "2160p");
assert.equal(stream.headers.referer, "https://player.example/");
assert.equal(stream.headers.Origin, "https://player.example");
assert.equal(stream.headers.COOKIE, "session=explicit");
assert.equal(stream.headers.Authorization, "Bearer proxy");
assert.equal(Object.keys(stream.headers).filter((key) => key.toLowerCase() === "referer").length, 1);
assert.equal(Object.keys(stream.headers).filter((key) => key.toLowerCase() === "cookie").length, 1);
assert.equal(stream.subtitles.length, 1);
assert.equal(stream.subtitles[0].url, "https://sub.example/fr.vtt?token=sub%2F1");
assert.equal(stream.subtitles[0].headers.Referer, "https://subtitle.example/");

const nested = normalizeStreamCandidate({
  url: {
    url: "https://signed.example/media?X-Amz-Signature=a%2Bb%2Fc&X-Amz-Expires=600",
    requestHeaders: { Referer: "https://nested.example/" },
    headers: { Cookie: "nested=1" },
  },
  requestHeaders: { Origin: "https://outer.example" },
}, { providerId: "nested" });
assert.equal(nested.url, "https://signed.example/media?X-Amz-Signature=a%2Bb%2Fc&X-Amz-Expires=600");
assert.deepEqual(nested.headers, {
  Referer: "https://nested.example/",
  Cookie: "nested=1",
  Origin: "https://outer.example",
});

// 1080p is a resolution only. Do not invent Blu-ray provenance from it.
const plain1080 = normalizeStreamCandidate({ url: "https://media.example/a.mp4", quality: "1080p" });
assert.equal(plain1080.quality, "1080p");
assert.doesNotMatch(JSON.stringify(plain1080), /blu[- ]?ray/i);

const spec = normalizeProviderSpec({
  id: "Example",
  name: "Example",
  supportedTypes: ["movie", "tv", "anime"],
  languages: ["fr", "FR"],
  sources: [{ upstream: "gowaru", path: "providers/example.js" }],
  strategies: { search: { kind: "html" }, media: { kind: "hls" } },
});
assert.deepEqual(spec.supportedTypes, ["movie", "tv", "anime"]);
assert.deepEqual(spec.languages, ["fr"]);

assert.throws(() => normalizeProviderSpec({
  id: "LegacyAlias",
  name: "Legacy Alias",
  supportedTypes: ["movie", "series"],
  sources: [{ upstream: "test", path: "providers/test.js" }],
  strategies: {},
}), /non-canonical provider type: series/);
assert.throws(() => normalizeResolveRequest({ mediaType: "tv", title: "Breaking Bad" }), /season and episode/);
assert.throws(() => normalizeMediaType("documentary"), /unsupported mediaType/);

console.log("engine v2 canonical contract tests passed");
