#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"

candidate={
    "canonical_id":"synthetic-llm-advisor",
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
guidance=[{
    "providerId":"synthetic-llm-advisor",
    "failureClass":"route_proven_gap",
    "targetLayer":"provider",
    "strategy":"search_detail_player_terminal_traversal",
    "profile":"proven_route_terminal_traversal_v1",
    "confidence":0.94,
    "priorOnly":True,
}]

def plan(mode:str,memory:list[dict]|None=None):
    payload={
        "mode":mode,
        "policy":policy,
        "learnedSkills":{},
        "historicalSolutions":[],
        "llmGuidance":guidance,
        "negativeMemory":memory or [],
        "items":[{
            "key":"published:synthetic-llm-advisor",
            "candidate":candidate,
            "result":result,
            "state":{},
        }],
    }
    completed=subprocess.run(
        ["node",str(PLANNER)],
        cwd=ROOT,input=json.dumps(payload),capture_output=True,text=True,check=True,timeout=20,
    )
    return next(iter((json.loads(completed.stdout).get("plans") or {}).values()))

learning=plan("learning")
assert learning["experimentVariant"]==0,learning
assert learning["llmAdvisorApplied"] is True,learning
assert learning["llmAdvisorStrategy"]=="search_detail_player_terminal_traversal",learning
assert learning["llmAdvisorProfile"]=="proven_route_terminal_traversal_v1",learning
assert learning["llmAdvisorConfidence"]==0.94,learning
assert learning["allowedProfiles"][0]=="proven_route_terminal_traversal_v1",learning

# Exact profile debt blocks the advisor. The deterministic Brain resumes its
# ordinary bounded profile selection instead of replaying a known failure.
blocked=plan("learning",[{
    "providerId":"synthetic-llm-advisor",
    "failureClass":"route_proven_gap",
    "experimentVariant":4,
    "experimentGeneration":1,
    "profile":"proven_route_terminal_traversal_v1",
    "failures":1,
    "consecutiveFailures":1,
    "successes":0,
}])
assert blocked["llmAdvisorApplied"] is False,blocked
assert blocked["llmAdvisorProfile"]=="",blocked
assert blocked["allowedProfiles"][0]!="proven_route_terminal_traversal_v1",blocked

# Production Repair never consumes LLM advice. The LLM is an acceleration prior
# for the sandbox Learning path only.
production=plan("repair")
assert production["llmAdvisorApplied"] is False,production
assert production["llmAdvisorProfile"]=="",production
assert production["allowedProfiles"]==["adaptive_runtime_recovery"],production

brain=(ROOT/"scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
assert '"llmGuidance": planner_llm_guidance()' in brain
assert "rawMutationContentRetained" in brain

print("Brain LLM advisor execution contract passed")
