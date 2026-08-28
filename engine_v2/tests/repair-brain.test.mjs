import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
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
assert.equal(classifyFailure({ audioTrackGap: true }), "audio_track_gap");

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

// Version-gated skills must be compatible with the complete client generation
// range NiakVIO claims to support, not merely with the newest audited HEAD.
const versionedRuntime = {
  invalidCapabilities: [],
  clients: {
    "nuvio-mobile": { supportedMinVersionCode: 109, supportedMaxVersionCode: 111 },
    "nuvio-desktop": { supportedMinVersionCode: 17, supportedMaxVersionCode: 20 },
    "nuvio-tv": { supportedMinVersionCode: 1045, supportedMaxVersionCode: 1048 },
  },
};
assert.equal(recipeIsCompatible({ capabilities: ["parser"], clientVersions: { "nuvio-mobile": { min: 109 } } }, versionedRuntime), true);
assert.equal(recipeIsCompatible({ capabilities: ["parser"], clientVersions: { "nuvio-mobile": { min: 111 } } }, versionedRuntime), false);
assert.equal(recipeIsCompatible({ capabilities: ["media"], clientVersions: { "nuvio-tv": { max: 1048 } } }, versionedRuntime), true);
assert.equal(recipeIsCompatible({ capabilities: ["media"], clientVersions: { "nuvio-tv": { max: 1047 } } }, versionedRuntime), false);
assert.equal(recipeIsCompatible({ capabilities: ["media"], clientVersions: { "unknown-client": { min: 1 } } }, versionedRuntime), false);

const suspicious = planRepair({ suspicious: true, invoked: true });
assert.equal(suspicious.action, "hold-or-quarantine-pending-proof");
const unknown = planRepair({ invoked: true, playableStreams: 0 });
assert.equal(unknown.failureClass, "unknown_failure");
assert.equal(unknown.action, "collect-more-evidence");
assert.deepEqual(unknown.hypotheses.map((row) => row.id), ["collect-missing-evidence"]);
assert.equal(unknown.hypotheses.some((row) => row.id === "inspect-player-javascript"), false);

// A dirty real-world provider/skill shape must never crash the batch planner.
// In particular, providers/capabilities/actions may arrive as scalars and
// network observations may contain null rows. The old planner crashed on this.
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

// A provider can return media successfully while the final media request is
// blocked or gone. That is a playback-context failure, not a provider transport
// failure. Misclassifying this sends the repair budget to the wrong layer.
const playbackPayload = {
  mode: "deep",
  policy: dirtyPayload.policy,
  learnedSkills: {},
  items: [{
    key: "published:stream-context",
    candidate: { canonical_id: "stream-context", metadata: { supportedTypes: ["movie"] } },
    result: {
      status: "blocked",
      evidence: { streams_returned: 2, streams_playable: 0 },
      tests: [{
        fixture: { category: "movie" },
        stream_count: 2,
        streams_playable: 0,
        failure_class: "stream_http_forbidden",
        network_observations: [{ status: 200 }, { status: 403 }],
      }],
    },
    state: {},
  }],
};
const playbackRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(playbackPayload), encoding: "utf8" });
assert.equal(playbackRun.status, 0, playbackRun.stderr);
const playbackOutput = JSON.parse(playbackRun.stdout);
const playbackPlan = playbackOutput.plans["published:stream-context"];
assert.equal(playbackPlan.failureClass, "playback_context_gap");
assert.equal(playbackPlan.repairScope, "capability");
assert.equal(playbackPlan.repairType, "playback_context");
assert.equal(playbackPlan.pipelineStage, "capability_global_invariants");
assert.equal(playbackPlan.hypotheses[0].id, "preserve-playback-context");
assert.ok(playbackPlan.allowedProfiles.includes("adaptive_runtime_recovery"));

