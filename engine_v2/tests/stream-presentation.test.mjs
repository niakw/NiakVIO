import fs from "node:fs";
import assert from "node:assert/strict";
import { normalizeStreamCandidate } from "../src/contracts.mjs";
import {
  buildBadgeIds,
  buildBadges,
  normalizeLanguage,
  normalizeLanguageCode,
  normalizeLanguageTracks,
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
assert.equal(presented.language, "fr");
assert.equal(presented.codec, "HEVC");
assert.equal(presented.audio, "E-AC3 5.1");
assert.equal(presented.duration, 169);
assert.equal(presented.sourceType, "BLU-RAY");
assert.deepEqual(presented.description.split("\n"), [
  "🎬 Interstellar • 2014",
  "⏱ 2h49 • 🔞 12+",
  "🌐 French · Dub",
  "🎞️ BLU-RAY • HEVC • HLS  |  🔊 E-AC3 • 5.1",
]);
assert.doesNotMatch(presented.description, /2160p|\b4K\b/i);
assert.ok(presented.badgeIds.includes("4k-ultra-hd"));
assert.ok(presented.badgeIds.includes("blu-ray-disc"));
assert.ok(presented.badgeIds.includes("hevc"));
assert.ok(presented.badgeIds.includes("lang-fr"));
assert.ok(presented.badgeIds.includes("age-12"));

const multiVf = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/multi.m3u8",
  language: "Dual Audio",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.doesNotMatch(multiVf.description, /🌐/);
assert.equal(multiVf.language, null);
assert.ok(!multiVf.badgeIds.some((id) => id.startsWith("lang-")));
assert.ok(!multiVf.badgeIds.includes("multi"));

const multiVo = presentStreamCandidate({
  name: "Cineby",
  url: "https://media.example/multi.m3u8",
  language: "MULTI",
}, { title: "Film", year: 2026, mediaType: "movie" }, voProvider);
assert.doesNotMatch(multiVo.description, /🌐 MULTI/);
assert.equal(multiVo.language, null);

const vostfr = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/vost.m3u8",
  language: "VOSTFR",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.equal(vostfr.language, null);
assert.match(vostfr.description, /🌐 💬 Sub · French/);
assert.ok(!vostfr.badgeIds.some((id) => String(id).startsWith("sub-")));

const vfq = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/vfq.m3u8",
  language: "fr-CA",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.equal(vfq.language, "fr-ca");
assert.match(vfq.description, /🌐 French \(Canada\) · Dub/);
assert.ok(vfq.badgeIds.includes("lang-fr-ca"));

const vfPlusVost = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/vf-vost.m3u8",
  language: "VF",
  description: "VOSTFR available",
}, { title: "Film", year: 2026, mediaType: "movie" }, vfProvider);
assert.equal(vfPlusVost.language, "fr");
assert.match(vfPlusVost.description, /French · Dub/);
assert.match(vfPlusVost.description, /💬 Sub · French/);
assert.doesNotMatch(vfPlusVost.description, /VOSTFR available|MULTI/);

const series = presentStreamCandidate({
  name: "Purstream",
  url: "https://media.example/episode.m3u8",
  language: "VF",
}, { title: "Jujutsu Kaisen", year: 2020, runtime: 24, certification: "-12", mediaType: "anime", season: 1, episode: 1 }, vfProvider);
assert.equal(series.description.split("\n")[0], "📺 Jujutsu Kaisen • 2020 • S01E01");
assert.equal(series.description.split("\n")[1], "⏱ 24min • 🔞 12+");

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

