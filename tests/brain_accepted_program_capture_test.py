#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/"scripts"
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location("deep_repair_capture",SCRIPTS/"deep_repair_loop.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

candidate={
    "local_patches":[
        {"type":"patch_profile","profile":"other","phase":"runtime","options":{"secret":"drop"}},
        {
            "type":"patch_profile",
            "profile":"provider_positive_program_replay_v1",
            "engine":"adaptive_runtime_recovery",
            "phase":"runtime",
            "revision":5,
            "options":{
                "base_url":"https://provider.example",
                "types":["movie"],
                "search_paths":["/search?q={query}"],
                "direct_paths":["/player/{id}"],
                "request_recipes":[{
                    "route":"/api/search?q={query}",
                    "origin":"https://provider.example",
                    "role":"search",
                    "method":"GET",
                    "bodyKind":"none",
                    "body":{},
                    "requiredBindings":[],
                    "source":"current-observation",
                    "executable":True,
                }],
                "repair_focus":"media-extraction",
                "experiment_variant":2,
                "experiment_failure_class":"media_extraction_gap",
                "max_pages":12,
                "unknown_secret_like_field":"must-not-persist",
            },
        },
    ]
}
program=mod.accepted_runtime_program(candidate, {"status":"healthy"})
assert program is not None
assert program["profile"]=="adaptive_runtime_recovery"
assert program["executedProfile"]=="provider_positive_program_replay_v1"
assert program["revision"]==5
opts=program["options"]
assert opts["base_url"]=="https://provider.example"
assert opts["request_recipes"][0]["source"]=="current-observation"
assert opts["experiment_failure_class"]=="media_extraction_gap"
assert "unknown_secret_like_field" not in opts
assert "secret" not in repr(program)

source=(SCRIPTS/"deep_repair_loop.py").read_text(encoding="utf-8")
assert 'updated_candidate["accepted_runtime_program"] = accepted_program' in source
assert '"accepted_program": copy.deepcopy(updated_candidate.get("accepted_runtime_program") or {})' in source

print("Brain accepted runtime program capture contract passed")
