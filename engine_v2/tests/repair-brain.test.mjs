import assert from "node:assert/strict";
import { classifyFailure, planRepair, recipeIsCompatible } from "../src/repair-brain.mjs";

assert.equal(classifyFailure({ invoked: false }), "not_invoked");
assert.equal(classifyFailure({ invoked: true, dns: { ok: false } }), "dns_unreachable");
assert.equal(classifyFailure({ invoked: true, dns: { ok: true }, stages: { homepage: { status: 403 } } }), "transport_blocked");
assert.equal(classifyFailure({
  invoked: true,
  dns: { ok: true },
  stages: { homepage: { status: 200 }, search: { attempted: true, status: 200, matches: 0 } },
}), "search_gap");
assert.equal(classifyFailure({
  invoked: true,
  request: { mediaType: "tv" },
  stages: {
    search: { attempted: true, status: 200, matches: 1 },
    identity: { attempted: true, matched: true },
    detail: { attempted: true, found: true },
    episode: { attempted: true, found: false },
  },
}), "episode_gap");
assert.equal(classifyFailure({
  invoked: true,
  stages: { player: { attempted: true, found: true }, media: { attempted: true, found: true, status: 403 } },
}), "playback_context_gap");
assert.equal(classifyFailure({
  invoked: true,
  playableStreams: 1,
  stages: { media: { attempted: true, found: true, status: 206, playable: true } },
}), "healthy");
assert.equal(classifyFailure({ contractDrift: true }), "runtime_contract_drift");

const plan = planRepair({
  invoked: true,
  stages: { player: { attempted: true, found: true }, media: { attempted: true, found: true, status: 403 } },
}, { maxHypotheses: 3 });
assert.equal(plan.failureClass, "playback_context_gap");
assert.ok(plan.hypotheses.length > 0 && plan.hypotheses.length <= 3);
assert.equal(plan.hypotheses[0].id, "preserve-playback-context");

const constrainedPlan = planRepair({
  invoked: true,
  stages: { player: { attempted: true, found: true }, media: { attempted: true, found: true, status: 403 } },
}, {
  runtimeCompatibility: { invalidCapabilities: ["headers", "cookies", "referer", "origin"] },
});
assert.ok(constrainedPlan.hypotheses.every((recipe) => !recipe.capabilities.includes("headers")));

assert.equal(recipeIsCompatible({ capabilities: ["media"] }, { invalidCapabilities: ["headers"] }), true);
assert.equal(recipeIsCompatible({ capabilities: ["headers"] }, { invalidCapabilities: ["headers"] }), false);

const suspicious = planRepair({ suspicious: true, invoked: true });
assert.equal(suspicious.failureClass, "identity_mismatch");
assert.equal(suspicious.action, "hold-or-quarantine-pending-proof");

console.log("engine v2 repair brain tests passed");