const kehflixProvider = { id: "kehflix", name: "Kehflix", languages: ["fr"] };
for (const placeholder of ["Inconnue", "Unknown", "N/A"]) {
  const row = presentStreamCandidate({
    name: `Kehflix - ${placeholder}`,
    title: `Kehflix - ${placeholder}`,
    url: "https://media.example/master.m3u8",
    quality: placeholder,
  }, { title: "Interstellar", year: 2014, mediaType: "movie" }, kehflixProvider);
  assert.equal(row.title, "Kehflix", row.title);
  assert.equal(row.name, "Kehflix", row.name);
  assert.equal(row.quality, null, JSON.stringify(row));
  assert.ok(row.badgeIds.includes("hls"), JSON.stringify(row));
  assert.ok(row.displayBadges.includes("HLS"), JSON.stringify(row));
  assert.match(row.description, /HLS/);
}
const kehflix1080 = presentStreamCandidate({ name: "Kehflix", url: "https://media.example/a.mp4", quality: "1080p" }, { mediaType: "movie" }, kehflixProvider);
assert.equal(kehflix1080.title, "Kehflix - 1080p");
assert.equal(kehflix1080.name, "Kehflix - 1080p");
assert.ok(kehflix1080.badgeIds.includes("mp4"));
const kehflix4k = presentStreamCandidate({ name: "Kehflix", url: "https://media.example/a.mp4", quality: "2160p" }, { mediaType: "movie" }, kehflixProvider);
assert.equal(kehflix4k.title, "Kehflix - 4K");
assert.equal(kehflix4k.name, "Kehflix - 4K");
const kehflix1080i = presentStreamCandidate({ name: "Kehflix", url: "https://media.example/a.ts", quality: "1080i" }, { mediaType: "movie" }, kehflixProvider);
assert.equal(kehflix1080i.title, "Kehflix - 1080i");
assert.ok(kehflix1080i.badgeIds.includes("1080i"));
const kehflix8k = presentStreamCandidate({ name: "Kehflix", url: "https://media.example/a.mkv", quality: "4320p" }, { mediaType: "movie" }, kehflixProvider);
assert.equal(kehflix8k.title, "Kehflix - 8K");
assert.ok(kehflix8k.badgeIds.includes("8k-ultra-hd"));
assert.deepEqual(buildBadgeIds({ sourceType: "ULTRA HD BLU-RAY", releaseType: "REMUX", subtitles: [] }), ["uhd-remux"]);
assert.deepEqual(buildBadgeIds({ sourceType: "BLU-RAY", releaseType: "REMUX", subtitles: [] }), ["blu-ray-remux"]);
assert.deepEqual(buildBadgeIds({ sourceType: "BDMV", subtitles: [] }), ["bdmv"]);


const richTechnical = presentStreamCandidate({
  name: "Anime CDN", url: "https://media.example/master.m3u8", resolution: "1920x1080", codec: "AVC",
  bitrate: "6.0 Mbps", frameRate: "23.976 fps", audioCodec: "AAC", audioChannels: "Stereo", audioSampleRate: "48 kHz", language: "Korean",
}, { title: "Example Anime", year: 2026, mediaType: "anime", originalLanguage: "ko" }, { id: "example", name: "Example" });
for (const id of ["1080p-full-hd","hls","avc","23.976fps","video-bitrate","aac","2.0","48khz","lang-ko"]) assert.ok(richTechnical.badgeIds.includes(id), [id, richTechnical.badgeIds]);
assert.match(richTechnical.description, /Korean · Original/);
assert.match(richTechnical.description, /AVC/); assert.match(richTechnical.description, /23\.976 fps/); assert.match(richTechnical.description, /HLS/);
assert.match(richTechnical.description, /AAC • 2\.0 • 48 kHz/); assert.match(richTechnical.description, /6\.0 Mbps/);
assert.equal(normalizeLanguage({ language: "fr" }, vfProvider), "fr");
assert.equal(normalizeLanguage({ language: "VFQ" }, vfProvider), "fr-ca");
assert.equal(normalizeLanguage({ language: "MULTI" }, voProvider), null);
assert.deepEqual(buildBadges({ quality: "2160p", language: "VFQ", codec: "AVC" }), ["4K", "AVC", "FR-CA"]);
assert.deepEqual(buildBadgeIds({ quality: "2160p", language: "VFQ", codec: "AVC", subtitles: [] }), ["4k-ultra-hd", "avc", "lang-fr-ca"]);


const badgeCatalog = JSON.parse(fs.readFileSync(new URL("../../assets/badge_catalog_v8_complete.json", import.meta.url), "utf8"));
const catalogLanguageCodes = new Set();
const collectCatalogLanguageCodes = (value) => {
  if (Array.isArray(value)) { for (const row of value) collectCatalogLanguageCodes(row); return; }
  if (!value || typeof value !== "object") return;
  if (typeof value.id === "string" && value.id.startsWith("lang-")) catalogLanguageCodes.add(value.id.slice(5));
  for (const row of Object.values(value)) collectCatalogLanguageCodes(row);
};
collectCatalogLanguageCodes(badgeCatalog);
assert.equal(catalogLanguageCodes.size, 47);
for (const code of catalogLanguageCodes) assert.equal(normalizeLanguageCode(code), code, code);
for (const [alias, expected] of [["fre","fr"],["fra","fr"],["jpn","ja"],["kor","ko"],["hin","hi"],["por","pt"],["zho","zh"],["spa","es"]]) {
  assert.equal(normalizeLanguageCode(alias), expected, alias);
}