// Real StreamZo shape: the provider/search/player chain is healthy and returns
// 2xx, but a terminal ShareCloudy HLS request is rejected before a stream row is
// surfaced. That downstream 403 must not poison the provider as transport-blocked.
const terminalMediaPayload = {
  mode: "quick",
  policy: dirtyPayload.policy,
  learnedSkills: {},
  items: [
    {
      key: "published:streamzo-zero-return",
      candidate: { canonical_id: "streamzo", metadata: { supportedTypes: ["movie", "tv"] } },
      result: {
        status: "no_streams",
        evidence: { streams_returned: 0, streams_playable: 0 },
        tests: [{
          fixture: { category: "anime" },
          stream_count: 0,
          streams_playable: 0,
          failure_class: "content_lookup_completed_no_streams",
          network_observations: [
            { stage: "search", host: "streamzo.fr", path_pattern: "/search?q={value}", status: 200, infrastructure: false },
            { stage: "content_lookup", host: "streamzo.fr", path_pattern: "/series/l-attaque-des-titans-2013", status: 200, infrastructure: false },
            { stage: "player", host: "streamzo.fr", path_pattern: "/embed/sharecloudy.com/{id}", status: 200, infrastructure: false },
            { stage: "content_lookup", host: "share102764.sharecloudy.com", path_pattern: "/files/aa/example.m3u8", status: 403, infrastructure: false },
          ],
        }],
      },
      state: {},
    },
    {
      key: "published:provider-blocked",
      candidate: { canonical_id: "provider-blocked", metadata: { supportedTypes: ["movie"] } },
      result: {
        status: "blocked",
        evidence: { streams_returned: 0, streams_playable: 0 },
        tests: [{
          fixture: { category: "movie" },
          stream_count: 0,
          failure_class: "provider_http_error",
          network_observations: [
            { stage: "origin_probe", host: "provider-blocked.example", path_pattern: "/", status: 403, infrastructure: false },
          ],
        }],
      },
      state: {},
    },
  ],
};
const terminalMediaRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(terminalMediaPayload), encoding: "utf8" });
assert.equal(terminalMediaRun.status, 0, terminalMediaRun.stderr);
const terminalMediaOutput = JSON.parse(terminalMediaRun.stdout);
const streamzoTerminalPlan = terminalMediaOutput.plans["published:streamzo-zero-return"];
assert.equal(streamzoTerminalPlan.failureClass, "playback_context_gap");
assert.equal(streamzoTerminalPlan.repairScope, "capability");
assert.equal(streamzoTerminalPlan.repairType, "playback_context");
assert.equal(streamzoTerminalPlan.capabilityStrategy, "mixed_embed_resolver");
assert.equal(streamzoTerminalPlan.learningDisposition, "core_repair_only");
assert.equal(streamzoTerminalPlan.hypotheses[0].id, "preserve-playback-context");
assert.ok(streamzoTerminalPlan.allowedProfiles.includes("adaptive_runtime_recovery"));
assert.equal(terminalMediaOutput.plans["published:provider-blocked"].failureClass, "transport_blocked");
assert.equal(terminalMediaOutput.plans["published:provider-blocked"].hypotheses[0].id, "bootstrap-session");


const identityPayload = {
  mode: "quick",
  policy: dirtyPayload.policy,
  learnedSkills: {},
  items: [{
    key: "published:any-provider",
    candidate: { canonical_id: "any-provider", metadata: { supportedTypes: ["anime"] } },
    result: {
      status: "healthy",
      evidence: { streams_playable: 1, identity_contradiction_count: 1 },
      tests: [{ fixture: { category: "anime", mediaType: "anime" }, streams_playable: 1 }],
    },
    state: {},
  }],
};
const identityRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(identityPayload), encoding: "utf8" });
assert.equal(identityRun.status, 0, identityRun.stderr);
const identityPlan = JSON.parse(identityRun.stdout).plans["published:any-provider"];
assert.equal(identityPlan.failureClass, "identity_mismatch");
assert.equal(identityPlan.repairScope, "global");
assert.equal(identityPlan.repairType, "media_identity_guard");
assert.deepEqual(identityPlan.allowedProfiles, []);

