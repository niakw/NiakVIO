#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/compile_brain_accepted_program_v3.py"
spec=importlib.util.spec_from_file_location("brain_v3_compiler",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

program={
    "schemaVersion":1,
    "profile":"adaptive_runtime_recovery",
    "revision":5,
    "options":{
        "base_url":"https://provider.example",
        "types":["movie"],
        "user_agent":"NiakVIO-Compiler-Test/1.0",
        "search_paths":["/engine/ajax/search.php"],
        "direct_paths":["/api/file/"],
        "experiment_variant":4,
        "experiment_generation":3,
        "experiment_failure_class":"media_extraction_gap",
        "request_recipes":[
            {
                "route":"/engine/ajax/search.php",
                "origin":"https://provider.example",
                "role":"search",
                "method":"POST",
                "bodyKind":"form",
                "body":{"query":"{query}"},
                "headerNames":["accept","content-type","referer"],
                "response":"html-or-text",
                "semanticType":"movie",
                "requiredBindings":[],
                "executable":True,
            },
            {
                "route":"/search?q={query}",
                "origin":"https://www.google.com",
                "role":"search",
                "method":"GET",
                "bodyKind":"none",
                "body":{},
                "headerNames":["accept","referer"],
                "response":"html-or-text",
                "semanticType":"movie",
                "requiredBindings":[],
                "executable":True,
            },
            {
                "route":"/player/{binding:id}",
                "origin":"https://player.example",
                "role":"player",
                "method":"GET",
                "bodyKind":"none",
                "body":{},
                "headerNames":["referer"],
                "response":"html-or-text",
                "semanticType":"movie",
                "requiredBindings":["id"],
                "executable":True,
            },
        ],
    },
}
compiled=mod.compile_program(program,"demo")
assert compiled["provider"]=="demo"
assert compiled["acceptedProgramRevision"]==5
assert compiled["searchRequestPlan"]==[{
    "base":"https://provider.example",
    "route":"/engine/ajax/search.php",
    "requestSpec":{
        "method":"POST",
        "headers":{
            "Accept":"text/html,application/xhtml+xml,application/json,*/*",
            "Referer":"https://provider.example/",
            "Content-Type":"application/x-www-form-urlencoded",
        },
        "bodyKind":"form",
        "body":{"query":"{query}"},
    },
    "responseKind":"html-or-text",
    "streamProof":False,
    "proofModelVersion":6,
    "sourceRole":"brain-accepted-runtime",
    "semanticTypes":["movie"],
}]
assert compiled["experimentVariant"]==4
assert compiled["experimentGeneration"]==3
assert compiled["experimentFailureClass"]=="media_extraction_gap"
assert compiled["learnedRoutes"]==["/engine/ajax/search.php","/api/file/"]
assert all("google." not in row["base"] for row in compiled["searchRequestPlan"])
assert compiled["providerValuePlan"][0]["steps"][0]["route"]=="/player/{id}"
assert compiled["providerValuePlan"][0]["steps"][0]["base"]=="https://player.example"
assert compiled["providerValuePlan"][0]["steps"][0]["responseKind"]=="html-or-text"

overrides={"provider_patches":{"demo":{
    "official_site":"https://provider.example",
    "search_request_plan":[{
        "base":"https://legacy.example",
        "route":"/?q={query}",
        "requestSpec":{"method":"GET","headers":{}},
        "proofModelVersion":5,
        "sourceRole":"historical-positive",
        "semanticTypes":["movie"],
    }],
    "provider_value_plan":[{
        "searchBase":"https://legacy.example",
        "searchRoute":"/?q={query}",
        "searchRequestSpec":{"method":"GET","headers":{}},
        "steps":[{"base":"https://legacy.example","route":"/watch/{id}","requestSpec":{"method":"GET","headers":{}},"role":"player"}],
        "semanticTypes":["movie"],
        "proofModelVersion":5,
        "sourceRole":"historical-positive",
    }],
}}}
original=copy.deepcopy(overrides)
proposed=mod.apply_compiled(overrides,compiled)
patch=proposed["provider_patches"]["demo"]
assert patch["official_site"]=="https://provider.example"
assert patch["learned_routes"][0:2]==["/engine/ajax/search.php","/api/file/"]
assert patch["brain_accepted_program"]["experiment_generation"]==3
assert patch["search_request_plan"][0]==compiled["searchRequestPlan"][0]
assert patch["search_request_plan"][1]["sourceRole"]=="historical-positive"
assert patch["provider_value_plan"][0]==compiled["providerValuePlan"][0]
assert patch["provider_value_plan"][1]["sourceRole"]=="historical-positive"
assert patch["brain_accepted_program"]["source"]=="strict-brain-accepted-runtime-program"
assert overrides==original

report={
    "acceptedRepairs":[{
        "provider":"demo",
        "profile":"adaptive_runtime_recovery",
        "acceptedProgram":program,
    }],
    "waves":[{
        "batches":[{
            "accepted":[{
                "provider":"demo",
                "acceptedProgram":program,
            }]
        }]
    }],
}
assert mod.find_accepted_program(report,"demo")==program

bad=json.loads(json.dumps(program))
bad["options"]["request_recipes"][1]["requiredBindings"]=["token"]
try:
    mod.compile_program(bad,"demo")
except ValueError:
    pass
else:
    raise AssertionError("unsupported provider-local token binding was persisted")

body_bound=json.loads(json.dumps(program))
body_bound["options"]["request_recipes"][1]["route"]="/player"
body_bound["options"]["request_recipes"][1]["bodyKind"]="form"
body_bound["options"]["request_recipes"][1]["method"]="POST"
body_bound["options"]["request_recipes"][1]["body"]={"id":"{binding:id}"}
try:
    mod.compile_program(body_bound,"demo")
except ValueError:
    pass
else:
    raise AssertionError("binding that ProviderBase cannot represent losslessly was persisted")

print("Brain accepted runtime program -> Provider v3 DATA compiler contract passed")
