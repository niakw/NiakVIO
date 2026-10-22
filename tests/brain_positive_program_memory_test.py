#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import copy
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
    assert memory.provider_program_fingerprint("demo",path=path)==fingerprints["demo"],fingerprints
    assert skill["source"]=="brain-positive-program-memory"

    # A pre-migration record still has valid terminal proof when it is carried
    # by its bound provider-value step. The new terminal plan is optional.
    legacy=copy.deepcopy(row)
    legacy["compiledProgram"].pop("terminalRequestPlan",None)
    assert memory.validation_rejection_reason(legacy)==""

    # A success flag and playable counter cannot replace a retained terminal
    # recipe. Old poisoned records remain in the source JSON for diagnosis,
    # but must not supply routes, skills, or replay fingerprints.
    stale=copy.deepcopy(legacy)
    stale["providerId"]="stale"
    stale["fingerprint"]="a"*64
    stale["compiledProgram"]["provider"]="stale"
    stale["compiledProgram"]["providerValuePlan"]=[]
    stale["compiledProgram"]["learnedRoutes"]=["/unrelated-promo.mp4"]
    raw_memory=copy.deepcopy(saved2)
    raw_memory["entries"]=[legacy,stale]
    path.write_text(json.dumps(raw_memory),encoding="utf-8")
    before=path.read_bytes()
    loaded=memory.load_memory(path)
    assert [r["providerId"] for r in loaded["entries"]]==["demo"],loaded
    assert loaded["rejectedEntries"]==[{
        "providerId":"stale",
        "fingerprint":"a"*64,
        "reason":"no_provider_owned_terminal_recipe_proof",
    }],loaded
    assert memory.provider_entries("stale",path=path)==[]
    assert memory.provider_routes("stale",path=path)==[]
    assert memory.provider_request_recipes("stale",path=path)==[]
    assert memory.provider_program_fingerprint("stale",path=path)==""
    assert memory.learned_skills(path=path)[skill["id"]]["providers"]==["demo"]
    assert path.read_bytes()==before,"loading evidence must not rewrite source records"

    # Preserve a legitimate independent terminal recipe through compilation,
    # capture and load. It has no bound provider-value step by design.
    independent=copy.deepcopy(program)
    terminal=independent["options"]["request_recipes"][1]
    terminal["route"]="/media/chosen-file"
    terminal["role"]="source"
    terminal["requiredBindings"]=[]
    terminal["headerNames"].append("user-agent")
    independent["options"]["request_recipes"][0]["headerNames"].remove("user-agent")
    independent_compiled=compiler.compile_program(independent,"independent")
    assert independent_compiled["providerValuePlan"]==[]
    assert independent_compiled["terminalRequestPlan"][0]["route"]=="/media/chosen-file"
    independent_accepted={**accepted,"provider":"independent","acceptedProgram":independent}
    independent_path=Path(directory)/"independent.json"
    memory.merge_records([(independent_accepted,independent_compiled)],path=independent_path)
    independent_recipes=memory.provider_request_recipes("independent",path=independent_path)
    assert any(r["route"]=="/media/chosen-file" and r["streamProof"] is True for r in independent_recipes),independent_recipes
    assert memory.provider_program_fingerprint("independent",path=independent_path)
    assert memory.provider_user_agent("independent",path=independent_path)=="NiakVIO-Positive-Memory-Test/1.0"

    # A full terminal plan must retain the search seed within the 32-recipe
    # runtime budget; otherwise its bound/traversal context cannot be rebuilt.
    crowded=copy.deepcopy(independent)
    crowded["options"]["request_recipes"]=[
        crowded["options"]["request_recipes"][0],
        *[{**copy.deepcopy(terminal),"route":f"/media/chosen-{i}"} for i in range(32)],
    ]
    crowded_compiled=compiler.compile_program(crowded,"crowded")
    crowded_path=Path(directory)/"crowded.json"
    memory.merge_records([({**accepted,"provider":"crowded","acceptedProgram":crowded},crowded_compiled)],path=crowded_path)
    crowded_recipes=memory.provider_request_recipes("crowded",path=crowded_path)
    assert len(crowded_recipes)==32,crowded_recipes
    assert crowded_recipes[0]["role"]=="search",crowded_recipes
    assert sum(r["streamProof"] is True for r in crowded_recipes)==31,crowded_recipes

    invalid_proof=copy.deepcopy(independent_compiled)
    invalid_proof["terminalRequestPlan"][0]["base"]="https://www.gstatic.com"
    try:
        memory.positive_record(independent_accepted,invalid_proof)
    except ValueError as exc:
        assert "terminal_recipe_proof" in str(exc),exc
    else:
        raise AssertionError("unowned terminal media must not become positive memory")

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
