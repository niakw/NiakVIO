#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import os
import tempfile
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

def plan(mode:str,memory:list[dict]|None=None,guidance_rows:list[dict]|None=None,exploration_chain:bool=False):
    payload={
        "mode":mode,
        "explorationChain":exploration_chain,
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

# Fast Repair exploration must execute a sanitized Learning advisor after the
# ordinary g2 variants and every coded post-exhaustion strategy are exhausted.
# It remains sandbox-only: base exhaustion stays visible, while the learned
# hypothesis itself is non-exhausted until current-byte validation actually runs.
exploration_memory=list(exhausted_memory)
exploration_plan=None
for _attempt in range(12):
    exploration_plan=plan("repair",exploration_memory,rescue_guidance,True)
    assert exploration_plan["baseExperimentExhausted"] is True,exploration_plan
    if not exploration_plan.get("strategyEscalated"):
        break
    profile=exploration_plan["postExhaustionStrategyProfile"]
    implementation_fp=exploration_plan["strategyImplementationFingerprint"]
    assert profile and implementation_fp,exploration_plan
    exploration_memory.append({
        "providerId":"synthetic-llm-advisor",
        "failureClass":"route_proven_gap",
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":profile,
        "strategyImplementationFingerprint":implementation_fp,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_post_exhaustion_strategy_failed",
    })
else:
    raise AssertionError(("post-exhaustion strategies did not converge",exploration_plan))

assert exploration_plan is not None
assert exploration_plan["strategyEscalated"] is False,exploration_plan
assert exploration_plan["baseExperimentExhausted"] is True,exploration_plan
assert exploration_plan["experimentExhausted"] is False,exploration_plan
assert exploration_plan["llmAdvisorApplied"] is True,exploration_plan
assert exploration_plan["llmAdvisorRescue"] is False,exploration_plan
assert exploration_plan["llmAdvisorExplorationRescue"] is True,exploration_plan
assert exploration_plan["llmAdvisorProfile"]=="search_contract_inference_v1",exploration_plan
assert exploration_plan["allowedProfiles"][0]=="search_contract_inference_v1",exploration_plan
assert exploration_plan["action"]=="probe-targeted-repair",exploration_plan
assert exploration_plan["exitReason"] is None,exploration_plan
assert exploration_plan["repairType"]=="synthesized_strategy",exploration_plan
assert exploration_plan["learningDisposition"]=="execute_learning_advisor_strategy",exploration_plan

exploration_failed=plan("repair",[
    *exploration_memory,
    {
        "providerId":"synthetic-llm-advisor",
        "failureClass":"route_proven_gap",
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":"search_contract_inference_v1",
        "llmAdvisorExperimentFingerprint":"a"*64,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"executed_candidate_failed_validation",
    },
],rescue_guidance,True)
assert exploration_failed["llmAdvisorExplorationRescue"] is False,exploration_failed
assert exploration_failed["llmAdvisorApplied"] is False,exploration_failed
assert exploration_failed["experimentExhausted"] is True,exploration_failed

brain=(ROOT/"scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
overlay=(ROOT/"scripts/adaptive_runtime/brain_repair_runtime.py").read_text(encoding="utf-8")
assert '"llmGuidance": planner_llm_guidance()' in brain
assert overlay.count('"llmGuidance": _BASE.planner_llm_guidance()')==2,overlay
assert overlay.count('"historicalSolutions": _BASE.planner_historical_solutions()')==2,overlay
assert "rawMutationContentRetained" in brain
assert "llmAdvisorExperimentFingerprint" in brain
assert "llmAdvisorExperiment" in brain

# Persistent Learning guidance is intentionally cross-run. When only neutral
# control/evidence files changed, Repair must re-scope it to the current SHA and
# treat it as meta-gap synthesis; provider-byte drift still suppresses that
# provider completely.
import importlib.util
runtime_spec=importlib.util.spec_from_file_location(
    "brain_runtime_persistent_guidance",
    ROOT/"scripts/brain_repair_runtime.py",
)
assert runtime_spec and runtime_spec.loader
runtime_mod=importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime_mod)
persistent_payload={
    "schemaVersion":2,
    "sourceSha":"1"*40,
    "brainLlmSha":"2"*40,
    "publicationAuthority":False,
    "directMutationAuthority":False,
    "proofAuthority":False,
    "rawMutationContentRetained":False,
    "minConfidence":0.8,
    "providerCount":1,
    "rows":guidance,
}
old_sha=os.environ.get("GITHUB_SHA")
old_chain=os.environ.get("NUVIO_BRAIN_EXPLORATION_CHAIN")
old_mode=os.environ.get("NUVIO_BRAIN_PLANNER_MODE")
try:
    os.environ["GITHUB_SHA"]="3"*40
    os.environ.pop("NUVIO_BRAIN_EXPLORATION_CHAIN",None)
    os.environ.pop("NUVIO_BRAIN_PLANNER_MODE",None)
    with tempfile.TemporaryDirectory(prefix="persistent-guidance-") as tmp:
        guidance_path=Path(tmp)/"guidance.json"
        guidance_path.write_text(json.dumps(persistent_payload),encoding="utf-8")
        runtime_mod.LLM_GUIDANCE_PATH=guidance_path
        runtime_mod._guidance_source_drift=lambda _root,_source,_current:(["MEMORY.md"],set())
        safe_rows=runtime_mod.planner_llm_guidance()
        safe=[row for row in safe_rows if row.get("providerId")=="synthetic-llm-advisor"]
        assert len(safe)==1,safe_rows
        assert safe[0]["guidanceKind"]=="persistent-learning",safe[0]
        runtime_mod._guidance_source_drift=lambda _root,_source,_current:([],{"synthetic-llm-advisor"})
        drifted_rows=runtime_mod.planner_llm_guidance()
        assert not any(row.get("providerId")=="synthetic-llm-advisor" for row in drifted_rows),drifted_rows
finally:
    if old_sha is None: os.environ.pop("GITHUB_SHA",None)
    else: os.environ["GITHUB_SHA"]=old_sha
    if old_chain is None: os.environ.pop("NUVIO_BRAIN_EXPLORATION_CHAIN",None)
    else: os.environ["NUVIO_BRAIN_EXPLORATION_CHAIN"]=old_chain
    if old_mode is None: os.environ.pop("NUVIO_BRAIN_PLANNER_MODE",None)
    else: os.environ["NUVIO_BRAIN_PLANNER_MODE"]=old_mode

# Persistent guidance intentionally stores a compact standard schema without
# guidanceKind. Deterministic Learning gap-fill strategies retain their
# semantics through their allowlisted meta-gap-* strategy name.
serialized_meta_payload={
    **persistent_payload,
    "sourceSha":"3"*40,
    "rows":[{
        **guidance[0],
        "strategy":"meta-gap-search-contract-fallback",
        "profile":"search_contract_inference_v1",
        "experimentFingerprint":"f"*64,
    }],
}
serialized_meta_rows=runtime_mod._validated_guidance_rows(
    serialized_meta_payload,
    current_sha="3"*40,
    require_exact_sha=True,
    guidance_kind="external-brain-llm",
)
assert len(serialized_meta_rows)==1,serialized_meta_rows
assert serialized_meta_rows[0]["guidanceKind"]=="meta-gap-synthesis",serialized_meta_rows
assert serialized_meta_rows[0]["profile"]=="search_contract_inference_v1",serialized_meta_rows

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
assert meta_final["llmAdvisorProfile"]=="search_contract_inference_v1",meta_final
assert meta_final["llmAdvisorFailureCompatibility"]=="exact",meta_final
assert meta_final["llmAdvisorSourceFailureClass"]=="unknown_failure",meta_final


# Brain Repair exploration uses mode=repair plus explorationChain=true. It must
# receive the same post-exhaustion meta-gap escape hatch without turning the
# whole planner into Learning mode.
repair_explore_payload={**meta_payload,"mode":"repair","explorationChain":True}
repair_explore_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(repair_explore_payload),capture_output=True,text=True,check=True,timeout=20,
)
repair_explore=next(iter((json.loads(repair_explore_completed.stdout).get("plans") or {}).values()))
assert repair_explore["baseExperimentExhausted"] is True,repair_explore
assert repair_explore["metaGapEscalated"] is True,repair_explore
assert repair_explore["repairType"]=="synthesized_strategy",repair_explore
assert repair_explore["action"]=="probe-targeted-repair",repair_explore
assert repair_explore["llmAdvisorGuidanceKind"]=="meta-gap-synthesis",repair_explore
assert repair_explore["allowedProfiles"][0]=="search_contract_inference_v1",repair_explore
assert repair_explore["llmAdvisorProfile"]=="search_contract_inference_v1",repair_explore
assert repair_explore["llmAdvisorFailureCompatibility"]=="exact",repair_explore

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
assert meta_prod_rescue["llmAdvisorProfile"]=="search_contract_inference_v1",meta_prod_rescue
assert meta_prod_rescue["llmAdvisorFailureCompatibility"]=="exact",meta_prod_rescue


