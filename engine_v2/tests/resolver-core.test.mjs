import assert from "node:assert/strict";
import { ResolverCore } from "../src/resolver-core.mjs";

const core = new ResolverCore({ maxRepairHypotheses: 2 });

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
    return { ok: true, status: 206, streams: [{ title: "VF", url: "https://cdn.example.test/master.m3u8", language: "fr" }] };
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
assert.equal(result.evidence.stages.episode.found, true);
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
assert.equal(directApi.repair.failureClass, "healthy");

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

console.log("engine v2 resolver core tests passed");
