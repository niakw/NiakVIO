import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { BRAIN_CONTROL_PLANE_VERSION, classifyFailure, planRepair, recipeIsCompatible } from "../src/repair-brain.mjs";

assert.equal(BRAIN_CONTROL_PLANE_VERSION, 4);
assert.equal(classifyFailure({ invoked: false }), "not_invoked");
assert.equal(classifyFailure({ invoked: true, dns: { ok: false } }), "dns_unreachable");
assert.equal(classifyFailure({ invoked: true, dns: { ok: true }, stages: { homepage: { status: 403 } } }), "transport_blocked");
assert.equal(classifyFailure({ invoked: true, dns: { ok: true }, stages: { homepage: { status: 200 }, search: { attempted: true, status: 200, matches: 0 } } }), "search_gap");
assert.equal(classifyFailure({ invoked: true, request: { mediaType: "tv" }, stages: { search: { attempted: true, status: 200, matches: 1 }, identity: { attempted: true, matched: true }, detail: { attempted: true, found: true }, episode: { attempted: true, found: false } } }), "episode_gap");
assert.equal(classifyFailure({ invoked: true, stages: { player: { attempted: true, found: true }, media: { attempted: true, found: true }, validation: { attempted: true, playable: false, playableCount: 0, statuses: [403] } } }), "playback_context_gap");
assert.equal(classifyFailure({ invoked: true, stages: { media: { attempted: true, found: true }, validation: { attempted: true, playable: false, playableCount: 0, statuses: [200] } } }), "media_validation_gap");
assert.equal(classifyFailure({ invoked: true, playableStreams: 1, stages: { validation: { attempted: true, playable: true, playableCount: 1, statuses: [206] } } }), "healthy");
assert.equal(classifyFailure({ contractDrift: true }), "runtime_contract_drift");

const playerBase = {
  invoked: true,
  stages: {
    playerPlayback: {
      attempted: true,
      sourceStatus: 206,
      sourceSignature: "matroska_ebml",
      exoReady: false,
      exoCode: 3003,
      mpvReady: false,
      playable: false,
    },
  },
};
assert.equal(classifyFailure(playerBase), "player_container_unsupported");
assert.equal(classifyFailure({
  ...playerBase,
  stages: { playerPlayback: { ...playerBase.stages.playerPlayback, mpvReady: true } },
}), "player_engine_compatibility_gap");
assert.equal(classifyFailure({
  ...playerBase,
  stages: { playerPlayback: { ...playerBase.stages.playerPlayback, sourceSignature: "html" } },
}), "media_extraction_gap");
assert.equal(classifyFailure({
  ...playerBase,
  stages: { playerPlayback: { ...playerBase.stages.playerPlayback, sourceStatus: 403 } },
}), "playback_context_gap");
assert.equal(classifyFailure({
  ...playerBase,
  stages: { playerPlayback: { ...playerBase.stages.playerPlayback, exoReady: true, playable: true, exoCode: 0 } },
}), "healthy");

const unsupportedPlan = planRepair(playerBase, { maxHypotheses: 3 });
assert.equal(unsupportedPlan.failureClass, "player_container_unsupported");
assert.equal(unsupportedPlan.action, "probe-targeted-repair");
assert.equal(unsupportedPlan.hypotheses[0].id, "resolve-terminal-media-for-reader");
assert.ok(unsupportedPlan.hypotheses.every((recipe) => !recipe.capabilities.includes("cookies")));

const blockedEvidence = { invoked: true, stages: { player: { attempted: true, found: true }, media: { attempted: true, found: true }, validation: { attempted: true, playable: false, playableCount: 0, statuses: [403] } } };
const plan = planRepair(blockedEvidence, { maxHypotheses: 3 });
assert.equal(plan.brainVersion, 4);
assert.equal(plan.failureClass, "playback_context_gap");
assert.equal(plan.action, "probe-targeted-repair");
assert.equal(plan.hypotheses[0].id, "preserve-playback-context");
assert.equal(plan.fallbackPolicy, "lkg_only_after_repair_budget");