# A real debt pattern seen on 4khdhub changes class during Repair from
# route/search to playback_context_gap. Stale meta-gap guidance must be rebound
# to the CURRENT class instead of being discarded.
playback_candidate={
    "canonical_id":"synthetic-playback-rebind",
    "metadata":{"supportedTypes":["movie"]},
}
playback_result={
    "status":"blocked",
    "evidence":{"streams_returned":2,"streams_playable":0},
    "tests":[{
        "fixture":{"category":"movie"},
        "stream_count":2,
        "streams_playable":0,
        "failure_class":"stream_http_forbidden",
        "network_observations":[{"status":200},{"status":403}],
    }],
}
def playback_plan(memory,guidance_rows):
    payload={
        "mode":"repair",
        "explorationChain":True,
        "policy":policy,
        "learnedSkills":{},
        "historicalSolutions":[],
        "llmGuidance":guidance_rows,
        "negativeMemory":memory,
        "items":[{
            "key":"published:synthetic-playback-rebind",
            "candidate":playback_candidate,
            "result":playback_result,
            "state":{},
        }],
    }
    completed=subprocess.run(
        ["node",str(PLANNER)],
        cwd=ROOT,input=json.dumps(payload),capture_output=True,text=True,check=True,timeout=20,
    )
    return next(iter((json.loads(completed.stdout).get("plans") or {}).values()))

