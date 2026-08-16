import assert from "node:assert/strict";
import {
  emptyRecipeMemory,
  evidenceSignature,
  findCompatibleRecipes,
  invalidateRecipe,
  rememberSuccessfulRecipe,
} from "../src/recipe-memory.mjs";

const signature = evidenceSignature({
  failureClass: "playback_context_gap",
  request: { mediaType: "movie", device: "tv" },
  invoked: true,
  stages: { player: { found: true, status: 200 }, media: { found: true, status: 403, playable: false } },
});
assert.equal(signature.length, 24);

let memory = emptyRecipeMemory();
memory = rememberSuccessfulRecipe(memory, {
  id: "preserve-player-context",
  signature,
  failureClass: "playback_context_gap",
  actions: ["preserve-referer", "preserve-origin"],
  capabilities: ["headers", "referer", "origin"],
  runtime: { tv: { acceptedRefs: ["tv-ref-1"] } },
  confidence: 0.95,
  validated: true,
});
assert.equal(memory.recipes.length, 1);
assert.equal(memory.recipes[0].successCount, 1);

const found = findCompatibleRecipes(memory, { signature, failureClass: "playback_context_gap", device: "tv", clientRef: "tv-ref-1" });
assert.equal(found.length, 1);
assert.equal(found[0].id, "preserve-player-context");

const wrongVersion = findCompatibleRecipes(memory, { signature, device: "tv", clientRef: "tv-ref-2" });
assert.equal(wrongVersion.length, 0);

const invalidatedCapability = findCompatibleRecipes(memory, { signature, device: "tv", clientRef: "tv-ref-1", invalidCapabilities: ["headers"] });
assert.equal(invalidatedCapability.length, 0);

memory = invalidateRecipe(memory, "preserve-player-context", "Nuvio TV header contract changed", "tv-ref-2");
assert.equal(memory.recipes[0].validated, false);
assert.equal(findCompatibleRecipes(memory, { signature }).length, 0);

assert.throws(() => rememberSuccessfulRecipe(emptyRecipeMemory(), { id: "x", signature, actions: ["a"], validated: false }), /validated/);

console.log("engine v2 recipe memory tests passed");
