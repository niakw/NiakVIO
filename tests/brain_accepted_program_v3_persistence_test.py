#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("brain_orchestrator_v3_persist",ROOT/"scripts/run_provider_brain_repair.py")
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
        "user_agent":"NiakVIO-Persist-Test/1.0",
        "request_recipes":[
            {
                "route":"/search",
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
                "origin":"https://provider.example",
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

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    overrides=root/"provider-overrides.json"
    overrides.write_text(json.dumps({
        "provider_patches":{
            "demo":{
                "official_site":"https://provider.example",
                "search_request_plan":[{
                    "base":"https://legacy.example",
                    "route":"/?q={query}",
                    "requestSpec":{"method":"GET","headers":{}},
                    "proofModelVersion":5,
                    "sourceRole":"historical-positive",
                    "semanticTypes":["movie"],
                }],
            }
        }
    }),encoding="utf-8")
    positive=root/"brain-positive-program-memory.json"
    old_overrides=mod.OVERRIDES
    old_positive=mod.POSITIVE_MEMORY
    mod.OVERRIDES=overrides
    mod.POSITIVE_MEMORY=positive
    try:
        accepted=[{
            "provider":"demo",
            "profile":"adaptive_runtime_recovery",
            "reason":"strict_playable_stream_improvement",
            "playableBefore":0,
            "playableAfter":1,
            "brainPlan":{
                "failureClass":"media_extraction_gap",
                "signature":"demo-signature",
                "experimentVariant":2,
                "experimentGeneration":1,
            },
            "acceptedProgram":program,
        }]
        compiled,rejected=mod.persist_accepted_programs(accepted)
        assert compiled=={"demo"},compiled
        assert rejected=={},rejected
        assert accepted[0]["v3ProgramPersistence"]["status"]=="compiled"
        assert accepted[0]["positiveProgramMemory"]["status"]=="persisted"
        positive_saved=json.loads(positive.read_text(encoding="utf-8"))
        assert positive_saved["role"]=="validated-positive-program-prior-only"
        assert positive_saved["entries"][0]["providerId"]=="demo"
        assert positive_saved["entries"][0]["signature"]=="demo-signature"
        assert positive_saved["entries"][0]["playableAfter"]==1
        saved=json.loads(overrides.read_text(encoding="utf-8"))
        patch=saved["provider_patches"]["demo"]
        assert patch["search_request_plan"][0]["sourceRole"]=="brain-accepted-runtime"
        assert patch["search_request_plan"][1]["sourceRole"]=="historical-positive"
        assert patch["provider_value_plan"][0]["steps"][0]["route"]=="/player/{id}"

        before=overrides.read_text(encoding="utf-8")
        bad=json.loads(json.dumps(program))
        bad["options"]["request_recipes"][1]["requiredBindings"]=["token"]
        rejected_rows=[{"provider":"bad_demo","acceptedProgram":bad}]
        compiled2,rejected2=mod.persist_accepted_programs(rejected_rows)
        assert compiled2==set(),compiled2
        assert "bad-demo" in rejected2,rejected2
        assert rejected_rows[0]["v3ProgramPersistence"]["status"]=="rejected"
        assert overrides.read_text(encoding="utf-8")==before
    finally:
        mod.OVERRIDES=old_overrides
        mod.POSITIVE_MEMORY=old_positive

source=(ROOT/"scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
assert "blocked_fixed = accepted_program_providers - compiled_this_wave" in source
assert "effective_fixed_this_wave = fixed_this_wave - blocked_fixed" in source
assert "materialize_targets_this_wave" in source
assert '"acceptedProgramCompileFailures"' in source
assert "merge_positive_program_records" in source
assert "positiveProgramMemory" in source

print("Brain accepted program v3 persistence/orchestration contract passed")