playback_initial=playback_plan([],[])
assert playback_initial["failureClass"]=="playback_context_gap",playback_initial
playback_signature=playback_initial["signature"]
playback_memory=[
    {
        "providerId":"synthetic-playback-rebind",
        "failureClass":"playback_context_gap",
        "signature":playback_signature,
        "experimentVariant":variant,
        "experimentGeneration":2 if variant==4 else 1,
        "profile":"adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_exhaustion",
    }
    for variant in range(5)
]
stale_route_guidance=[{
    "providerId":"synthetic-playback-rebind",
    "failureClass":"route_proven_gap",
    "targetLayer":"provider",
    "strategy":"meta-gap-route-transition-composition",
    "profile":"proven_route_terminal_traversal_v1",
    "confidence":0.86,
    "priorOnly":True,
    "experiment":{
        "routePolicy":"owned_plus_peer_generic",
        "recipePolicy":"current_plus_provider_peer",
        "roleOrder":["search","detail","api","episode","player","source","other"],
        "terminalOnly":False,
        "aliasSearch":True,
        "responseSalvage":True,
        "documentRequestMining":True,
        "sessionBootstrap":False,
        "maxDepth":5,
        "maxPages":30,
        "maxEmbeds":24,
        "maxRecipePasses":5,
    },
    "experimentFingerprint":"e"*64,
    "guidanceKind":"meta-gap-synthesis",
}]
playback_rebound=None
# Same-family deterministic evolved strategies have higher priority than stale
# cross-family meta-gap guidance. Exhaust their exact implementation
# fingerprints first; only then should the planner rebind the advisor.
for _attempt in range(20):
    playback_rebound=playback_plan(playback_memory,stale_route_guidance)
    assert playback_rebound["baseExperimentExhausted"] is True,playback_rebound
    if not playback_rebound.get("strategyEscalated"):
        break
    profile=playback_rebound.get("postExhaustionStrategyProfile") or ""
    implementation_fp=playback_rebound.get("strategyImplementationFingerprint") or ""
    source_failure=playback_rebound.get("postExhaustionSourceFailureClass") or "playback_context_gap"
    assert profile and implementation_fp,playback_rebound
    playback_memory.append({
        "providerId":"synthetic-playback-rebind",
        "failureClass":source_failure,
        "signature":playback_signature,
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":profile,
        "strategyImplementationFingerprint":implementation_fp,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_same_family_evolved_strategy_failed",
    })
