#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"

planner_source=PLANNER.read_text(encoding="utf-8")
families_index=planner_source.index("const LLM_FAILURE_FAMILIES = Object.freeze({")
execution_index=planner_source.index("for (const rawItem of asArray(input.items))")
assert families_index < execution_index, (
    "LLM failure-family table must be initialized before top-level planner execution "
    "or every real item falls into planner_item_error via JavaScript TDZ"
)


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
    "experiment":{"routePolicy":"owned_plus_peer_generic","recipePolicy":"current_plus_provider_peer","roleOrder":["search","detail","player","source","api"],"terminalOnly":False,"aliasSearch":True,"responseSalvage":False,"documentRequestMining":False,"sessionBootstrap":True,"maxDepth":5,"maxPages":24,"maxEmbeds":22,"maxRecipePasses":4},
    "experimentFingerprint":"a"*64,
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
assert learning["llmAdvisorExperimentFingerprint"]=="a"*64,learning
assert learning["llmAdvisorExperiment"]["maxDepth"]==5,learning
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

# Legacy profile-wide debt cannot suppress a new v2 experiment fingerprint.
legacy_debt=[{
    "providerId":"synthetic-llm-advisor",
    "failureClass":"route_proven_gap",
    "experimentVariant":4,
    "experimentGeneration":1,
    "profile":"proven_route_terminal_traversal_v1",
    "failures":1,
    "consecutiveFailures":1,
    "successes":0,
}]
legacy_fresh=plan("learning",legacy_debt)
assert legacy_fresh["llmAdvisorApplied"] is True,legacy_fresh
assert legacy_fresh["llmAdvisorExperimentFingerprint"]=="a"*64,legacy_fresh

# Only the exact executed experiment fingerprint blocks replay.
exact_debt=[{**legacy_debt[0],"llmAdvisorExperimentFingerprint":"a"*64}]
blocked=plan("learning",exact_debt)
assert blocked["llmAdvisorApplied"] is False,blocked
assert blocked["llmAdvisorProfile"]=="",blocked

# A different experiment in the same profile remains eligible.
different=[{**guidance[0],"experimentFingerprint":"b"*64,"experiment":{**guidance[0]["experiment"],"maxDepth":6}}]
fresh=plan("learning",exact_debt,different)
assert fresh["llmAdvisorApplied"] is True,fresh
assert fresh["llmAdvisorExperimentFingerprint"]=="b"*64,fresh

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
        "llmAdvisorExperimentFingerprint":"a"*64,
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
assert "llmAdvisorExperimentFingerprint" in brain
assert "llmAdvisorExperiment" in brain

print("Brain LLM advisor execution contract passed")

# Meta-gap synthesis is the final bounded escape hatch in Learning after the
# ordinary experiment generations are exhausted and no coded post-exhaustion
# profile exists. It remains a prior: current-byte validation still decides.
meta_candidate={
    "canonical_id":"synthetic-meta-gap",
    "metadata":{"supportedTypes":["movie"]},
}
meta_result={
    "status":"runtime_error",
    "evidence":{"streams_playable":0,"streams_returned":0},
    "tests":[{
        "fixture":{"mediaType":"movie","category":"movie","title":"Synthetic"},
        "failure_class":"synthetic_novel_gap",
        "status":"runtime_error",
        "runtime_errors":["synthetic"],
        "network_observations":[],
        "streams_playable":0,
        "stream_count":0,
    }],
}
def meta_plan(memory):
    payload={
        "mode":"learning",
        "policy":policy,
        "learnedSkills":{},
        "historicalSolutions":[],
        "llmGuidance":[],
        "negativeMemory":memory,
        "items":[{
            "key":"published:synthetic-meta-gap",
            "candidate":meta_candidate,
            "result":meta_result,
            "state":{},
        }],
    }
    completed=subprocess.run(
        ["node",str(PLANNER)],
        cwd=ROOT,input=json.dumps(payload),capture_output=True,text=True,check=True,timeout=20,
    )
    return next(iter((json.loads(completed.stdout).get("plans") or {}).values()))

