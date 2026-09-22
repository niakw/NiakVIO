#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"

candidate={
    "canonical_id":"synthetic-history",
    "censusPrior":{
        "status":"ROUTE PROVEN",
        "dominantIssue":"provider_network_zero_result",
        "evidenceDepth":["movie=lookup_only"],
    },
    "metadata":{"supportedTypes":["movie"]},
}
result={
    "status":"no_streams",
    "evidence":{"streams_playable":0,"streams_returned":0},
    "tests":[{
        "fixture":{"mediaType":"movie","category":"movie","title":"Synthetic"},
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
def mem(variant:int):
    return {
        "providerId":"synthetic-history",
        "failureClass":"route_proven_gap",
        "experimentVariant":variant,
        "experimentGeneration":1,
        "profile":"adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
    }

payload={
    "mode":"learning",
    "policy":policy,
    "learnedSkills":{},
    "historicalSolutions":[{
        "id":"hist-current-route-proven-gap",
        "failureClass":"route_proven_gap",
        "solutionClass":"search_detail_player_terminal_traversal",
        "providers":["global"],
        "priorOnly":True,
    }],
    # v0-v2 have failed. Without executable historical transfer the next step
    # would be generic expanded-discovery v3.
    "negativeMemory":[mem(0),mem(1),mem(2)],
    "items":[{
        "key":"published:synthetic-history",
        "candidate":candidate,
        "result":result,
        "state":{},
    }],
}
completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,
    input=json.dumps(payload),
    capture_output=True,
    text=True,
    check=True,
    timeout=20,
)
parsed=json.loads(completed.stdout)
plan=next(iter((parsed.get("plans") or {}).values()))
assert plan["experimentVariant"]==3,plan
assert plan["experimentExhausted"] is False,plan
assert plan["action"]=="probe-targeted-repair",plan
assert plan["historicalStrategyProfile"]=="proven_route_terminal_traversal_v1",plan
assert plan["historicalStrategyCase"]=="hist-current-route-proven-gap",plan
assert plan["historicalSolutionClass"]=="search_detail_player_terminal_traversal",plan
assert plan["allowedProfiles"][0]=="proven_route_terminal_traversal_v1",plan

# Production must not shortcut its normal bounded variant order from a prior.
payload["mode"]="repair"
completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,
    input=json.dumps(payload),
    capture_output=True,
    text=True,
    check=True,
    timeout=20,
)
production=next(iter((json.loads(completed.stdout).get("plans") or {}).values()))
assert production["experimentVariant"]==3,production
assert production.get("historicalStrategyProfile") in {"",None},production
assert production["allowedProfiles"]==["adaptive_runtime_recovery"],production

runtime=(ROOT/"scripts/adaptive_runtime/runtime_repair.py").read_text(encoding="utf-8")
brain=(ROOT/"scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
assert 'brain_plan.get("historicalStrategyProfile")' in runtime
assert '"historicalSolutions": planner_historical_solutions()' in brain
assert '"historicalStrategyProfile": str(plan.get("historicalStrategyProfile") or "")' in brain

print("Brain historical solution execution contract passed")