else:
    raise AssertionError(("playback same-family strategies did not converge",playback_rebound))
assert playback_rebound is not None
assert playback_rebound["metaGapEscalated"] is True,playback_rebound
assert playback_rebound["repairType"]=="synthesized_strategy",playback_rebound
assert playback_rebound["llmAdvisorFailureCompatibility"]=="exact-rebound",playback_rebound
assert playback_rebound["llmAdvisorSourceFailureClass"]=="playback_context_gap",playback_rebound
assert playback_rebound["llmAdvisorProfile"]=="player_media_extractor_v1",playback_rebound
assert playback_rebound["allowedProfiles"][0]=="player_media_extractor_v1",playback_rebound
assert playback_rebound["llmAdvisorExperiment"]["terminalOnly"] is True,playback_rebound
assert playback_rebound["llmAdvisorExperiment"]["roleOrder"][0]=="player",playback_rebound
assert playback_rebound["action"]=="probe-targeted-repair",playback_rebound

# Exact-class meta-gap guidance keeps Learning's safe executor choice, while
# stale/mismatched guidance above still rebinds to the current failure class.
transport_candidate={
    "canonical_id":"synthetic-transport-executor-choice",
    "metadata":{"supportedTypes":["movie","tv"]},
}
transport_result={
    "status":"blocked",
    "evidence":{"streams_returned":0,"streams_playable":0},
    "tests":[{
        "fixture":{"category":"movie"},
        "failure_class":"provider_http_blocked",
        "status":"blocked",
        "stream_count":0,
        "streams_playable":0,
        "network_observations":[{"status":403,"infrastructure":False,"stage":"search"}],
    }],
}
transport_guidance=[{
    "providerId":"synthetic-transport-executor-choice",
    "failureClass":"transport_blocked",
    "targetLayer":"provider",
    "strategy":"meta-gap-search-contract-fallback",
    "profile":"search_contract_inference_v1",
    "confidence":0.86,
    "priorOnly":True,
    "experiment":{
        "routePolicy":"owned_plus_peer",
        "recipePolicy":"current_plus_provider",
        "roleOrder":["search","api","detail","player","source","episode","other"],
        "terminalOnly":False,
        "aliasSearch":True,
        "responseSalvage":True,
        "documentRequestMining":True,
        "sessionBootstrap":True,
        "maxDepth":5,
        "maxPages":24,
        "maxEmbeds":20,
        "maxRecipePasses":5,
    },
    "experimentFingerprint":"9"*64,
    "guidanceKind":"meta-gap-synthesis",
}]
transport_base_payload={
    "mode":"repair",
    "explorationChain":True,
    "policy":policy,
    "learnedSkills":{},
    "historicalSolutions":[],
    "llmGuidance":[],
    "negativeMemory":[],
    "items":[{
        "key":"published:synthetic-transport-executor-choice",
        "candidate":transport_candidate,
        "result":transport_result,
        "state":{},
    }],
}
transport_initial_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(transport_base_payload),capture_output=True,text=True,check=True,timeout=20,
)
transport_initial=next(iter((json.loads(transport_initial_completed.stdout).get("plans") or {}).values()))
assert transport_initial["failureClass"]=="transport_blocked",transport_initial
transport_signature=transport_initial["signature"]
transport_exhausted_memory=[
    {
        "providerId":"synthetic-transport-executor-choice",
        "failureClass":"transport_blocked",
        "signature":transport_signature,
        "experimentVariant":variant,
        "experimentGeneration":2 if variant==4 else 1,
        "profile":"provider_origin_failover_v1" if variant==4 else "adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_transport_variant_exhausted",
    }
    for variant in range(5)
]
transport_memory=list(transport_exhausted_memory)
transport_plan=None
saw_same_family_evolved_strategy=False
# Exploration Chain deliberately tries each coded post-exhaustion strategy
# before Learning meta-gap guidance. Exhaust those bounded implementations by
# their exact implementation fingerprint; never let a meta-gap prior bypass
# an untried deterministic strategy. The route-terminal causal family spans
# transport/route/search labels, so bounded sibling strategies are valid after
# the current label's local strategies are exhausted.
for _attempt in range(20):
    transport_payload={
        **transport_base_payload,
        "llmGuidance":transport_guidance,
        "negativeMemory":transport_memory,
    }
    transport_completed=subprocess.run(
        ["node",str(PLANNER)],
        cwd=ROOT,input=json.dumps(transport_payload),capture_output=True,text=True,check=True,timeout=20,
    )
    transport_plan=next(iter((json.loads(transport_completed.stdout).get("plans") or {}).values()))
    assert transport_plan["baseExperimentExhausted"] is True,transport_plan
    if not transport_plan.get("strategyEscalated"):
        break
    profile=transport_plan["postExhaustionStrategyProfile"]
    implementation_fp=transport_plan["strategyImplementationFingerprint"]
    source_failure=transport_plan.get("postExhaustionSourceFailureClass") or ""
    assert profile,transport_plan
    assert implementation_fp,transport_plan
    if source_failure and source_failure!="transport_blocked":
        saw_same_family_evolved_strategy=True
    transport_memory.append({
        "providerId":"synthetic-transport-executor-choice",
        "failureClass":"transport_blocked",
        "signature":transport_signature,
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":profile,
        "strategyImplementationFingerprint":implementation_fp,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_post_exhaustion_strategy_failed",
    })
