#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import { profileGeneratorFingerprintMaterial as generatorMaterial, profileRuntimeFingerprintMaterial as material, postExhaustionStrategyProfiles } from "../src/strategy-fingerprint.mjs";

const source = [
  "prefix",
  "POST_EXHAUSTION_STRATEGY_PROFILES = {",
  '    "route_transition_graph_v2",',
  "}",
  '    if new_strategy_id == "route_transition_graph_v2":',
  '        search_paths = ["parent"]',
  '    elif new_strategy_id == "peer_v1":',
  '        search_paths = ["peer"]',
  "",
  "    shared_runtime_call()",
  "",
].join("\n");
const expanded = source
  .replace('    "route_transition_graph_v2",\n',
    '    "route_transition_graph_v2",\n    "route_transition_graph_v3",\n')
  .replace('    elif new_strategy_id == "peer_v1":',
    '    elif new_strategy_id == "route_transition_graph_v3":\n'
      + '        search_paths = ["new"]\n'
      + '    elif new_strategy_id == "peer_v1":');
for (const existing of ["route_transition_graph_v2", "peer_v1", "html_class_token_exact_v1"]) {
  assert.equal(material(source, existing), material(expanded, existing),
    `new Brain sibling must not invalidate previously executed ${existing}`);
}
assert.notEqual(material(source, "route_transition_graph_v2"),
  material(expanded, "route_transition_graph_v3"));
assert.notEqual(material(source, "route_transition_graph_v2"),
  material(expanded.replace('["parent"]', '["changed"]'), "route_transition_graph_v2"));
assert.notEqual(material(source, "route_transition_graph_v2"),
  material(source.replace("shared_runtime_call()", "changed_shared_runtime_call()"),
    "route_transition_graph_v2"));

// Exercise the actual current repository runtime. New profile registration
// must not change the fingerprint of old Brain Lego strategies.
const live = fs.readFileSync("scripts/adaptive_runtime/runtime_repair.py", "utf8");
assert(live.includes('elif new_strategy_id == "route_transition_graph_v3":'));
const extra = live
  .replace('    "route_transition_graph_v3",\n',
    '    "route_transition_graph_v3",\n    "hypothetical_future_v4",\n')
  .replace('    elif new_strategy_id == "route_transition_graph_v3":',
    '    elif new_strategy_id == "hypothetical_future_v4":\n'
      + "        search_paths = []\n"
      + '    elif new_strategy_id == "route_transition_graph_v3":');
for (const existing of [
  "html_class_token_exact_v1", "route_transition_graph_v1",
  "route_transition_graph_v2", "route_transition_graph_v3",
]) {
  assert.equal(material(live, existing), material(extra, existing),
    `live ${existing} fingerprint changed because of unrelated sibling`);
}
console.log("Brain scoped implementation fingerprint contract passed");


// The adaptive generator is shared by many profiles. The scripted player
// request parser belongs to V2 and to the media-extraction session follow-up
// that composes V2; unrelated profiles must remain isolated.
const generator = fs.readFileSync("scripts/adaptive_runtime/runtime_recovery_generator.py", "utf8");
assert(generator.includes("function bootstrapMediaIntent("));
assert(generator.includes('"scriptedRequestMining": bool(cfg.get("scripted_request_mining", False))'));
const generatorChanged = generator.replace(
  "function bootstrapMediaIntent(url,body){",
  "function bootstrapMediaIntent(url,body){/* fingerprint-test-v2-change */",
);
assert.notEqual(
  generatorMaterial(generator, "document_request_contract_mining_v2"),
  generatorMaterial(generatorChanged, "document_request_contract_mining_v2"),
  "scripted request-contract V2 implementation change must refresh V2",
);
assert.notEqual(
  generatorMaterial(generator, "provider_session_bootstrap_replay_v1"),
  generatorMaterial(generatorChanged, "provider_session_bootstrap_replay_v1"),
  "scripted request parser change must refresh composed session-bootstrap provenance",
);
for (const existing of [
  "document_request_contract_mining_v1",
  "player_media_extractor_v1",
  "runtime_response_salvage_v1",
  "catalogue_inline_token_resolver_v2",
]) {
  assert.equal(
    generatorMaterial(generator, existing),
    generatorMaterial(generatorChanged, existing),
    `V2-only generator change must not resurrect ${existing}`,
  );
}
assert(!generatorMaterial(generator, "document_request_contract_mining_v1").includes("function bootstrapMediaIntent("));
assert(generatorMaterial(generator, "document_request_contract_mining_v2").includes("function bootstrapMediaIntent("));
assert(generatorMaterial(generator, "provider_session_bootstrap_replay_v1").includes("function bootstrapMediaIntent("));
console.log("Brain scripted request-contract V2 fingerprint isolation passed");


