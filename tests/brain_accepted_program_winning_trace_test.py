#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

runtime=load("accepted_trace_runtime",ROOT/"scripts/adaptive_runtime/runtime_repair.py")
compiler=load("accepted_trace_compiler",ROOT/"scripts/compile_brain_accepted_program_v3.py")

candidate={"canonical_id":"demo"}
result={
    "status":"healthy",
    "tests":[{
        "fixture":{
            "category":"movie",
            "mediaType":"movie",
            "title":"Synthetic Movie",
            "tmdbId":"999",
        },
        "network_observations":[
            {
                "status":200,
                "ok":True,
                "infrastructure":False,
                "stage":"search",
                "method":"GET",
                "proof_url":"https://provider.example/search?q=Synthetic%20Movie",
                "proof_headers":{"Accept":"text/html"},
                "content_type":"text/html",
                "response_value_hints":[{"key":"id","value":"42"}],
            },
            {
                "status":200,
                "ok":True,
                "infrastructure":False,
                "stage":"player",
                "method":"GET",
                "proof_url":"https://provider.example/api/source/42",
                "proof_headers":{"Referer":"https://provider.example/"},
                "content_type":"application/vnd.apple.mpegurl",
                "response_value_hints":[],
            },
        ],
    }],
}
program={
    "schemaVersion":1,
    "profile":"adaptive_runtime_recovery",
    "executedProfile":"provider_positive_program_replay_v1",
    "revision":5,
    "options":{
        "base_url":"https://provider.example",
        "types":["movie"],
        "search_paths":["/search?q={query}"],
        "direct_paths":[],
        "request_recipes":[],
        "experiment_variant":4,
        "experiment_generation":5,
        "experiment_failure_class":"chain_terminal_gap",
        "new_strategy_id":"provider_positive_program_replay_v1",
    },
}
augmented=runtime.augment_accepted_runtime_program(candidate,result,program)
assert augmented is program
recipes=program["options"]["request_recipes"]
assert len(recipes)==2,recipes
assert recipes[0]["role"]=="search",recipes
assert recipes[0]["route"]=="/search?q={query}",recipes
assert recipes[1]["role"]=="player",recipes
assert recipes[1]["route"]=="/api/source/{binding:id}",recipes
assert recipes[1]["requiredBindings"]==["id"],recipes
assert recipes[1]["streamProof"] is True,recipes

compiled=compiler.compile_program(program,"demo")
assert compiled["searchRequestPlan"],compiled
assert compiled["providerValuePlan"],compiled
plan=compiled["providerValuePlan"][0]
assert plan["searchRoute"]=="/search?q={query}",plan
assert any(step["route"]=="/api/source/{id}" for step in plan["steps"]),plan

# The persistence layer stores names of safe headers only; values from the winning
# trace (including Referer values) never become executable secret/header DATA.
assert "provider.example/" not in repr(compiled.get("providerValuePlan")),compiled

print("Brain accepted winning network trace compiler contract passed")
