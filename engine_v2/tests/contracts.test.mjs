import assert from "node:assert/strict";
import {
  adaptRequestForDevice,
  normalizeMediaType,
  normalizeResolveRequest,
  normalizeStreamCandidate,
  normalizeProviderSpec,
} from "../src/contracts.mjs";

assert.equal(normalizeMediaType("series"), "tv");
assert.equal(normalizeMediaType("show"), "tv");
assert.equal(normalizeMediaType("other"), "tv");
assert.equal(normalizeMediaType("anime"), "anime");

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

const interstellar = adaptRequestForDevice({
  tmdbId: "157336",
  mediaType: "movie",
  title: "Interstellar",
}, "tv");
assert.deepEqual(interstellar.args, ["157336", "movie", undefined, undefined]);

const stream = normalizeStreamCandidate({
  title: "VF 1080p",
  url: "https://media.example/stream.m3u8",
  language: "fr",
  headers: { Referer: "https://player.example/", Origin: "https://player.example" },
  subtitles: [{ url: "https://sub.example/fr.vtt", language: "fr" }],
}, { providerId: "example" });
assert.equal(stream.provider, "example");
assert.equal(stream.headers.Referer, "https://player.example/");
assert.equal(stream.subtitles.length, 1);

const spec = normalizeProviderSpec({
  id: "Example",
  name: "Example",
  supportedTypes: ["movie", "series"],
  languages: ["fr", "FR"],
  sources: [{ upstream: "gowaru", path: "providers/example.js" }],
  strategies: { search: { kind: "html" }, media: { kind: "hls" } },
});
assert.deepEqual(spec.supportedTypes, ["movie", "tv"]);
assert.deepEqual(spec.languages, ["fr"]);

assert.throws(() => normalizeResolveRequest({ mediaType: "tv", title: "Breaking Bad" }), /season and episode/);
assert.throws(() => normalizeMediaType("documentary"), /unsupported mediaType/);

console.log("engine v2 canonical contract tests passed");
