import assert from "node:assert/strict";
import {
  emptyRecipeMemory, evidenceSignature, findCompatibleRecipes, findAutoApplicableSkills,
  invalidateRecipe, maturityFor, recordRecipeFailure, rememberSuccessfulRecipe,
} from "../src/recipe-memory.mjs";

const signature = evidenceSignature({ failureClass: "playback_context_gap", request: { mediaType: "movie", device: "tv" }, invoked: true, stages: { player: { found: true, status: 200 }, media: { found: true, status: 403, playable: false } } });
assert.equal(signature.length, 24);
const policy = { candidateSuccesses: 2, trustedSuccesses: 3, trustedProviders: 2, minimumConfidence: 0.8 };
let memory = emptyRecipeMemory();
for (const providerId of ["streamzo", "streamzo", "frenchstream"]) {
  memory = rememberSuccessfulRecipe(memory, {
    id: "preserve-player-context", signature, failureClass: "playback_context_gap",
    actions: ["preserve-referer", "preserve-origin"], capabilities: ["headers", "referer", "origin"],
    runtime: { tv: { acceptedRefs: ["tv-ref-1"] } }, confidence: 0.95, validated: true, providerId,
  }, policy);
}
assert.equal(memory.recipes.length, 1);
assert.equal(memory.recipes[0].successCount, 3);
assert.equal(memory.recipes[0].maturity, "trusted");
assert.equal(memory.recipes[0].autoApply, true);
assert.equal(findAutoApplicableSkills(memory, { failureClass: "playback_context_gap", device: "tv", clientRef: "tv-ref-1" }).length, 1);
assert.equal(findCompatibleRecipes(memory, { signature, failureClass: "playback_context_gap", device: "tv", clientRef: "tv-ref-2" }).length, 0);
assert.equal(findCompatibleRecipes(memory, { signature, device: "tv", clientRef: "tv-ref-1", invalidCapabilities: ["headers"] }).length, 0);

memory = recordRecipeFailure(memory, "preserve-player-context", signature, "other", policy);
assert.equal(memory.recipes[0].failureCount, 1);
assert.equal(memory.recipes[0].confidence, 0.75);
assert.equal(memory.recipes[0].autoApply, false);
assert.equal(maturityFor({ successCount: 1, failureCount: 0, provenOnProviders: ["x"] }, policy).maturity, "experimental");

memory = invalidateRecipe(memory, "preserve-player-context", "Nuvio TV header contract changed", "tv-ref-2");
assert.equal(memory.recipes[0].validated, false);
assert.equal(findCompatibleRecipes(memory, { signature }).length, 0);
assert.throws(() => rememberSuccessfulRecipe(emptyRecipeMemory(), { id: "x", signature, actions: ["a"], validated: false }), /validated/);
console.log("engine v2 recipe memory tests passed");
