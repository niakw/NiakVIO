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
    "provider_positive_program_replay_v1",
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

# Regression: a pre-exhaustion Brain-LLM advisor profile must be executable, not
# filtered into profile_unavailable. The snapshot carries the advisor decision
# and adaptive runtime materializes that exact causal profile.
llm_plan={
    "providerId":"synthetic-second-order",
    "failureClass":"route_proven_gap",
    "signature":"sig-llm",
    "experimentVariant":0,
    "experimentGeneration":1,
    "action":"probe-targeted-repair",
    "allowedProfiles":["proven_route_terminal_traversal_v1"],
    "llmAdvisorApplied":True,
    "llmAdvisorStrategy":"search_detail_player_terminal_traversal",
    "llmAdvisorProfile":"proven_route_terminal_traversal_v1",
    "llmAdvisorSourceFailureClass":"route_proven_gap",
    "llmAdvisorFailureCompatibility":"exact",
    "llmAdvisorExperimentFingerprint":"a"*64,
    "llmAdvisorExperiment":{
        "routePolicy":"owned_only",
        "recipePolicy":"current_only",
        "roleOrder":["detail","player","source","api"],
        "terminalOnly":True,
        "aliasSearch":False,
        "responseSalvage":False,
        "documentRequestMining":False,
        "sessionBootstrap":False,
        "maxDepth":3,
        "maxPages":10,
        "maxEmbeds":10,
        "maxRecipePasses":3,
    },
}
llm_snapshot=brain._plan_snapshot(llm_plan)
assert llm_snapshot["llmAdvisorApplied"] is True,llm_snapshot
assert llm_snapshot["llmAdvisorProfile"]=="proven_route_terminal_traversal_v1",llm_snapshot
llm_candidate=candidate("","route_proven_gap","ROUTE PROVEN")
llm_candidate["brain_repair_plan"]=llm_snapshot
llm_options=runtime._adaptive_runtime_options(llm_candidate,config)
assert llm_options,llm_options
assert llm_options["new_strategy_id"]=="proven_route_terminal_traversal_v1",llm_options
llm_profiles=runtime.matching_profiles(
    llm_candidate,
    {"status":"provider_unreachable","evidence":{"streams_playable":0}},
    "async function provider(){}",
    config,
)
assert "proven_route_terminal_traversal_v1" in llm_profiles,llm_profiles

old_positive_routes=runtime.positive_program_routes
old_positive_recipes=runtime.positive_program_request_recipes
old_positive_user_agent=runtime.positive_program_user_agent
old_positive_fingerprint=runtime.positive_program_fingerprint
try:
    runtime.positive_program_routes=lambda provider_id:[
        "/search.php?q={query}",
        "/api/file/{id}",
    ]
    runtime.positive_program_request_recipes=lambda provider_id:[{
        "route":"/search.php?q={query}",
        "origin":"https://provider.example",
        "role":"search",
        "method":"GET",
        "bodyKind":"none",
        "body":{},
        "headerNames":["accept","user-agent"],
        "response":"html-or-text",
        "semanticType":"anime",
        "streamProof":False,
        "requiredBindings":[],
        "executable":True,
        "source":"positive-program-memory",
    }]
    runtime.positive_program_user_agent=lambda provider_id:"Positive-Replay-Test/1.0"
    runtime.positive_program_fingerprint=lambda provider_id:"f"*64

    positive_candidate=candidate(
        "provider_positive_program_replay_v1",
        "chain_terminal_gap",
    )
    positive_candidate["brain_repair_plan"]["positiveProgramFingerprint"]="f"*64
    # Simulate a stale/mixed plan from an older orchestration layer: strict
    # positive replay must still outrank an attached LLM advisor at runtime.
    positive_candidate["brain_repair_plan"]["providerPositiveProgramReplay"]=True
    positive_candidate["brain_repair_plan"]["llmAdvisorApplied"]=True
    positive_candidate["brain_repair_plan"]["llmAdvisorProfile"]="chain_terminal_extractor_v1"
    positive_replay=runtime._adaptive_runtime_options(
        positive_candidate,
        config,
    )
    assert positive_replay,positive_replay
    assert positive_replay["new_strategy_id"]=="provider_positive_program_replay_v1",positive_replay
    assert positive_replay["positive_program_replay"] is True,positive_replay
    assert positive_replay["positive_program_fingerprint"]=="f"*64,positive_replay
    assert positive_replay["search_paths"]==["/search.php?q={query}"],positive_replay
    assert positive_replay["direct_paths"]==["/api/file/{id}"],positive_replay
    assert len(positive_replay["request_recipes"])==1,positive_replay
    assert positive_replay["request_recipes"][0]["source"]=="positive-program-memory",positive_replay
    assert "/film/{slug}" not in positive_replay["direct_paths"],positive_replay
    assert "/api/search?q={query}" not in positive_replay["search_paths"],positive_replay

    stale_candidate=candidate(
        "provider_positive_program_replay_v1",
        "chain_terminal_gap",
    )
    stale_candidate["brain_repair_plan"]["positiveProgramFingerprint"]="e"*64
    assert runtime._adaptive_runtime_options(stale_candidate,config) is None
finally:
    runtime.positive_program_routes=old_positive_routes
    runtime.positive_program_request_recipes=old_positive_recipes
    runtime.positive_program_user_agent=old_positive_user_agent
    runtime.positive_program_fingerprint=old_positive_fingerprint

print("Brain second-order runtime strategy contract passed")