const liveV2Runtime = fs.readFileSync("scripts/adaptive_runtime/runtime_repair.py", "utf8");
assert(liveV2Runtime.includes('session_bootstrap_media_followup = ('));
assert(liveV2Runtime.includes('new_strategy_id == "document_request_contract_mining_v2"'));
assert(!material(liveV2Runtime, "document_request_contract_mining_v1").includes("session_bootstrap_media_followup ="));
assert(material(liveV2Runtime, "document_request_contract_mining_v2").includes("scripted_request_mining ="));
assert(material(liveV2Runtime, "provider_session_bootstrap_replay_v1").includes("session_bootstrap_media_followup"));
const liveV2RuntimeChanged = liveV2Runtime.replace(
  'new_strategy_id == "document_request_contract_mining_v2"\n        or session_bootstrap_media_followup',
  'new_strategy_id == "document_request_contract_mining_v2"\n        or session_bootstrap_media_followup /* composed-v2-change */',
);
assert.equal(
  material(liveV2Runtime, "document_request_contract_mining_v1"),
  material(liveV2RuntimeChanged, "document_request_contract_mining_v1"),
  "document request-contract V2 runtime flags must not reset V1",
);
assert.notEqual(
  material(liveV2Runtime, "document_request_contract_mining_v2"),
  material(liveV2RuntimeChanged, "document_request_contract_mining_v2"),
  "V2 runtime change must refresh V2 provenance",
);
assert.notEqual(
  material(liveV2Runtime, "provider_session_bootstrap_replay_v1"),
  material(liveV2RuntimeChanged, "provider_session_bootstrap_replay_v1"),
  "composed session-bootstrap runtime change must refresh its provenance",
);
console.log("Brain scripted request-contract/session runtime fingerprint isolation passed");


// The Learning persistence layer must never carry a hand-maintained copy of
// installed Brain strategies. The Brain registry is authoritative, the adaptive
// executor must contain every installed profile, and Learning derives the same
// set at runtime.
const brainRuntime = fs.readFileSync("scripts/brain_repair_runtime.py", "utf8");
const adaptiveRuntime = fs.readFileSync("scripts/adaptive_runtime/runtime_repair.py", "utf8");
const brainProfiles = postExhaustionStrategyProfiles(brainRuntime);
const adaptiveProfiles = postExhaustionStrategyProfiles(adaptiveRuntime);
assert(brainProfiles.size > 0, "Brain strategy registry must be readable");
assert(brainProfiles.has("catalogue_inline_token_resolver_v2"),
  "promoted resolver V2 missing from authoritative Brain registry");
for (const profile of brainProfiles) {
  assert(adaptiveProfiles.has(profile),
    `adaptive runtime missing installed Brain strategy ${profile}`);
}
const learningLab = fs.readFileSync("engine_v2/scripts/learning-lab.mjs", "utf8");
assert(learningLab.includes("postExhaustionStrategyProfiles("),
  "Learning must derive installed strategies from the authoritative registry");
assert(!learningLab.includes("const POST_EXHAUSTION_STRATEGY_PROFILES = new Set(["),
  "Learning must not reintroduce a duplicated installed-strategy registry");
assert(
  learningLab.indexOf("const root = path.resolve(")
    < learningLab.indexOf("postExhaustionStrategyProfiles("),
  "Learning root must be initialized before registry lookup",
);
console.log("Brain installed strategy registry synchronization contract passed");
