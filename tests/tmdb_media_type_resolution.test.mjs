import assert from "node:assert/strict";
import {
  animeEvidence,
  normalizeTmdbPayload,
  resolveCanonicalMediaType,
} from "../engine_v2/src/tmdb-metadata.mjs";

const naruto = {
  id: 46260,
  name: "Naruto",
  first_air_date: "2002-10-03",
  genres: [{ id: 16, name: "Animation" }, { id: 10759, name: "Action & Adventure" }],
  original_language: "ja",
  origin_country: ["JP"],
  keywords: { results: [{ id: 210024, name: "anime" }] },
};
assert.equal(animeEvidence(naruto).isAnime, true);
assert.equal(resolveCanonicalMediaType("series", naruto, {}), "anime");
assert.equal(resolveCanonicalMediaType("tv", naruto, {}), "anime");

const normalized = normalizeTmdbPayload(naruto, {
  mediaType: "tv",
  request: { tmdbId: "46260", mediaType: "series", title: "Naruto" },
});
assert.equal(normalized.mediaType, "anime");
assert.equal(normalized.canonicalMediaType, "anime");
assert.equal(normalized.tmdbKind, "tv");
assert.equal(normalized.animeEvidence.isAnime, true);

const western = {
  id: 1,
  name: "Western Animation",
  genres: [{ id: 16, name: "Animation" }],
  original_language: "en",
  origin_country: ["US"],
};
assert.equal(animeEvidence(western).isAnime, false);
assert.equal(resolveCanonicalMediaType("series", western, {}), "tv");
assert.equal(resolveCanonicalMediaType("series", {}, {}), "tv");
assert.equal(resolveCanonicalMediaType("series", {}, { category: "anime" }), "anime");

console.log("TMDB anime media-type resolution tests passed");
