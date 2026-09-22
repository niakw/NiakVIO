#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

compiler=load("brain_positive_compiler",ROOT/"scripts/compile_brain_accepted_program_v3.py")
memory=load("brain_positive_memory",ROOT/"scripts/brain_positive_program_memory.py")

program={
    "schemaVersion":1,
    "profile":"adaptive_runtime_recovery",
    "revision":5,
    "options":{
        "base_url":"https://provider.example",
        "types":["movie"],
        "user_agent":"NiakVIO-Positive-Memory-Test/1.0",
        "search_paths":["/search?q={query}"],
        "direct_paths":["/api/file/"],
        "experiment_variant":4,
        "experiment_generation":3,
        "experiment_failure_class":"media_extraction_gap",
        "request_recipes":[
            {
                "route":"/search?q={query}",
                "origin":"https://provider.example",
                "role":"search",
                "method":"GET",
                "bodyKind":"none",
                "body":{},
                "headerNames":["accept","referer","user-agent"],
                "response":"html-or-text",
                "semanticType":"movie",
                "requiredBindings":[],
                "streamProof":False,
                "executable":True,
            },
            {
                "route":"/api/player/{binding:id}",
                "origin":"https://provider.example",
                "role":"player",
                "method":"GET",
                "bodyKind":"none",
                "body":{},
                "headerNames":["accept","referer"],
                "response":"json",
                "semanticType":"movie",
                "requiredBindings":["id"],
                "streamProof":True,
                "executable":True,
            },
            {
                "route":"/search?q={query}",
                "origin":"https://www.google.com",
                "role":"search",
                "method":"GET",
                "bodyKind":"none",
                "body":{},
                "headerNames":["accept"],
                "response":"html-or-text",
                "semanticType":"movie",
                "requiredBindings":[],
                "streamProof":False,
                "executable":True,
            },
        ],
    },
}
compiled=compiler.compile_program(program,"demo")
assert compiled["experimentGeneration"]==3
assert compiled["learnedRoutes"]==["/search?q={query}","/api/file/"]
assert all("google." not in value for value in compiled["origins"])
assert all("google." not in row["base"] for row in compiled["searchRequestPlan"])
assert compiled["providerValuePlan"][0]["steps"][0]["responseKind"]=="json"
assert compiled["providerValuePlan"][0]["steps"][0]["streamProof"] is True

accepted={
    "provider":"demo",
    "profile":"adaptive_runtime_recovery",
    "reason":"strict_playable_stream_improvement",
    "statusBefore":"no_streams",
    "statusAfter":"healthy",
    "playableBefore":0,
    "playableAfter":1,
    "brainPlan":{
        "failureClass":"media_extraction_gap",
        "signature":"demo-positive-signature",
        "experimentVariant":4,
        "experimentGeneration":3,
    },
    "acceptedProgram":program,
}

with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/"positive.json"
    saved=memory.merge_records([(accepted,compiled)],path=path)
    assert saved["role"]=="validated-positive-program-prior-only"
    assert saved["safety"]["publicationAuthority"] is False
    assert saved["safety"]["candidateJavaScriptPersisted"] is False
    assert len(saved["entries"])==1
    row=saved["entries"][0]
    assert row["providerId"]=="demo"
    assert row["signature"]=="demo-positive-signature"
    assert row["experimentGeneration"]==3
    assert row["playableBefore"]==0 and row["playableAfter"]==1

    # Idempotent merge: rerunning the same successful evidence does not bloat memory.
    saved2=memory.merge_records([(accepted,compiled)],path=path)
    assert len(saved2["entries"])==1

    routes=memory.provider_routes("demo",path=path)
    assert routes==["/search?q={query}","/api/file/"]
    assert memory.provider_user_agent("demo",path=path)=="NiakVIO-Positive-Memory-Test/1.0"

    recipes=memory.provider_request_recipes("demo",path=path)
    assert any(row["role"]=="search" and row["route"]=="/search?q={query}" for row in recipes)
    player=next(row for row in recipes if row["role"]=="player")
    assert player["route"]=="/api/player/{binding:id}"
    assert player["requiredBindings"]==["id"]
    assert player["response"]=="json"
    assert player["streamProof"] is True
    assert all("google." not in str(row.get("origin") or "") for row in recipes)

    skills=memory.learned_skills(path=path)
    skill=skills["media_extraction_gap:adaptive_runtime_recovery"]
    assert skill["validated"] is True
    assert skill["maturity"]=="experimental"
    assert skill["providers"]==["demo"]
    assert skill["autoApply"] is False
    assert skill["sameProviderPositiveProgram"] is True
    fingerprints=skill["positiveProgramFingerprintsByProvider"]
    assert set(fingerprints)=={"demo"},fingerprints
    assert len(fingerprints["demo"])==64,fingerprints
    assert all(ch in "0123456789abcdef" for ch in fingerprints["demo"]),fingerprints
    assert skill["source"]=="brain-positive-program-memory"

adaptive=(ROOT/"scripts/adaptive_runtime/runtime_repair.py").read_text(encoding="utf-8")
base=(ROOT/"scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
repair=(ROOT/"scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
workflow=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
assert "positive_program_routes(provider_id)" in adaptive
assert "positive_program_request_recipes(provider_id)" in adaptive
assert "positive_program_user_agent(provider_id)" in adaptive
assert '"positiveProgramUserAgent": bool(validated_positive_user_agent)' in adaptive
assert '"user_agent": validated_positive_user_agent or network_hints["user_agent"]' in adaptive
assert "positive_program_learned_skills()" in base
assert "merge_positive_program_records" in repair
assert "automation/brain-positive-program-memory.json" in workflow
assert 'git add automation/brain-positive-program-memory.json' in workflow

print("Brain durable positive program memory contract passed")
