import assert from "node:assert/strict";
import { ResolverCore } from "../src/resolver-core.mjs";

const passValidator = async (streams) => ({
  playable: streams.length > 0,
  playableCount: streams.length,
  results: streams.map((candidate) => ({
    candidate,
    validation: { playable: true, status: 206, finalUrl: candidate.url, reason: null },
  })),
});
const core = new ResolverCore({ maxRepairHypotheses: 2, mediaValidator: passValidator });

const seriesAdapter = {
  async discover() { return { ok: true, host: "example.test", url: "https://example.test/" }; },
  async homepage() { return { ok: true, status: 200 }; },
  async search(ctx) {
    assert.equal(ctx.request.mediaType, "tv");
    assert.equal(ctx.request.season, 1);
    assert.equal(ctx.request.episode, 1);
    return { ok: true, status: 200, matches: [{ id: "bb" }] };
  },
  async identity() { return { ok: true, matched: true }; },
  async detail() { return { ok: true, found: true }; },
  async episode(ctx) { return { ok: true, found: true, season: ctx.request.season, episode: ctx.request.episode }; },
  async player() { return { ok: true, found: true, host: "player.example.test" }; },
  async media() {
    return { ok: true, streams: [{ title: "VF", url: "https://cdn.example.test/master.m3u8", language: "fr" }] };
  },
};

const result = await core.resolve({
  provider: { id: "example" },
  adapter: seriesAdapter,
  request: { tmdbId: "1396", mediaType: "series", title: "Breaking Bad", season: 1, episode: 1, device: "tv" },
  fixtureId: "breaking-bad-s01e01",
  clientRef: "tv-test",
});
assert.equal(result.request.mediaType, "tv");
assert.equal(result.streams.length, 1);
assert.equal(result.streams[0].playable, true);
assert.equal(result.evidence.stages.episode.found, true);
assert.equal(result.evidence.stages.validation.playable, true);
assert.equal(result.evidence.playableStreams, 1);
assert.equal(result.repair.failureClass, "healthy");

const directApi = await core.resolve({
  provider: { id: "direct" },
  adapter: {
    pipeline: ["media"],
    async media() { return { streams: [{ title: "1080p", url: "https://cdn.example/movie.mp4" }] }; },
  },
  request: { tmdbId: "157336", mediaType: "movie", title: "Interstellar", device: "desktop" },
});
assert.equal(directApi.streams.length, 1);
assert.equal(directApi.evidence.stages.search.skipped, true);
assert.equal(directApi.evidence.stages.validation.playable, true);
assert.equal(directApi.repair.failureClass, "healthy");

const failingCore = new ResolverCore({
  mediaValidator: async (streams) => ({
    playable: false,
    playableCount: 0,
    results: streams.map((candidate) => ({ candidate, validation: { playable: false, status: 403, reason: "http-403" } })),
  }),
});
const media403 = await failingCore.resolve({
  provider: { id: "blocked" },
  adapter: {
    pipeline: ["media"],
    async media() { return { streams: [{ title: "x", url: "https://cdn.example/x.m3u8", headers: { Referer: "https://player.example/" } }] }; },
  },
  request: { tmdbId: "157336", mediaType: "movie", title: "Interstellar", device: "tv" },
});
assert.equal(media403.evidence.playableStreams, 0);
assert.equal(media403.repair.failureClass, "playback_context_gap");
assert.equal(media403.repair.hypotheses[0].id, "preserve-playback-context");

const searchFailure = await core.resolve({
  provider: { id: "broken" },
  adapter: {
    async homepage() { return { ok: true, status: 200 }; },
    async search() { return { ok: true, status: 200, matches: [] }; },
  },
  request: { tmdbId: "157336", mediaType: "movie", title: "Interstellar", device: "worker" },
});
assert.equal(searchFailure.repair.failureClass, "search_gap");
assert.ok(searchFailure.repair.hypotheses.length <= 2);

// A master HLS stream's proven playable variant, not its original 4K
// advertising nor its pre-probe title, must determine the visible quality.
const validatedHls = new ResolverCore({
  mediaValidator: async (streams) => ({
    playable: true, playableCount: 1,
    results: streams.map((candidate) => ({
      candidate,
      validation: {
        playable: true, status: 200, kind: "hls",
        effectiveHeight: 1080,
        chain: { kind: "master", selectedVariant: { height: 1080 } },
      },
    })),
  }),
});
const measured = await validatedHls.resolve({
  provider: { id: "quality-test", name: "Quality Source" },
  request: { tmdbId: "157336", mediaType: "movie", title: "Interstellar" },
  adapter: {
    pipeline: ["media", "validation"],
    async media() {
      return { streams: [{
        url: "https://cdn.example/master.m3u8?sig=unchanged",
        title: "Quality Source - 4K", quality: "2160p",
        resolution: "3840x2160", headers: { Referer: "https://origin.example/" },
      }] };
    },
  },
});
assert.equal(measured.streams[0].quality, "1080p");
assert.match(measured.streams[0].title, /1080p/);
assert.doesNotMatch(measured.streams[0].title, /4K/);
assert(measured.streams[0].badgeIds.includes("1080p-full-hd"));
assert(!measured.streams[0].badgeIds.includes("4k-ultra-hd"));
assert.equal(measured.streams[0].declaredQuality, "2160p");
assert.equal(measured.streams[0].qualityEvidence, "playable-hls-selected-variant");
assert.equal(measured.streams[0].url, "https://cdn.example/master.m3u8?sig=unchanged");
assert.equal(measured.streams[0].headers.Referer, "https://origin.example/");
assert.equal(measured.streams[0].playable, true);

console.log("engine v2 resolver core tests passed");