const nuvioPlayerFacts = presentStreamCandidate({
  name: "Player Source",
  url: "https://media.example/master.m3u8",
  mediaInfo: {
    video: { codec: "AVC", width: 1920, height: 1080, bitrate: 6000000 },
    audioTracks: [{ codec: "AAC", channels: "Stereo", sampleRate: 48000, language: "kor" }],
    subtitleTracks: [{ name: "fr", language: "French", source: "Integrated", integrated: true }],
  },
}, { title: "Player Fixture", year: 2026, mediaType: "movie" }, { id: "fixture", name: "Fixture" });
assert.equal(nuvioPlayerFacts.codec, "AVC");
assert.equal(nuvioPlayerFacts.resolution, "1920x1080");
assert.equal(nuvioPlayerFacts.quality, "1080p");
assert.equal(nuvioPlayerFacts.bitrate, "6.0 Mbps");
assert.equal(nuvioPlayerFacts.audioCodec, "AAC");
assert.equal(nuvioPlayerFacts.audioChannels, "2.0");
assert.equal(nuvioPlayerFacts.audioSampleRate, "48 kHz");
assert.equal(nuvioPlayerFacts.language, "ko");
assert.ok(nuvioPlayerFacts.badgeIds.includes("1080p-full-hd"));
assert.ok(nuvioPlayerFacts.badgeIds.includes("avc"));
assert.ok(nuvioPlayerFacts.badgeIds.includes("video-bitrate"));
assert.ok(nuvioPlayerFacts.badgeIds.includes("aac"));
assert.ok(nuvioPlayerFacts.badgeIds.includes("2.0"));
assert.ok(nuvioPlayerFacts.badgeIds.includes("48khz"));
assert.ok(nuvioPlayerFacts.badgeIds.includes("lang-ko"));
assert.ok(!nuvioPlayerFacts.badgeIds.some((id) => id.startsWith("sub-")));
assert.match(nuvioPlayerFacts.description, /Korean/);
assert.match(nuvioPlayerFacts.description, /💬 Int\. Sub · French/);
assert.match(nuvioPlayerFacts.description, /AVC/);
assert.match(nuvioPlayerFacts.description, /1920x1080 \(1080p\)/);
assert.match(nuvioPlayerFacts.description, /6\.0 Mbps/);
assert.match(nuvioPlayerFacts.description, /AAC/);
assert.match(nuvioPlayerFacts.description, /2\.0/);
assert.match(nuvioPlayerFacts.description, /48 kHz/);

const indianTracks = presentStreamCandidate({
  name: "HindMoviez",
  url: "https://media.example/india.m3u8",
  language: "Hindi/English",
}, { title: "Example", year: 2026, mediaType: "movie", originalLanguage: "en" }, { id: "hindmoviez", name: "HindMoviez", languages: ["hi", "en"] });
assert.deepEqual(indianTracks.languageTracks, [
  { code: "hi", tag: "HI", label: "Hindi", role: "Dub" },
  { code: "en", tag: "EN", label: "English", role: "Original" },
]);
assert.match(indianTracks.description, /Hindi · Dub • English · Original/);
assert.ok(indianTracks.displayBadges.includes("HI Dub"));
assert.ok(indianTracks.displayBadges.includes("EN Original"));

const castleHindi = presentStreamCandidate({
  name: "Castle",
  url: "https://media.example/castle-hi.m3u8",
  language: "Hindi",
}, { title: "Example", year: 2026, mediaType: "movie", originalLanguage: "en" }, { id: "castle", name: "Castle", languages: ["hi", "en"] });
assert.deepEqual(castleHindi.languageTracks, [{ code: "hi", tag: "HI", label: "Hindi", role: "Dub" }]);
assert.match(castleHindi.description, /Hindi · Dub/);

const animeSub = presentStreamCandidate({
  name: "Anime-Sama",
  url: "https://media.example/anime.m3u8",
  language: "VOSTFR",
}, { title: "Anime", year: 2026, mediaType: "anime", originalLanguage: "ja" }, { id: "anime-sama", name: "Anime-Sama", languages: ["fr", "ja"] });
assert.deepEqual(animeSub.languageTracks, [
  { code: "ja", tag: "JA", label: "Japanese", role: "Original" },
  { code: "fr", tag: "FR", label: "French", role: "Sub" },
]);
assert.match(animeSub.description, /Japanese · Original • 💬 Sub · French/);

const hlsTracks = normalizeLanguageTracks({
  audioTracks: [{ language: "en", name: "English" }, { language: "fr", name: "French" }],
}, { originalLanguage: "en" }, vfProvider);
assert.deepEqual(hlsTracks, [
  { code: "en", tag: "EN", label: "English", role: "Original" },
  { code: "fr", tag: "FR", label: "French", role: "Dub" },
]);

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
