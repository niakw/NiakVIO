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

print("Brain second-order runtime strategy contract passed")
