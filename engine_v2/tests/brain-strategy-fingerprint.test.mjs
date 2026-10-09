#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import { profileRuntimeFingerprintMaterial as material } from "../src/strategy-fingerprint.mjs";

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
