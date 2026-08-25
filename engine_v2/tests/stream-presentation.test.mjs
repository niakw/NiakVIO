import assert from "node:assert/strict";
import { normalizeStreamCandidate } from "../src/contracts.mjs";
import {
  buildBadges,
  buildTechnicalLines,
  presentStreamCandidate,
  normalizeSourceType,
} from "../src/stream-presentation.mjs";
import { createTmdbMetadataResolver, normalizeTmdbPayload } from "../src/tmdb-metadata.mjs";

const facts = normalizeStreamCandidate({
  name: "Purstream",
  url: "https://media.example/master.m3u8",
  quality: "4K",
  language: "VFF",
  codec: "x265",
  audio: "DDP 5.1",
  duration: 169,
  sourceType: "BluRay",
  ageRating: "-12",
}, { providerId: "purstream" });

assert.equal(facts.quality, "2160p");
assert.equal(facts.language, "VFF");
assert.equal(facts.codec, "x265");
assert.equal(facts.audio, "DDP 5.1");
assert.equal(facts.duration, 169);
assert.equal(facts.sourceType, "BluRay");
assert.equal(facts.ageRating, "-12");

const presented = presentStreamCandidate({
  ...facts,
  description: "🔥 provider private layout",
  size: "private prose | 8.4 GB | click now",
}, {
  title: "Interstellar",
  year: 2014,
  runtime: 169,
  certification: "-12",
  genres: [{ name: "Science-fiction" }, { name: "Drame" }],
}, { id: "purstream", name: "Purstream" });

assert.equal(presented.title, "Purstream");
assert.equal(presented.quality, "2160p");
assert.equal(presented.codec, "HEVC");
assert.equal(presented.audio, "E-AC3 5.1");
assert.equal(presented.duration, 169);
assert.equal(presented.sourceType, "BLU-RAY");
assert.equal(presented.fileSize, "8.4 GB");
assert.doesNotMatch(presented.description, /provider private|click now/i);
assert.deepEqual(presented.description.split("\n"), [
  "🎬 Interstellar • 2014 • Science-fiction, Drame",
  "🎞️ 2160p • BLU-RAY • HLS",
  "🔊 E-AC3 5.1",
  "🌐 VFF",
  "⏱ 2h49 • 💾 8.4 GB • 🔞 -12",
]);
assert.deepEqual(presented.displayBadges, [
  "4K",
  "BLU-RAY",
  "E-AC3 5.1",
  "VFF",
  "2h49",
  "-12",
]);

const withoutQuality = buildTechnicalLines(presented.presentationFacts, { includeQuality: false });
assert.equal(withoutQuality[0], "🎞️ BLU-RAY • HLS");
assert(!withoutQuality.join("\n").includes("2160p"));

const tmdbFallback = presentStreamCandidate({
  name: "Cineby",
  url: "https://media.example/unknown.mp4",
  description: "Unknown",
}, {
  title: "Sinners",
  year: 2025,
  runtime: 137,
  certification: "16+",
}, { name: "Cineby" });
assert.doesNotMatch(tmdbFallback.description ?? "", /Unknown/i);
assert.match(tmdbFallback.description, /⏱ 2h17/);
assert.match(tmdbFallback.description, /🔞 16\+/);
assert.match(tmdbFallback.description, /🎬 Sinners • 2025/);

const noInventedBluray = presentStreamCandidate({
  name: "FrenchStream",
  url: "https://media.example/1080.mp4",
  quality: "1080p",
}, {}, { name: "FrenchStream" });
assert.match(noInventedBluray.description, /🎞️ 1080p • MP4/);
assert.doesNotMatch(noInventedBluray.description, /BLU-RAY/i);
assert.equal(normalizeSourceType("1080p"), null);
assert.equal(normalizeSourceType("some provider label"), null);

const badges = buildBadges({ quality: "4K", language: "VFQ", codec: "H.264" });
assert.deepEqual(badges, ["4K", "AVC", "VFQ"]);

const normalizedMovie = normalizeTmdbPayload({
  id: 157336,
  title: "Interstellar",
  original_title: "Interstellar",
  release_date: "2014-11-05",
  runtime: 169,
  alternative_titles: { titles: [{ title: "Interstellar" }] },
  release_dates: {
    results: [
      { iso_3166_1: "US", release_dates: [{ certification: "PG-13" }] },
      { iso_3166_1: "FR", release_dates: [{ certification: "U" }] },
    ],
  },
}, { mediaType: "movie", request: { tmdbId: "157336" } });
assert.equal(normalizedMovie.runtime, 169);
assert.equal(normalizedMovie.certification, "U");
assert.equal(normalizedMovie.year, 2014);

let requestedUrl = "";
const tmdbResolver = createTmdbMetadataResolver({
  apiKey: "test-key",
  fetchImpl: async (url) => {
    requestedUrl = String(url);
    return {
      ok: true,
      async json() {
        return {
          id: 95396,
          name: "Severance",
          original_name: "Severance",
          first_air_date: "2022-02-18",
          episode_run_time: [50],
          alternative_titles: { results: [] },
          content_ratings: { results: [{ iso_3166_1: "FR", rating: "12" }] },
        };
      },
    };
  },
});
const tvMetadata = await tmdbResolver({ tmdbId: "95396", mediaType: "tv", title: "Severance" });
assert.match(requestedUrl, /\/tv\/95396/);
assert.match(requestedUrl, /language=fr-FR/);
assert.equal(tvMetadata.runtime, 50);
assert.equal(tvMetadata.certification, "12");
assert.equal(tvMetadata.source, "tmdb");

const fallbackWithoutId = await tmdbResolver({ mediaType: "movie", title: "Sinners", year: 2025 });
assert.equal(fallbackWithoutId.title, "Sinners");
assert.equal(fallbackWithoutId.year, 2025);
assert.equal(fallbackWithoutId.source, "request");

console.log("engine v2 stream presentation V12 tests passed: provider prose removed, multiline groups canonical");