initial_meta=meta_plan([])
meta_signature=initial_meta["signature"]
meta_failure=initial_meta["failureClass"]
meta_guidance=[{
    "providerId":"synthetic-meta-gap",
    "failureClass":meta_failure,
    "targetLayer":"provider",
    "strategy":"meta-gap-runtime-composition",
    "profile":"search_contract_inference_v1",
    "confidence":0.86,
    "priorOnly":True,
    "experiment":{
        "routePolicy":"owned_plus_peer_generic",
        "recipePolicy":"current_plus_provider_peer",
        "roleOrder":["api","search","detail","player","source"],
        "terminalOnly":False,
        "aliasSearch":True,
        "responseSalvage":True,
        "documentRequestMining":True,
        "sessionBootstrap":False,
        "maxDepth":5,
        "maxPages":28,
        "maxEmbeds":20,
        "maxRecipePasses":5,
    },
    "experimentFingerprint":"c"*64,
    "guidanceKind":"meta-gap-synthesis",
}]
meta_memory=[
    {
        "providerId":"synthetic-meta-gap",
        "failureClass":meta_failure,
        "signature":meta_signature,
        "experimentVariant":variant,
        "experimentGeneration":1,
        "profile":"adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_exhaustion",
    }
    for variant in range(4)
]
meta_memory.extend([
    {
        "providerId":"synthetic-meta-gap",
        "failureClass":meta_failure,
        "signature":meta_signature,
        "experimentVariant":4,
        "experimentGeneration":generation,
        "profile":"adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_generation_exhaustion",
    }
    for generation in range(2,6)
])
meta_payload={
    "mode":"learning",
    "policy":policy,
    "learnedSkills":{},
    "historicalSolutions":[],
    "llmGuidance":meta_guidance,
    "negativeMemory":meta_memory,
    "items":[{
        "key":"published:synthetic-meta-gap",
        "candidate":meta_candidate,
        "result":meta_result,
        "state":{},
    }],
}
meta_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(meta_payload),capture_output=True,text=True,check=True,timeout=20,
)
meta_final=next(iter((json.loads(meta_completed.stdout).get("plans") or {}).values()))
assert meta_final["baseExperimentExhausted"] is True,meta_final
assert meta_final["metaGapEscalated"] is True,meta_final
assert meta_final["repairType"]=="synthesized_strategy",meta_final
assert meta_final["learningDisposition"]=="execute_meta_gap_synthesized_strategy",meta_final
assert meta_final["action"]=="probe-targeted-repair",meta_final
assert meta_final["llmAdvisorApplied"] is True,meta_final
assert meta_final["llmAdvisorGuidanceKind"]=="meta-gap-synthesis",meta_final
assert meta_final["allowedProfiles"][0]=="search_contract_inference_v1",meta_final

# Meta-gap guidance is also available to Brain Repair exploration, but it must
# never preempt ordinary variants. It becomes eligible only after exhaustion.
meta_prod_guidance=[{
    **guidance[0],
    "strategy":"meta-gap-route-transition-composition",
    "profile":"search_contract_inference_v1",
    "confidence":0.99,
    "guidanceKind":"meta-gap-synthesis",
    "experimentFingerprint":"d"*64,
}]
meta_prod_early=plan("repair",[],meta_prod_guidance)
assert meta_prod_early["llmAdvisorApplied"] is False,meta_prod_early
meta_prod_rescue=plan("repair",exhausted_memory,meta_prod_guidance)
assert meta_prod_rescue["baseExperimentExhausted"] is True,meta_prod_rescue
assert meta_prod_rescue["llmAdvisorApplied"] is True,meta_prod_rescue
assert meta_prod_rescue["llmAdvisorRescue"] is True,meta_prod_rescue
assert meta_prod_rescue["llmAdvisorGuidanceKind"]=="meta-gap-synthesis",meta_prod_rescue
assert meta_prod_rescue["allowedProfiles"][0]=="search_contract_inference_v1",meta_prod_rescue
