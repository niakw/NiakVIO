#!/usr/bin/env python3
from __future__ import annotations

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
    "proofModelVersion":6,
    "sourceRole":"brain-accepted-runtime",
    "semanticTypes":["movie"],
}]
assert compiled["providerValuePlan"][0]["steps"][0]["route"]=="/player/{id}"
assert compiled["providerValuePlan"][0]["steps"][0]["base"]=="https://player.example"

overrides={"provider_patches":{"demo":{"official_site":"https://provider.example"}}}
proposed=mod.apply_compiled(overrides,compiled)
patch=proposed["provider_patches"]["demo"]
assert patch["official_site"]=="https://provider.example"
assert patch["search_request_plan"]==compiled["searchRequestPlan"]
assert patch["provider_value_plan"]==compiled["providerValuePlan"]
assert patch["brain_accepted_program"]["source"]=="strict-brain-accepted-runtime-program"
assert "search_request_plan" not in overrides["provider_patches"]["demo"]

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
