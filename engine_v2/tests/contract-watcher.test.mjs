import assert from "node:assert/strict";
import {
  classifyChangedPaths,
  classifySemanticTokens,
  deriveContractAction,
  runtimeCompatibilityFromDrift,
} from "../src/contract-watcher.mjs";

const client = {
  contract_paths: ["app/plugin/", "app/StreamRepository.kt"],
  semantic_paths: ["app/player/", "gradle/libs.versions.toml"],
};

const classified = classifyChangedPaths(client, [
  { filename: "app/plugin/PluginRuntime.kt" },
  { filename: "app/player/Player.kt" },
  { filename: "app/home/Home.kt" },
]);
assert.deepEqual(classified.hard, ["app/plugin/PluginRuntime.kt"]);
assert.deepEqual(classified.semantic, ["app/player/Player.kt"]);
assert.deepEqual(classified.unrelated, ["app/home/Home.kt"]);

const tokenHits = classifySemanticTokens([
  "proxyHeaders = headers; okhttp client",
  "unrelated",
], ["proxyHeaders", "okhttp", "getStreams"]);
assert.deepEqual(tokenHits, ["okhttp", "proxyHeaders"]);

assert.equal(deriveContractAction({ hard: ["x"], semantic: [], semanticTokenHits: [] }), "runtime-reaudit-required");
assert.equal(deriveContractAction({ hard: [], semantic: ["x"], semanticTokenHits: ["okhttp"] }), "targeted-semantic-review-required");
assert.equal(deriveContractAction({ hard: [], semantic: ["x"], semanticTokenHits: [] }), "semantic-path-review-recommended");
assert.equal(deriveContractAction({ hard: [], semantic: [], semanticTokenHits: [] }), "safe-advance-candidate");

const compatibility = runtimeCompatibilityFromDrift("tv", {
  hard: [],
  semantic: ["player"],
  semanticTokenHits: ["proxyHeaders", "okhttp"],
});
assert.equal(compatibility.device, "tv");
assert.ok(compatibility.invalidCapabilities.includes("headers"));
assert.ok(compatibility.invalidCapabilities.includes("cookies"));
assert.ok(compatibility.invalidCapabilities.includes("redirects"));

console.log("engine v2 contract watcher tests passed");
