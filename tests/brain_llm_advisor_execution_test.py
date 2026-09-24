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

def plan(mode:str,memory:list[dict]|None=None,guidance_rows:list[dict]|None=None):
    payload={
        "mode":mode,
        "policy":policy,
        "learnedSkills":{},
        "historicalSolutions":[],
        "llmGuidance":guidance if guidance_rows is None else guidance_rows,
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
assert learning["llmAdvisorFailureCompatibility"]=="exact",learning
assert learning["llmAdvisorSourceFailureClass"]=="route_proven_gap",learning
assert learning["allowedProfiles"][0]=="proven_route_terminal_traversal_v1",learning

family_guidance=[{**guidance[0],"failureClass":"search_gap"}]
family=plan("repair",guidance_rows=family_guidance)
assert family["llmAdvisorApplied"] is True,family
assert family["llmAdvisorFailureCompatibility"]=="family",family
assert family["llmAdvisorSourceFailureClass"]=="search_gap",family
assert family["allowedProfiles"][0]=="proven_route_terminal_traversal_v1",family

incompatible_guidance=[{**guidance[0],"failureClass":"chain_terminal_gap"}]
incompatible=plan("repair",guidance_rows=incompatible_guidance)
assert incompatible["llmAdvisorApplied"] is False,incompatible
assert incompatible["llmAdvisorFailureCompatibility"]=="",incompatible

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

# Production Repair consumes the same sanitized advisor only as hypothesis
# ordering. Current-byte playback/identity gates remain the sole acceptance
# authority.
production=plan("repair")
assert production["llmAdvisorApplied"] is True,production
assert production["llmAdvisorRescue"] is False,production
assert production["llmAdvisorProfile"]=="proven_route_terminal_traversal_v1",production
assert production["allowedProfiles"][0]=="proven_route_terminal_traversal_v1",production

# If ordinary production variants are exhausted, a different advisor profile
# that has not itself failed gets one bounded rescue. Exact profile debt still
# blocks repetition on the next cycle.
exhausted_memory=[
    {
        "providerId":"synthetic-llm-advisor",
        "failureClass":"route_proven_gap",
        "experimentVariant":variant,
        # v4 is generation-aware; true exhaustion requires the configured
        # final generation, not only generation 1.
        "experimentGeneration":2 if variant==4 else 1,
        "profile":"proven_route_terminal_traversal_v1" if variant==4 else "adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"executed_candidate_failed_validation",
    }
    for variant in range(5)
]
rescue_guidance=[{
    **guidance[0],
    "strategy":"discover-api-from-current-page-and-bundles",
    "profile":"search_contract_inference_v1",
}]
rescued=plan("repair",exhausted_memory,rescue_guidance)
assert rescued["baseExperimentExhausted"] is True,rescued
assert rescued["experimentExhausted"] is False,rescued
assert rescued["llmAdvisorApplied"] is True,rescued
assert rescued["llmAdvisorRescue"] is True,rescued
assert rescued["allowedProfiles"][0]=="search_contract_inference_v1",rescued
assert rescued["action"]=="probe-targeted-repair",rescued

rescue_failed=plan("repair",[
    *exhausted_memory,
    {
        "providerId":"synthetic-llm-advisor",
        "failureClass":"route_proven_gap",
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":"search_contract_inference_v1",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"executed_candidate_failed_validation",
    },
],rescue_guidance)
assert rescue_failed["llmAdvisorApplied"] is False,rescue_failed
assert rescue_failed["experimentExhausted"] is True,rescue_failed

brain=(ROOT/"scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
overlay=(ROOT/"scripts/adaptive_runtime/brain_repair_runtime.py").read_text(encoding="utf-8")
assert '"llmGuidance": planner_llm_guidance()' in brain
assert overlay.count('"llmGuidance": _BASE.planner_llm_guidance()')==2,overlay
assert overlay.count('"historicalSolutions": _BASE.planner_historical_solutions()')==2,overlay
assert "rawMutationContentRetained" in brain

print("Brain LLM advisor execution contract passed")
