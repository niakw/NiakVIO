import assert from "node:assert/strict";
import { buildProviderInventory, inventoryStats } from "../src/provider-ingest.mjs";

const inventory = buildProviderInventory([
  {
    upstreamId: "a",
    repository: "x/a",
    ref: "aaa",
    manifestSha: "m1",
    manifest: {
      scrapers: [{
        id: "Example",
        name: "Example A",
        filename: "providers/example.js",
        supportedTypes: ["movie", "series"],
        contentLanguage: ["FRA"],
        formats: ["m3u8"],
        enabled: true,
      }],
    },
  },
  {
    upstreamId: "b",
    repository: "x/b",
    ref: "bbb",
    manifestSha: "m2",
    manifest: {
      scrapers: [{
        id: "example",
        name: "Example B",
        filename: "providers/example.js",
        supportedTypes: ["anime"],
        contentLanguage: ["fr", "eng"],
        supportedFormats: ["mp4"],
        disabledPlatforms: ["ios"],
        hasSettings: true,
        enabled: false,
      }],
    },
  },
]);

assert.equal(inventory.providerCount, 1);
assert.equal(inventory.variantCount, 2);
assert.equal(inventory.duplicateProviderCount, 1);
const provider = inventory.providers[0];
assert.equal(provider.id, "example");
assert.deepEqual(provider.supportedTypes, ["movie", "tv", "anime"]);
assert.deepEqual(provider.languages, ["fr", "en"]);
assert.deepEqual(provider.formats, ["m3u8", "mp4"]);
assert.equal(provider.hasSettings, true);
assert.deepEqual(provider.disabledPlatforms, ["ios"]);
assert.deepEqual(provider.upstreamEnabledStates, { a: true, b: false });
assert.equal(provider.selection, null);
assert.equal(provider.state, "unobserved");

const stats = inventoryStats(inventory);
assert.equal(stats.providers, 1);
assert.equal(stats.variants, 2);
assert.equal(stats.duplicates, 1);
assert.equal(stats.movie, 1);
assert.equal(stats.tv, 1);
assert.equal(stats.anime, 1);

console.log("engine v2 provider ingestion tests passed");