else:
    raise AssertionError(("transport post-exhaustion strategies did not converge",transport_plan))

assert transport_plan is not None
assert saw_same_family_evolved_strategy is True,transport_memory
assert transport_plan["strategyEscalated"] is False,transport_plan
assert transport_plan["metaGapEscalated"] is True,transport_plan
assert transport_plan["llmAdvisorApplied"] is True,transport_plan
assert transport_plan["llmAdvisorProfile"]=="search_contract_inference_v1",transport_plan
assert transport_plan["llmAdvisorFailureCompatibility"]=="exact",transport_plan
assert transport_plan["allowedProfiles"][0]=="search_contract_inference_v1",transport_plan

# An evolved strategy failed under route_proven_gap must stay failed after the
# current observation drifts to transport_blocked. Strategy implementation
# identity is provider+causal-family scoped, not failure-label scoped.
route_transition_fp=None
for memory_row in transport_memory:
    if memory_row.get("profile")=="route_transition_graph_v1":
        route_transition_fp=memory_row.get("strategyImplementationFingerprint")
        memory_row["failureClass"]="route_proven_gap"
        break
assert route_transition_fp,transport_memory
cross_label_payload={
    **transport_base_payload,
    "llmGuidance":transport_guidance,
    "negativeMemory":transport_memory,
}
cross_label_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(cross_label_payload),capture_output=True,text=True,check=True,timeout=20,
)
cross_label_plan=next(iter((json.loads(cross_label_completed.stdout).get("plans") or {}).values()))
assert not (
    cross_label_plan.get("postExhaustionStrategyProfile")=="route_transition_graph_v1"
    and cross_label_plan.get("strategyImplementationFingerprint")==route_transition_fp
),cross_label_plan

