import assert from "node:assert/strict";
import { compareDeviceInvocations, toRuntimeStream } from "../src/runtime-adapters.mjs";

const comparison = compareDeviceInvocations({
  tmdbId: "1396", mediaType: "series", title: "Breaking Bad", season: 1, episode: 1,
});
assert.equal(comparison.consistent, true);
for (const device of ["mobile", "desktop", "tv"]) {
  assert.deepEqual(comparison.invocations[device].positionalArgs, ["1396", "tv", 1, 1]);
}

const raw = {
  title: "Example - 4K",
  name: "Example",
  description: "🎬 Interstellar • 2014\n⏱ 2h49 • 🔞 -12\n🇫🇷 VF\n🎞️ WEB-DL • HEVC • HDR10 • HLS | 🔊 E-AC3 • 5.1",
  url: {
    url: "https://cdn.example/stream.m3u8",
    behaviorHints: { proxyHeaders: { request: { Referer: "https://nested.example/" } }, notWebReady: true },
  },
  headers: { Origin: "https://player.example/" },
  behaviorHints: {
    bingeGroup: "example-group",
    proxyHeaders: { request: { Referer: "https://player.example/" } },
  },
  subtitles: [{ url: "https://sub.example/fr.vtt", language: "fr" }],
  resolution: "4K",
  lang: "VF",
  video_codec: "HEVC",
  audio_codec: "E-AC3 5.1",
  duration_minutes: 169,
  source_type: "WEB-DL",
  release_type: "REMUX",
  format: "HLS",
  age_rating: "-12",
  source_label: "Server 1",
  fileName: "interstellar.m3u8",
  hdr: "HDR10",
  bit_depth: "10bit",
  badgeIds: ["4k-ultra-hd", "webdl", "hevc"],
  displayBadges: ["4K", "WEB-DL", "HEVC"],
  presentationFacts: { quality: "2160p", language: "VF" },
  edition: "Director's Cut",
  release_group: "NTb",
  bitrate: 18300000,
  container: "MKV",
  encoder: "x265",
  indexer: "ExampleIndexer",
  network: "CDN-A",
  folder_size: 9876543210,
  seeders: 42,
};

for (const device of ["mobile", "desktop", "tv"]) {
  const row = toRuntimeStream(raw, device, { providerId: "example" });
  assert.equal(row.title, "Example - 4K");
  assert.equal(row.description.includes("2160p"), false);
  assert.equal(row.quality, "2160p");
  assert.equal(row.language, "VF");
  assert.equal(row.codec, "HEVC");
  assert.equal(row.audio, "E-AC3 5.1");
  assert.equal(row.duration, 169);
  assert.equal(row.sourceType, "WEB-DL");
  assert.equal(row.releaseType, "REMUX");
  assert.equal(row.format, "HLS");
  assert.equal(row.ageRating, "-12");
  assert.equal(row.sourceLabel, "Server 1");
  assert.equal(row.filename, "interstellar.m3u8");
  assert.equal(row.hdr, "HDR10");
  assert.equal(row.bitDepth, "10bit");
  assert.deepEqual(row.badgeIds, ["4k-ultra-hd", "webdl", "hevc"]);
  assert.deepEqual(row.presentationFacts, { quality: "2160p", language: "VF" });
  assert.equal(row.edition, "Director's Cut");
  assert.equal(row.releaseGroup, "NTb");
  assert.equal(row.bitrate, 18300000);
  assert.equal(row.container, "MKV");
  assert.equal(row.encode, "x265");
  assert.equal(row.indexer, "ExampleIndexer");
  assert.equal(row.network, "CDN-A");
  assert.equal(row.folderSize, 9876543210);
  assert.equal(row.seeders, 42);
  assert.equal(row.behaviorHints.bingeGroup, "example-group");
  assert.equal(row.behaviorHints.notWebReady, true);
  assert.equal(row.headers.Referer, "https://player.example/");
  assert.equal(row.headers.Origin, "https://player.example/");
}

const mobile = toRuntimeStream(raw, "mobile", { providerId: "example" });
const desktop = toRuntimeStream(raw, "desktop", { providerId: "example" });
const tv = toRuntimeStream(raw, "tv", { providerId: "example" });
assert.equal(mobile.subtitles.length, 1);
assert.equal(desktop.subtitles.length, 1);
assert.equal("subtitles" in tv, false);

console.log("engine v2 runtime adapter metadata projection tests passed");
