#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "runtime_repair_second_order",
    ROOT/"scripts/adaptive_runtime/runtime_repair.py",
)
assert spec and spec.loader
runtime=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

expected={
    "transport_request_differential_v1",
    "route_transition_graph_v1",
    "route_peer_transition_replay_v1",
    "terminal_transition_graph_v1",
    "terminal_request_program_inference_v1",
    "candidate_divergence_trace_v1",
    "candidate_request_program_replay_v1",
    "player_protocol_family_replay_v1",
    "media_response_shape_inference_v1",
    "search_contract_inference_v1",
    "search_response_route_binding_v1",
}
for profile in expected:
    assert runtime._is_causal_strategy_profile(profile), profile

config={
    "provider_patches":{
        "synthetic-second-order":{
            "official_site":"https://provider.example",
            "documented_routes":[
                "/search?q={query}",
                "/detail/{slug}",
                "/player/{id}",
                "/api/source/{id}",
                "/episode/{id}/{season}/{episode}",
            ],
        },
    },
    "provider_capabilities":{
        "synthetic-second-order":{
            "strategy":"html_scraper",
            "catalogue_types":["anime"],
        },
    },
}

def candidate(profile:str,failure:str,status:str="CHAIN REACHED"):
    return {
        "canonical_id":"synthetic-second-order",
        "metadata":{
            "name":"Synthetic",
            "supportedTypes":["anime"],
            "baseUrl":"https://provider.example",
        },
        "censusPrior":{"status":status},
        "brain_repair_plan":{
            "failureClass":failure,
            "experimentVariant":4,
            "experimentGeneration":5,
            "postExhaustionStrategyProfile":profile,
            "postExhaustionStrategyMethod":"test-second-order",
            "negativeMemoryMatches":12,
        },
    }

terminal=runtime._adaptive_runtime_options(
    candidate("terminal_transition_graph_v1","chain_terminal_gap"),
    config,
)
assert terminal, terminal
assert terminal["new_strategy_id"]=="terminal_transition_graph_v1",terminal
assert terminal["post_exhaustion_strategy_profile"]=="terminal_transition_graph_v1",terminal
assert terminal["experiment_strategy"]=="learned-family-new-strategy",terminal
assert "/player/{id}" in terminal["direct_paths"],terminal
assert "/api/source/{id}" in terminal["direct_paths"],terminal
assert "/detail/{slug}" not in terminal["direct_paths"],terminal
assert "/film/{slug}" not in terminal["direct_paths"],terminal
assert terminal["search_paths"]==["/search?q={query}"],terminal

candidate_replay=runtime._adaptive_runtime_options(
    candidate("candidate_divergence_trace_v1","candidate_replay_gap","CANDIDATE OK"),
    config,
)
assert candidate_replay, candidate_replay
assert candidate_replay["new_strategy_id"]=="candidate_divergence_trace_v1",candidate_replay
assert "/film/{slug}" not in candidate_replay["direct_paths"],candidate_replay
assert "/api/search?q={query}" not in candidate_replay["search_paths"],candidate_replay

# Regression: the planner's post-g5 decision must survive the snapshot attached
# to the concrete candidate. Without this, matching_profiles() recomputes the g5
# strategy from generation=5 and the allowed second-order profile disappears.
brain_spec=importlib.util.spec_from_file_location(
    "brain_runtime_second_order_snapshot",
    ROOT/"scripts/brain_repair_runtime.py",
)
assert brain_spec and brain_spec.loader
brain=importlib.util.module_from_spec(brain_spec)
brain_spec.loader.exec_module(brain)
post_plan={
    "providerId":"synthetic-second-order",
    "failureClass":"chain_terminal_gap",
    "signature":"sig-post-g5",
    "experimentVariant":4,
    "experimentGeneration":5,
    "experimentGenerationLimit":5,
    "action":"probe-targeted-repair",
    "repairType":"evolved_strategy",
    "learningDisposition":"execute_bounded_evolved_strategy",
    "allowedProfiles":["terminal_transition_graph_v1"],
    "postExhaustionStrategyProfile":"terminal_transition_graph_v1",
    "postExhaustionStrategyMethod":"terminal-response-transition-graph",
    "strategyEscalated":True,
    "baseExperimentExhausted":True,
}
snapshot=brain._plan_snapshot(post_plan)
assert snapshot["postExhaustionStrategyProfile"]=="terminal_transition_graph_v1",snapshot
assert snapshot["postExhaustionStrategyMethod"]=="terminal-response-transition-graph",snapshot
assert snapshot["repairType"]=="evolved_strategy",snapshot
assert snapshot["learningDisposition"]=="execute_bounded_evolved_strategy",snapshot
assert snapshot["experimentGenerationLimit"]==5,snapshot

snap_candidate=candidate("terminal_transition_graph_v1","chain_terminal_gap")
snap_candidate["brain_repair_plan"]=snapshot
profiles=runtime.matching_profiles(
    snap_candidate,
    {"status":"provider_unreachable","evidence":{"streams_playable":0}},
    "async function provider(){}",
    config,
)
assert "terminal_transition_graph_v1" in profiles,profiles

print("Brain second-order runtime strategy contract passed")
