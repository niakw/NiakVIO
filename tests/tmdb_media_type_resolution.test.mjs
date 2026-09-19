import assert from "node:assert/strict";
import {
  animeEvidence,
  createTmdbMetadataResolver,
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

const animeMovie = {
  id: 4242,
  title: "Anime Movie",
  original_title: "Anime Movie",
  release_date: "2026-01-01",
  genres: [{ id: 16, name: "Animation" }],
  original_language: "ja",
  production_countries: [{ iso_3166_1: "JP" }],
  keywords: { keywords: [{ id: 1, name: "anime" }] },
};
assert.equal(resolveCanonicalMediaType("movie", animeMovie, {}), "anime");
const normalizedMovieAnime = normalizeTmdbPayload(animeMovie, {
  mediaType: "movie",
  tmdbKind: "movie",
  request: { tmdbId: "4242", mediaType: "movie", title: "Anime Movie" },
});
assert.equal(normalizedMovieAnime.mediaType, "anime");
assert.equal(normalizedMovieAnime.canonicalMediaType, "anime");
assert.equal(normalizedMovieAnime.tmdbKind, "movie");
assert.equal(normalizedMovieAnime.title, "Anime Movie");

const seenKinds = [];
const resolveAmbiguousAnime = createTmdbMetadataResolver({
  apiKey: "test",
  fetchImpl: async (url) => {
    const value = String(url);
    seenKinds.push(value);
    if (value.includes("/tv/4242")) {
      return {
        ok: true,
        json: async () => ({
          id: 4242,
          name: "Ordinary TV",
          first_air_date: "2026-01-01",
          genres: [{ id: 18, name: "Drama" }],
          original_language: "en",
          origin_country: ["US"],
        }),
      };
    }
    if (value.includes("/movie/4242")) return { ok: true, json: async () => animeMovie };
    throw new Error(`unexpected TMDB URL: ${value}`);
  },
});
const ambiguousAnime = await resolveAmbiguousAnime({ tmdbId: "4242", mediaType: "anime" });
assert.equal(ambiguousAnime.mediaType, "anime");
assert.equal(ambiguousAnime.tmdbKind, "movie");
assert.equal(seenKinds.length, 2);
assert.ok(seenKinds[0].includes("/tv/4242"));
assert.ok(seenKinds[1].includes("/movie/4242"));

console.log("TMDB anime media-type resolution tests passed");
