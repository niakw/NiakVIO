import assert from "node:assert/strict";
import { normalizeStreamCandidate } from "../src/contracts.mjs";
import { presentStreamCandidate } from "../src/stream-presentation.mjs";

const provider = { id: "reader", name: "Reader", languages: ["fr"] };
const movie = { mediaType: "movie", title: "Fixture" };

const fromPlayer = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/master.m3u8", quality: "0", height: 1080, audioTrack: "Hindi/English" }, { providerId: "reader", providerName: "Reader" });
const playerPresented = presentStreamCandidate(fromPlayer, movie, provider);
assert.equal(playerPresented.quality, "1080p");
assert.equal(playerPresented.language, null);
assert.match(playerPresented.description, /Hindi .* English/);
assert.deepEqual(playerPresented.badgeIds.filter((id) => id.startsWith("lang-")), ["lang-hi", "lang-en"]);

const fromLabel = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/master.m3u8", quality: "HD", sourceLabel: "Server FHD 1920x1080" }, { providerId: "reader", providerName: "Reader" });
assert.equal(presentStreamCandidate(fromLabel, movie, provider).quality, "1080p");

const fromUrl = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/video-720p.mp4", quality: "source" }, { providerId: "reader", providerName: "Reader" });
assert.equal(presentStreamCandidate(fromUrl, movie, provider).quality, "720p");

const unknown = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/master.m3u8", quality: "0" }, { providerId: "reader", providerName: "Reader" });
const unknownPresented = presentStreamCandidate(unknown, movie, provider);
assert.equal(unknownPresented.quality, null);
assert.equal(unknownPresented.language, "fr");

const natural = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/a.mp4", language: "Japanese" }, { providerId: "reader", providerName: "Reader" });
assert.equal(presentStreamCandidate(natural, movie, provider).language, "ja");

const explicitVo = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/a.mp4", language: "VO" }, { providerId: "reader", providerName: "Reader" });
assert.equal(presentStreamCandidate(explicitVo, movie, provider).language, null);

const captions = normalizeStreamCandidate({ name: "Reader", url: "https://media.example/a.mp4", language: "Hindi", extCaptions: [{ lan: "fr", lanName: "French", url: "https://media.example/fr.vtt" }] }, { providerId: "reader", providerName: "Reader" });
assert.equal(captions.subtitles[0].language, "French");
assert.match(presentStreamCandidate(captions, movie, provider).description, /💬 Sub · French/);

{
  const integrated = normalizeStreamCandidate(
    { name: "Neko-Sama - Inconnue", url: "https://media.example/master.m3u8", type: "hls", hlsMasterSubtitleTracks: [{ language: "fr", name: "French" }] },
    { providerId: "neko-sama", providerName: "Neko-Sama" },
  );
  const presented = presentStreamCandidate(integrated, { mediaType: "anime", title: "Fixture", originalLanguage: "ja" }, { id: "neko-sama", name: "Neko-Sama" });
  assert.ok(!presented.badgeIds.some((id) => String(id).startsWith("sub-")), JSON.stringify(presented.badgeIds));
  assert.ok(presented.languageTracks.some((row) => row.code === "fr" && row.role === "Sub"), JSON.stringify(presented.languageTracks));
  assert.deepEqual(presented.subtitles, [], "integrated HLS metadata must not manufacture external subtitle rows");
}

console.log("stream metadata truth contract passed");
