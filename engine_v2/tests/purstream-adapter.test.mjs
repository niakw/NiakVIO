import assert from "node:assert/strict";
import { ResolverCore } from "../src/resolver-core.mjs";
import { createPurstreamAdapter, derivePurstreamEndpoint, strictIdentityScore } from "../providers/purstream.mjs";

const calls = [];
const fetchImpl = async (url, options = {}) => {
  const href = String(url);
  calls.push({ href, options });
  if (href === "https://purstream.art/") {
    return new Response("<html>Purstream</html>", { status: 200, headers: { "content-type": "text/html" } });
  }
  if (href.includes("/search-bar/search/Interstellar")) {
    return json({ data: { items: { movies: { items: [
      { id: 1, title: "Interstellar Something Else", type: "movie", release_date: "2014-01-01" },
      { id: 42, title: "Interstellar", type: "movie", release_date: "2014-11-05" },
    ] } } } });
  }
  if (href.endsWith("/media/42/sheet")) {
    return json({ data: { items: { urls: [
      { name: "1080p VF", url: "https://cdn.example/interstellar.m3u8" },
      { name: "embed", url: "https://embed.example/watch/42" },
    ] } } });
  }
  if (href.includes("/search-bar/search/Breaking%20Bad")) {
    return json({ data: { items: { movies: { items: [
      { id: 66, title: "Breaking Bad", type: "movie", release_date: "2008-01-01" },
      { id: 77, title: "Breaking Bad", type: "tv", first_air_date: "2008-01-20" },
    ] } } } });
  }
  if (href.includes("/stream/77/episode?season=1&episode=1")) {
    return json({ data: { items: { sources: [
      { source_name: "1080p VF", stream_url: "https://cdn.example/breaking-bad-s01e01.m3u8", format: "m3u8" },
    ] } } });
  }
  throw new Error(`unexpected Purstream test URL: ${href}`);
};

const passValidator = async (streams) => ({
  playable: streams.length > 0,
  playableCount: streams.length,
  results: streams.map((candidate) => ({ candidate, validation: { playable: true, status: 206, finalUrl: candidate.url, reason: null } })),
});
const core = new ResolverCore({ mediaValidator: passValidator });
const adapter = createPurstreamAdapter({ fetchImpl, terminalUrl: "https://purstream.art/", domainSource: "test" });

const movie = await core.resolve({
  provider: { id: "purstream" },
  adapter,
  request: { tmdbId: "157336", mediaType: "movie", title: "Interstellar", year: 2014, device: "desktop" },
  fixtureId: "interstellar",
  clientRef: "desktop-test",
});
assert.equal(movie.repair.failureClass, "healthy");
assert.equal(movie.streams.length, 1);
assert.equal(movie.streams[0].url, "https://cdn.example/interstellar.m3u8");
assert.equal(movie.streams[0].language, "VF");
assert.equal(movie.evidence.stages.identity.selectedId, undefined); // evidence intentionally stores only generic proof fields
assert.equal(movie.evidence.stages.identity.matched, true);
assert.equal(movie.evidence.stages.validation.playable, true);

const tv = await core.resolve({
  provider: { id: "purstream" },
  adapter,
  request: { tmdbId: "1396", mediaType: "series", title: "Breaking Bad", year: 2008, season: 1, episode: 1, device: "tv" },
  fixtureId: "breaking-bad-s01e01",
  clientRef: "tv-test",
});
assert.equal(tv.request.mediaType, "tv");
assert.equal(tv.repair.failureClass, "healthy");
assert.equal(tv.streams.length, 1);
assert.equal(tv.streams[0].url, "https://cdn.example/breaking-bad-s01e01.m3u8");
assert.equal(tv.evidence.stages.episode.found, true);
assert.equal(tv.evidence.stages.validation.playable, true);

const apiCall = calls.find((call) => call.href.includes("/search-bar/search/Breaking%20Bad"));
assert.equal(apiCall.options.headers.Referer, "https://purstream.art/");
assert.equal(apiCall.options.headers.Origin, "https://purstream.art");

assert.deepEqual(derivePurstreamEndpoint("https://purstream.club/"), {
  suffix: "club",
  site: "https://purstream.club/",
  api: "https://api.purstream.club/api/v1",
  referer: "https://purstream.club/",
  origin: "https://purstream.club",
});
assert.throws(() => createPurstreamAdapter({ terminalUrl: "https://purstream.wiki/" }), /hub is not a terminal/);
assert.equal(strictIdentityScore({ id: 1, title: "Breaking Bad", type: "movie", year: 2008 }, { title: "Breaking Bad", year: 2008 }, "tv"), 0);
assert.ok(strictIdentityScore({ id: 1, title: "Breaking Bad", type: "tv", year: 2008 }, { title: "Breaking Bad", year: 2008 }, "tv") >= 100);

console.log("engine v2 Purstream adapter tests passed");

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { "content-type": "application/json" } });
}