const looped = planRepair(blockedEvidence, { budget: { repeatedSignatureCount: 2, maxRepeatedSignature: 2 } });
assert.equal(looped.action, "deferred_retry");
assert.equal(looped.exitReason, "repair_loop_detected");
const tooMuchCode = planRepair(blockedEvidence, { budget: { generatedBytes: 200000, maxGeneratedBytes: 180000 } });
assert.equal(tooMuchCode.action, "deferred_retry");
assert.equal(tooMuchCode.exitReason, "generated_code_budget_exhausted");
const coreEdit = planRepair(blockedEvidence, { coreMutationRequested: true });
assert.equal(coreEdit.action, "deferred_retry");
assert.equal(coreEdit.exitReason, "core_mutation_requires_learning_lab");
const labCore = planRepair(blockedEvidence, { coreMutationRequested: true, learningLab: true });
assert.equal(labCore.action, "probe-targeted-repair");

const constrainedPlan = planRepair(blockedEvidence, { runtimeCompatibility: { invalidCapabilities: ["headers", "cookies", "referer", "origin"] } });
assert.ok(constrainedPlan.hypotheses.every((recipe) => !recipe.capabilities.includes("headers")));
assert.equal(recipeIsCompatible({ capabilities: ["media"] }, { invalidCapabilities: ["headers"] }), true);
assert.equal(recipeIsCompatible({ capabilities: ["headers"] }, { invalidCapabilities: ["headers"] }), false);

const suspicious = planRepair({ suspicious: true, invoked: true });
assert.equal(suspicious.action, "hold-or-quarantine-pending-proof");
const unknown = planRepair({ invoked: true, playableStreams: 0 });
assert.equal(unknown.failureClass, "unknown_failure");
assert.equal(unknown.action, "collect-more-evidence");
assert.deepEqual(unknown.hypotheses.map((row) => row.id), ["collect-missing-evidence"]);
assert.equal(unknown.hypotheses.some((row) => row.id === "inspect-player-javascript"), false);

const planner = fileURLToPath(new URL("../scripts/plan-repairs.mjs", import.meta.url));
const dirtyPayload = {
  mode: "quick",
  policy: {
    production: { maxHypotheses: 3, maxMutationsPerProvider: 2, maxRepeatedSignature: 2, maxGeneratedBytesPerProvider: 180000, maxElapsedMsPerProvider: 45000 },
    skillMaturity: { trustedSuccesses: 3, trustedProviders: 2, minimumConfidence: 0.8 },
  },
  learnedSkills: {
    dirty: { id: "dirty", failureClass: "search_gap", profile: "adaptive_runtime_recovery", providers: "dirty-provider", capabilities: "search", actions: "repair" },
  },
  items: [
    {
      key: "published:dirty-provider",
      candidate: { canonical_id: "dirty-provider", metadata: { supportedTypes: "movie" } },
      result: { status: "no_streams", tests: [null, { failure_class: "content_lookup_completed_no_streams", network_observations: [null, { status: 200 }] }] },
      state: { mutationCount: 0, signatureCounts: {} },
    },
    {
      key: "published:healthy-provider",
      candidate: { canonical_id: "healthy-provider", metadata: { supportedTypes: ["movie"] } },
      result: { status: "healthy", evidence: { streams_playable: 1 }, tests: [] },
      state: {},
    },
  ],
};
const plannerRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(dirtyPayload), encoding: "utf8" });
assert.equal(plannerRun.status, 0, plannerRun.stderr);
const plannerOutput = JSON.parse(plannerRun.stdout);
assert.equal(plannerOutput.brainVersion, 4);
assert.equal(plannerOutput.plannerErrors, 0);
assert.ok(plannerOutput.plans["published:dirty-provider"]);
assert.equal(plannerOutput.plans["published:healthy-provider"].action, "none");

console.log("engine v2 repair brain tests passed");