# A Learning meta-gap executor selected from a sibling failure class in the
# same causal family must survive current-class drift. This is the Moviebox
# shape: persisted/census evidence can say route_proven_gap while the current
# sandbox classifies transport_blocked. Rebinding the executor back to origin
# failover would erase Learning's bounded strategy rotation.
transport_family_guidance=[{
    **transport_guidance[0],
    "failureClass":"route_proven_gap",
    "profile":"search_contract_inference_v1",
    "strategy":"meta-gap-search-contract-fallback",
    "confidence":0.86,
    "experimentFingerprint":"8"*64,
}]
transport_family_payload={
    **transport_base_payload,
    "llmGuidance":transport_family_guidance,
    "negativeMemory":transport_memory,
}
transport_family_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(transport_family_payload),capture_output=True,text=True,check=True,timeout=20,
)
transport_family_plan=next(iter((json.loads(transport_family_completed.stdout).get("plans") or {}).values()))
assert transport_family_plan["baseExperimentExhausted"] is True,transport_family_plan
assert transport_family_plan["strategyEscalated"] is False,transport_family_plan
assert transport_family_plan["metaGapEscalated"] is True,transport_family_plan
assert transport_family_plan["llmAdvisorApplied"] is True,transport_family_plan
assert transport_family_plan["llmAdvisorProfile"]=="search_contract_inference_v1",transport_family_plan
assert transport_family_plan["allowedProfiles"][0]=="search_contract_inference_v1",transport_family_plan
assert transport_family_plan["llmAdvisorFailureCompatibility"]=="exact-rebound",transport_family_plan
assert transport_family_plan["llmAdvisorSourceFailureClass"]=="transport_blocked",transport_family_plan

# Fresh LLM/persistent fingerprints must not reopen an advisor executor that
# already consumed the same bounded causal-family budget. This is the Moviebox
# loop: route_proven/search/transport labels drift, but three real
# search_contract advisor executions exhaust that executor for route-terminal.
transport_profile_exhausted_memory=list(transport_memory)
for index,(failure,fp) in enumerate((
    ("route_proven_gap","a"*64),
    ("search_gap","b"*64),
    ("transport_blocked","c"*64),
),start=1):
    transport_profile_exhausted_memory.append({
        "providerId":"synthetic-transport-executor-choice",
        "failureClass":failure,
        "signature":transport_signature,
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":"search_contract_inference_v1",
        "llmAdvisorExperimentFingerprint":fp,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "progresses":1 if index==2 else 0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_causal_family_advisor_budget",
    })
