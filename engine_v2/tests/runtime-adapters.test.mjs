import assert from "node:assert/strict";
import { compareDeviceInvocations, toRuntimeStream } from "../src/runtime-adapters.mjs";

const comparison = compareDeviceInvocations({
  tmdbId: "1396",
  mediaType: "series",
  title: "Breaking Bad",
  season: 1,
  episode: 1,
});
assert.equal(comparison.consistent, true);
for (const device of ["mobile", "desktop", "tv"]) {
  assert.deepEqual(comparison.invocations[device].positionalArgs, ["1396", "tv", 1, 1]);
}

const raw = {
  title: "VF",
  url: "https://cdn.example/stream.m3u8",
  headers: { Referer: "https://player.example/" },
  subtitles: [{ url: "https://sub.example/fr.vtt", language: "fr" }],
};
const mobile = toRuntimeStream(raw, "mobile", { providerId: "example" });
const desktop = toRuntimeStream(raw, "desktop", { providerId: "example" });
const tv = toRuntimeStream(raw, "tv", { providerId: "example" });
assert.equal(mobile.subtitles.length, 1);
assert.equal(desktop.subtitles.length, 1);
assert.equal("subtitles" in tv, false);
assert.equal(tv.headers.Referer, "https://player.example/");

console.log("engine v2 runtime adapter tests passed");
