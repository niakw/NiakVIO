#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"

candidate={
    "canonical_id":"synthetic-generation",
    "censusPrior":{
        "status":"CHAIN REACHED",
        "dominantIssue":"provider_network_zero_result",
        "evidenceDepth":["anime=chain_reached"],
    },
    "metadata":{"supportedTypes":["anime"]},
}
result={
    "status":"no_streams",
    "evidence":{"streams_playable":0,"streams_returned":0},
    "tests":[{
        "fixture":{"mediaType":"anime","category":"anime","title":"Synthetic"},
        "failure_class":"content_lookup_completed_no_streams",
        "status":"no_streams",
        "network_observations":[],
        "streams_playable":0,
        "stream_count":0,
    }],
}
policy={
    "production":{
        "negativeExperimentMemory":{
            "rotateExperimentAfterFailures":1,
            "maxVariantsPerSignature":5,
            "finalVariantGeneration":2,
            "maxLearningGenerationsPerSignature":5,
        },
        "maxHypotheses":3,
        "maxMutationsPerProvider":2,
        "maxRepeatedSignature":2,
        "maxGeneratedBytesPerProvider":180000,
        "maxElapsedMsPerProvider":45000,
    },
    "skillMaturity":{},
}

def row(variant:int,generation:int=1):
    profile="adaptive_runtime_recovery"
    if variant==4 and generation>=2:
        profile="chain_terminal_extractor_v1" if generation==2 else f"chain_terminal_extractor_v1_g{generation}"
    return {
        "providerId":"synthetic-generation",
        "failureClass":"chain_terminal_gap",
        "experimentVariant":variant,
        "experimentGeneration":generation,
        "profile":profile,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
    }

def plan(memory, mode="repair"):
    payload={
        "mode":mode,
        "policy":policy,
        "learnedSkills":{},
        "negativeMemory":memory,
        "items":[{"key":"published:synthetic-generation","candidate":candidate,"result":result,"state":{}}],
    }
    completed=subprocess.run(
        ["node",str(PLANNER)],cwd=ROOT,input=json.dumps(payload),
        capture_output=True,text=True,check=True,timeout=20,
    )
    parsed=json.loads(completed.stdout)
    return next(iter((parsed.get("plans") or {}).values()))

# v0-v3 historical failures remain authoritative. Old v4 belongs to generation 1
# and must not exhaust materially new generation 2 semantics.
old=[row(0),row(1),row(2),row(3),row(4,1)]
fresh=plan(old)
assert fresh["experimentVariant"]==4,fresh
assert fresh["experimentGeneration"]==2,fresh
assert fresh["experimentExhausted"] is False,fresh
assert fresh["action"]=="probe-targeted-repair",fresh
assert fresh["allowedProfiles"]==["chain_terminal_extractor_v1"],fresh
assert fresh["negativeMemoryMatches"]==5,fresh

# Once the current generation itself fails, all five variants are exhausted again.
exhausted=plan([*old,row(4,2)])
assert exhausted["experimentExhausted"] is True,exhausted
assert exhausted["experimentGeneration"]==2,exhausted
assert exhausted["repairScope"]=="deferred",exhausted
assert exhausted["action"]=="deferred_retry",exhausted
assert exhausted["experimentGenerationLimit"]==2,exhausted

# Learning owns bounded strategy evolution after production g2 is exhausted.
# Each failed final generation advances to a genuinely new generation until the
# configured limit, then turns into explicit architecture debt.
learning_g3=plan([*old,row(4,2)],"learning")
assert learning_g3["experimentVariant"]==4,learning_g3
assert learning_g3["experimentGeneration"]==3,learning_g3
assert learning_g3["experimentExhausted"] is False,learning_g3
assert learning_g3["action"]=="probe-targeted-repair",learning_g3
assert learning_g3["experimentGenerationLimit"]==5,learning_g3

learning_g4=plan([*old,row(4,2),row(4,3)],"learning")
assert learning_g4["experimentGeneration"]==4,learning_g4
assert learning_g4["experimentExhausted"] is False,learning_g4

learning_g5=plan([*old,row(4,2),row(4,3),row(4,4)],"learning")
assert learning_g5["experimentGeneration"]==5,learning_g5
assert learning_g5["experimentExhausted"] is False,learning_g5

learning_exhausted=plan([*old,row(4,2),row(4,3),row(4,4),row(4,5)],"learning")
assert learning_exhausted["experimentGeneration"]==5,learning_exhausted
assert learning_exhausted["experimentExhausted"] is True,learning_exhausted
assert learning_exhausted["repairScope"]=="learning",learning_exhausted
assert learning_exhausted["repairType"]=="architecture_gap",learning_exhausted
assert learning_exhausted["action"]=="collect-more-evidence",learning_exhausted
assert learning_exhausted["exitReason"]=="learning_generations_exhausted",learning_exhausted
assert learning_exhausted["learningDisposition"]=="propose_new_or_evolved_core_type",learning_exhausted

# Python memory plumbing must preserve old rows as generation 1 and explicit new rows as 2.
spec=importlib.util.spec_from_file_location("brain_runtime",ROOT/"scripts/brain_repair_runtime.py")
assert spec and spec.loader
brain=importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)
with tempfile.TemporaryDirectory() as td:
    path=Path(td)/"memory.json"
    path.write_text(json.dumps({"schemaVersion":1,"entries":[row(4,1),row(4,2)]}),encoding="utf-8")
    prior=brain.REPAIR_MEMORY_PATH
    brain.REPAIR_MEMORY_PATH=path
    try:
        sent=brain.planner_negative_memory("repair")
    finally:
        brain.REPAIR_MEMORY_PATH=prior
    assert [x["experimentGeneration"] for x in sent]==[1,2],sent

# Orchestrator exhaustion must use the same generation rule.
spec2=importlib.util.spec_from_file_location("brain_orchestrator",ROOT/"scripts/run_provider_brain_repair.py")
assert spec2 and spec2.loader
orch=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(orch)
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    mem=td/"memory.json"
    pol=td/"policy.json"
    pol.write_text(json.dumps(policy),encoding="utf-8")
    original_mem,original_policy=orch.REPAIR_MEMORY,orch.BRAIN_POLICY
    orch.REPAIR_MEMORY,orch.BRAIN_POLICY=mem,pol
    summary={"plans":{"published:synthetic-generation":{
        "providerId":"synthetic-generation",
        "failureClass":"chain_terminal_gap",
        "signature":"sig",
        "allowedProfiles":["chain_terminal_extractor_v1"],
        "experimentVariant":4,
        "experimentGeneration":2,
        "experimentVariantCount":5,
    }}}
    memory_rows=[]
    for v in range(5):
        memory_rows.append({
            **row(v,1),
            "signature":"sig",
            "profile":"chain_terminal_extractor_v1" if v == 4 else "adaptive_runtime_recovery",
        })
    mem.write_text(json.dumps({"schemaVersion":1,"entries":memory_rows}),encoding="utf-8")
    try:
        assert "synthetic-generation" not in orch.exhausted_from_negative_memory(summary)
        memory_rows.append({
            **row(4,2),
            "signature":"sig",
            "profile":"chain_terminal_extractor_v1",
        })
        mem.write_text(json.dumps({"schemaVersion":1,"entries":memory_rows}),encoding="utf-8")
        assert "synthetic-generation" in orch.exhausted_from_negative_memory(summary)
    finally:
        orch.REPAIR_MEMORY,orch.BRAIN_POLICY=original_mem,original_policy

print("Brain final experiment generation contract passed")