transport_profile_rotation_guidance=[
    {
        **transport_guidance[0],
        "failureClass":"route_proven_gap",
        "profile":"search_contract_inference_v1",
        "strategy":"meta-gap-search-contract-fallback",
        "confidence":0.99,
        "experimentFingerprint":"d"*64,
    },
    {
        **transport_guidance[0],
        "failureClass":"route_proven_gap",
        "profile":"adaptive_runtime_recovery",
        "strategy":"meta-gap-adaptive-runtime-fallback",
        "confidence":0.86,
        "experimentFingerprint":"e"*64,
    },
]
transport_profile_rotation_payload={
    **transport_base_payload,
    "llmGuidance":transport_profile_rotation_guidance,
    "negativeMemory":transport_profile_exhausted_memory,
}
transport_profile_rotation_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(transport_profile_rotation_payload),
    capture_output=True,text=True,check=True,timeout=20,
)
transport_profile_rotation=next(iter((json.loads(transport_profile_rotation_completed.stdout).get("plans") or {}).values()))
assert transport_profile_rotation["baseExperimentExhausted"] is True,transport_profile_rotation
assert transport_profile_rotation["strategyEscalated"] is False,transport_profile_rotation
assert transport_profile_rotation["metaGapEscalated"] is True,transport_profile_rotation
assert transport_profile_rotation["llmAdvisorApplied"] is True,transport_profile_rotation
assert transport_profile_rotation["llmAdvisorProfile"]=="adaptive_runtime_recovery",transport_profile_rotation
assert transport_profile_rotation["allowedProfiles"][0]=="adaptive_runtime_recovery",transport_profile_rotation
assert transport_profile_rotation["llmAdvisorProfile"]!="search_contract_inference_v1",transport_profile_rotation


# If the current plan is already a confirmed architecture_gap, Repair
# exploration must not wait for synthetic experiment exhaustion that cannot
# exist. Rebind the provider's stale meta-gap guidance immediately.
direct_arch_payload={
    "mode":"repair",
    "explorationChain":True,
    "policy":policy,
    "learnedSkills":{},
    "historicalSolutions":[],
    "llmGuidance":[{
        **meta_guidance[0],
        "providerId":"synthetic-direct-arch-gap",
        "failureClass":"chain_terminal_gap",
        "profile":"chain_terminal_extractor_v1",
        "experimentFingerprint":"f"*64,
    }],
    "negativeMemory":[],
    "items":[{
        "key":"published:synthetic-direct-arch-gap",
        "candidate":{
            "canonical_id":"synthetic-direct-arch-gap",
            "metadata":{"supportedTypes":["movie"]},
        },
        "result":meta_result,
        "state":{},
    }],
}
direct_arch_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(direct_arch_payload),capture_output=True,text=True,check=True,timeout=20,
)
direct_arch=next(iter((json.loads(direct_arch_completed.stdout).get("plans") or {}).values()))
assert direct_arch["failureClass"]=="unknown_failure",direct_arch
assert direct_arch["architectureGapEscalation"] is True,direct_arch
assert direct_arch["metaGapEscalated"] is True,direct_arch
assert direct_arch["repairType"]=="synthesized_strategy",direct_arch
assert direct_arch["llmAdvisorFailureCompatibility"]=="exact-rebound",direct_arch
assert direct_arch["llmAdvisorSourceFailureClass"]=="unknown_failure",direct_arch
assert direct_arch["llmAdvisorProfile"]=="adaptive_runtime_recovery",direct_arch
assert direct_arch["allowedProfiles"][0]=="adaptive_runtime_recovery",direct_arch
assert direct_arch["action"]=="probe-targeted-repair",direct_arch


direct_first_fp=direct_arch["llmAdvisorExperimentFingerprint"]
direct_retry_memory=[{
    "providerId":"synthetic-direct-arch-gap",
    "failureClass":"unknown_failure",
    "signature":direct_arch["signature"],
    "experimentVariant":0,
    "experimentGeneration":1,
    "profile":"adaptive_runtime_recovery",
    "failures":1,
    "consecutiveFailures":1,
    "successes":0,
    "executionObserved":True,
    "lastOutcome":"rejected",
    "lastReason":"synthetic_meta_gap_v1_failed",
    "llmAdvisorExperimentFingerprint":direct_first_fp,
}]
direct_retry_payload={**direct_arch_payload,"negativeMemory":direct_retry_memory}
direct_retry_completed=subprocess.run(
    ["node",str(PLANNER)],
    cwd=ROOT,input=json.dumps(direct_retry_payload),capture_output=True,text=True,check=True,timeout=20,
)
direct_retry=next(iter((json.loads(direct_retry_completed.stdout).get("plans") or {}).values()))
assert direct_retry["metaGapEscalated"] is True,direct_retry
assert direct_retry["llmAdvisorProfile"]=="adaptive_runtime_recovery",direct_retry
assert direct_retry["llmAdvisorExperimentFingerprint"] != direct_first_fp,direct_retry
assert direct_retry["llmAdvisorMetaGapGeneration"]==1,direct_retry
assert direct_retry["repairType"]=="synthesized_strategy",direct_retry

