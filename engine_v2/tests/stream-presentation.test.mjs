import assert from "node:assert/strict";
import { normalizeStreamCandidate } from "../src/contracts.mjs";
import {
  buildBadges,
  presentStreamCandidate,
  normalizeSourceType,
} from "../src/stream-presentation.mjs";

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

const presented = presentStreamCandidate(facts, {
  title: "Interstellar",
  year: 2014,
  runtime: 169,
  certification: "-12",
}, { id: "purstream", name: "Purstream" });

assert.equal(presented.title, "Purstream");
assert.equal(presented.quality, "2160p");
assert.equal(presented.codec, "HEVC");
assert.equal(presented.audio, "E-AC3 5.1");
assert.equal(presented.duration, 169);
assert.equal(presented.sourceType, "BLU-RAY");
assert.match(presented.description, /【4K】/);
assert.match(presented.description, /【BLU-RAY】/);
assert.match(presented.description, /🌐 VFF/);
assert.match(presented.description, /🎞 HEVC/);
assert.match(presented.description, /🔊 E-AC3 5\.1/);
assert.match(presented.description, /⏱ 2h49/);
assert.match(presented.description, /🔞 -12/);

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

const noInventedBluray = presentStreamCandidate({
  name: "FrenchStream",
  url: "https://media.example/1080.mp4",
  quality: "1080p",
}, {}, { name: "FrenchStream" });
assert.match(noInventedBluray.description, /【1080P】/);
assert.doesNotMatch(noInventedBluray.description, /BLU-RAY/i);
assert.equal(normalizeSourceType("1080p"), "1080P");

const badges = buildBadges({ quality: "4K", language: "VFQ", codec: "H.264" });
assert.deepEqual(badges, ["【4K】", "🌐 VFQ", "🎞 H.264"]);

console.log("engine v2 stream presentation tests passed");
