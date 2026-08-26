import assert from "node:assert/strict";
import { normalizeStreamCandidate } from "../src/contracts.mjs";
import {
  buildBadgeIds,
  buildBadges,
  normalizeLanguage,
  normalizeSourceType,
  presentStreamCandidate,
} from "../src/stream-presentation.mjs";
import { createTmdbMetadataResolver, normalizeTmdbPayload } from "../src/tmdb-metadata.mjs";

const vfProvider = { id: "purstream", name: "Purstream", languages: ["fr"] };
const voProvider = { id: "cineby", name: "Cineby", languages: ["en"] };

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

const presented = presentStreamCandidate(facts, {
  title: "Interstellar",
  year: 2014,
  runtime: 169,
  certification: "-12",
  mediaType: "movie",
}, vfProvider);

assert.equal(presented.title, "Purstream - 4K");
assert.equal(presented.quality, "2160p");
assert.equal(presented.language, "VF");
assert.equal(presented.codec, "HEVC");
assert.equal(presented.audio, "E-AC3 5.1");
assert.equal(presented.duration, 169);
assert.equal(presented.sourceType, "BLU-RAY");
assert.deepEqual(presented.description.split("\n"), [
  "🎬 Interstellar • 2014",
  "⏱ 2h49 • 🔞 -12",
  "🇫🇷 VF",
  "🎞️ BLU-RAY • HEVC • HLS  |  🔊 E-AC3 5.1",
]);
assert.doesNotMatch(presented.description, /2160p|\b4K\b/i);
assert.ok(presented.badgeIds.includes("4k-ultra-hd"));
assert.ok(presented.badgeIds.includes("blu-ray-disc"));
assert.ok(presented.badgeIds.includes("hevc"));
assert.ok(presented.badgeIds.includes("vf"));
assert.ok(presented.badgeIds.includes("age-12"));

const multiVf = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/multi.m3u8",
  language: "Dual Audio",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.match(multiVf.description, /^🎬 Film • 2026\n🇫🇷 MULTI \(VF\/VO\)/m);
assert.equal(multiVf.language, "MULTI (VF/VO)");
assert.ok(multiVf.badgeIds.includes("multi"));

const multiVo = presentStreamCandidate({
  name: "Cineby",
  url: "https://media.example/multi.m3u8",
  language: "MULTI",
}, { title: "Film", year: 2026, mediaType: "movie" }, voProvider);
assert.match(multiVo.description, /🌐 MULTI/);
assert.equal(multiVo.language, "MULTI");

const vostfr = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/vost.m3u8",
  language: "VOSTFR",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.equal(vostfr.language, "VOSTFR");
assert.match(vostfr.description, /🌐🇫🇷 VOSTFR/);

const vfq = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/vfq.m3u8",
  language: "fr-CA",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.equal(vfq.language, "VFQ");
assert.match(vfq.description, /🇫🇷 VFQ/);

const vfPlusVost = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/vf-vost.m3u8",
  language: "VF",
  description: "VOSTFR available",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.equal(vfPlusVost.language, "MULTI (VF/VO)");
assert.match(vfPlusVost.description, /🇫🇷 MULTI \(VF\/VO\)/);
assert.doesNotMatch(vfPlusVost.description, /VOSTFR available/);

const series = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/episode.m3u8",
  language: "VF",
}, { title: "Jujutsu Kaisen", year: 2020, runtime: 24, certification: "-12", mediaType: "anime", season: 1, episode: 1 }, vfProvider);
assert.equal(series.description.split("\n")[0], "📺 Jujutsu Kaisen • 2020 • S01E01");
assert.equal(series.description.split("\n")[1], "⏱ 24min • 🔞 -12");

const tmdbFallback = presentStreamCandidate({
  name: "Cineby",
  url: "https://media.example/unknown.mp4",
  description: "Unknown",
}, { title: "Sinners", year: 2025, runtime: 137, certification: "16+", mediaType: "movie" }, voProvider);
assert.doesNotMatch(tmdbFallback.description ?? "", /Unknown/i);
assert.match(tmdbFallback.description, /⏱ 2h17/);
assert.match(tmdbFallback.description, /🔞 16\+/);
assert.match(tmdbFallback.description, /🎬 Sinners • 2025/);

const noInventedBluray = presentStreamCandidate({
  name: "FrenchStream",
  url: "https://media.example/1080.mp4",
  quality: "1080p",
}, { title: "Example", year: 2026, mediaType: "movie" }, { name: "FrenchStream", languages: ["fr"] });
assert.equal(noInventedBluray.title, "FrenchStream - 1080p");
assert.doesNotMatch(noInventedBluray.description, /1080p|BLU-RAY/i);
assert.equal(noInventedBluray.sourceType, null);
assert.equal(normalizeSourceType("1080p"), null);
assert.equal(normalizeSourceType("some provider label"), null);

assert.equal(normalizeLanguage({ language: "fr" }, vfProvider), "VF");
assert.equal(normalizeLanguage({ language: "VFQ" }, vfProvider), "VFQ");
assert.equal(normalizeLanguage({ language: "MULTI" }, voProvider), "MULTI");
assert.deepEqual(buildBadges({ quality: "2160p", language: "VFQ", codec: "AVC" }), ["4K", "AVC", "VFQ"]);
assert.deepEqual(buildBadgeIds({ quality: "2160p", language: "VFQ", codec: "AVC", subtitles: [] }), ["4k-ultra-hd", "avc", "vfq"]);

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
assert.match(requestedUrl, /api_key=test-key/);
assert.match(requestedUrl, /language=fr-FR/);
assert.equal(tvMetadata.runtime, 50);
assert.equal(tvMetadata.certification, "12");
assert.equal(tvMetadata.source, "tmdb");

let bearerUrl = "";
let bearerHeaders = null;
const bearerResolver = createTmdbMetadataResolver({
  accessToken: "test-access-token",
  apiKey: "must-not-be-used",
  fetchImpl: async (url, options) => {
    bearerUrl = String(url);
    bearerHeaders = options.headers;
    return {
      ok: true,
      async json() {
        return {
          id: 157336,
          title: "Interstellar",
          original_title: "Interstellar",
          release_date: "2014-11-05",
          runtime: 169,
          alternative_titles: { titles: [] },
          release_dates: { results: [] },
        };
      },
    };
  },
});
await bearerResolver({ tmdbId: "157336", mediaType: "movie", title: "Interstellar" });
assert.doesNotMatch(bearerUrl, /api_key=/);
assert.equal(bearerHeaders.Authorization, "Bearer test-access-token");

assert.throws(
  () => createTmdbMetadataResolver({ accessToken: "", apiKey: "" }),
  /TMDB credentials are required/,
);

const fallbackWithoutId = await tmdbResolver({ mediaType: "movie", title: "Sinners", year: 2025 });
assert.equal(fallbackWithoutId.title, "Sinners");
assert.equal(fallbackWithoutId.year, 2025);
assert.equal(fallbackWithoutId.source, "request");

console.log("engine v2 stream presentation V12 and shared TMDB metadata tests passed");
