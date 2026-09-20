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
    return {
        "providerId":"synthetic-generation",
        "failureClass":"chain_terminal_gap",
        "experimentVariant":variant,
        "experimentGeneration":generation,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
    }

def plan(memory):
    payload={
        "mode":"repair",
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
assert fresh["negativeMemoryMatches"]==4,fresh

# Once the current generation itself fails, all five variants are exhausted again.
exhausted=plan([*old,row(4,2)])
assert exhausted["experimentExhausted"] is True,exhausted
assert exhausted["experimentGeneration"]==2,exhausted
assert exhausted["repairScope"]=="deferred",exhausted
assert exhausted["action"]=="deferred_retry",exhausted

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
        "allowedProfiles":["adaptive_runtime_recovery"],
        "experimentVariant":4,
        "experimentGeneration":2,
        "experimentVariantCount":5,
    }}}
    memory_rows=[]
    for v in range(5):
        memory_rows.append({
            **row(v,1),
            "signature":"sig",
            "profile":"adaptive_runtime_recovery",
        })
    mem.write_text(json.dumps({"schemaVersion":1,"entries":memory_rows}),encoding="utf-8")
    try:
        assert "synthetic-generation" not in orch.exhausted_from_negative_memory(summary)
        memory_rows.append({
            **row(4,2),
            "signature":"sig",
            "profile":"adaptive_runtime_recovery",
        })
        mem.write_text(json.dumps({"schemaVersion":1,"entries":memory_rows}),encoding="utf-8")
        assert "synthetic-generation" in orch.exhausted_from_negative_memory(summary)
    finally:
        orch.REPAIR_MEMORY,orch.BRAIN_POLICY=original_mem,original_policy

print("Brain final experiment generation contract passed")