const monotonicPayload = {
  mode: "learning",
  policy: dirtyPayload.policy,
  learnedSkills: {},
  items: [{
    key: "published:hindmovie-like",
    candidate: { canonical_id: "hindmovie-like", metadata: { supportedTypes: ["movie", "tv", "anime"] } },
    result: {
      status: "no_streams",
      evidence: { streams_returned: 0, streams_playable: 0 },
      tests: [{
        fixture: { category: "anime", mediaType: "anime" },
        failure_class: "content_lookup_completed_no_streams",
        stream_count: 0,
        streams_playable: 0,
        network_observations: [
          { stage: "search", status: 200, infrastructure: false },
          { stage: "content_lookup", status: 200, infrastructure: false },
          { stage: "player", status: 200, infrastructure: false },
        ],
      }],
    },
    state: {},
  }],
};
const monotonicRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(monotonicPayload), encoding: "utf8" });
assert.equal(monotonicRun.status, 0, monotonicRun.stderr);
const monotonicPlan = JSON.parse(monotonicRun.stdout).plans["published:hindmovie-like"];
assert.equal(monotonicPlan.observedPipelineStage, "player");
assert.equal(monotonicPlan.failureClass, "media_extraction_gap");
assert.equal(monotonicPlan.repairType, "terminal_media_resolution");
assert.notEqual(monotonicPlan.failureClass, "search_gap");
assert.notEqual(monotonicPlan.failureClass, "player_gap");


const quickUnknownPayload = {
  mode: "quick",
  policy: dirtyPayload.policy,
  learnedSkills: { "should-not-be-used": { profile: "adaptive_runtime_recovery" } },
  items: [{
    key: "published:new-pattern-quick",
    candidate: { canonical_id: "new-pattern-quick", metadata: { supportedTypes: ["movie"] } },
    result: { status: "runtime_error", evidence: { streams_returned: 0 }, tests: [{ failure_class: "novel_unknown_pattern" }] },
    state: {},
  }],
};
const quickUnknownRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(quickUnknownPayload), encoding: "utf8" });
assert.equal(quickUnknownRun.status, 0, quickUnknownRun.stderr);
const quickUnknownPlan = JSON.parse(quickUnknownRun.stdout).plans["published:new-pattern-quick"];
assert.equal(quickUnknownPlan.repairScope, "deferred");
assert.equal(quickUnknownPlan.repairType, "architecture_gap");
assert.equal(quickUnknownPlan.repairEngine, "independent_learning_queue");
assert.equal(quickUnknownPlan.learningDisposition, "queue_for_independent_learning");
assert.deepEqual(quickUnknownPlan.allowedProfiles, []);

const unknownPayload = {
  mode: "learning",
  policy: dirtyPayload.policy,
  learnedSkills: {},
  items: [{
    key: "published:new-pattern",
    candidate: { canonical_id: "new-pattern", metadata: { supportedTypes: ["movie"] } },
    result: { status: "runtime_error", evidence: { streams_returned: 0 }, tests: [{ failure_class: "novel_unknown_pattern" }] },
    state: {},
  }],
};
const unknownRun = spawnSync(process.execPath, [planner], { input: JSON.stringify(unknownPayload), encoding: "utf8" });
assert.equal(unknownRun.status, 0, unknownRun.stderr);
const unknownPlan = JSON.parse(unknownRun.stdout).plans["published:new-pattern"];
assert.equal(unknownPlan.repairScope, "learning");
assert.equal(unknownPlan.repairType, "architecture_gap");
assert.equal(unknownPlan.learningDisposition, "propose_new_or_evolved_core_type");
assert.deepEqual(unknownPlan.allowedProfiles, []);

// Deep repair children must inherit the original causal plan. Otherwise round 2
// silently loses every allowed profile because PLANS is keyed by the parent.
const deepRepairPath = fileURLToPath(new URL("../../scripts/run_adaptive_deep_repair.py", import.meta.url));
const deepRepairSource = readFileSync(deepRepairPath, "utf8");
assert.match(deepRepairSource, /parent_key = str\(\(candidate\.get\("runtime_repair"\) or \{\}\)\.get\("parent_key"\) or ""\)/);
assert.match(deepRepairSource, /brain\.PLANS\.get\(parent_key or key\)/);

console.log("engine v2 repair brain tests passed");