# Representative route/search exhaustion contract: after the exact HTML parser
# gets its one bounded current-implementation attempt, a legacy failure row must
# remain negative even without an old fingerprint and Brain must advance directly
# to the new route_transition_graph_v2 executor instead of replaying v1 debt.
route_v2_provider="synthetic-route-v2-priority"
route_v2_candidate={
    "canonical_id":route_v2_provider,
    "metadata":{"supportedTypes":["movie"]},
}
route_v2_result={
    "status":"no_streams",
    "evidence":{"streams_playable":0,"streams_returned":0},
    "tests":[{
        "fixture":{"mediaType":"movie","category":"movie","title":"Synthetic"},
        "failure_class":"content_lookup_completed_no_streams",
        "status":"no_streams",
        "network_observations":[{"status":200,"stage":"search","infrastructure":False}],
        "streams_playable":0,
        "stream_count":0,
    }],
}
route_v2_base_memory=[
    {
        "providerId":route_v2_provider,
        "failureClass":"search_gap",
        "experimentVariant":variant,
        "experimentGeneration":2 if variant==4 else 1,
        "profile":"search_contract_inference_v1" if variant==4 else "adaptive_runtime_recovery",
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_base_exhausted",
    }
    for variant in range(5)
]

def route_v2_plan(memory_rows):
    payload={
        "mode":"repair",
        "explorationChain":True,
        "policy":policy,
        "learnedSkills":{},
        "historicalSolutions":[],
        "llmGuidance":[],
        "negativeMemory":memory_rows,
        "items":[{
            "key":f"published:{route_v2_provider}",
            "candidate":route_v2_candidate,
            "result":route_v2_result,
            "state":{},
        }],
    }
    completed=subprocess.run(
        ["node",str(PLANNER)],
        cwd=ROOT,input=json.dumps(payload),capture_output=True,text=True,check=True,timeout=20,
    )
    return next(iter((json.loads(completed.stdout).get("plans") or {}).values()))

route_v2_first=route_v2_plan(route_v2_base_memory)
assert route_v2_first["failureClass"]=="search_gap",route_v2_first
assert route_v2_first["baseExperimentExhausted"] is True,route_v2_first
assert route_v2_first["postExhaustionStrategyProfile"]=="html_class_token_exact_v1",route_v2_first
assert route_v2_first["strategyEscalated"] is True,route_v2_first
html_fp=route_v2_first["strategyImplementationFingerprint"]
assert html_fp,route_v2_first

route_v2_second=route_v2_plan([
    *route_v2_base_memory,
    {
        "providerId":route_v2_provider,
        "failureClass":"search_gap",
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":"html_class_token_exact_v1",
        "strategyImplementationFingerprint":html_fp,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_html_current_impl_failed",
    },
    {
        "providerId":route_v2_provider,
        "failureClass":"search_gap",
        "experimentVariant":4,
        "experimentGeneration":2,
        "profile":"search_contract_inference_v1",
        # Legacy memory intentionally has no implementation fingerprint.
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"synthetic_legacy_search_contract_failed",
    },
])
assert route_v2_second["explorationChainEnabled"] is True,route_v2_second
assert route_v2_second["strategyEscalated"] is True,route_v2_second
assert route_v2_second["postExhaustionStrategyProfile"]=="route_transition_graph_v2",route_v2_second
assert route_v2_second["allowedProfiles"]==["route_transition_graph_v2"],route_v2_second
assert route_v2_second["postExhaustionStrategyMethod"]=="same-provider-observed-transition-salvage",route_v2_second
