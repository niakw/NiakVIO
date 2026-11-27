#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"
QUEUE=ROOT/"scripts/run_brain_learning_queue.py"
spec=importlib.util.spec_from_file_location("learning_queue_resolver_handoff",QUEUE)
assert spec and spec.loader
queue=importlib.util.module_from_spec(spec); spec.loader.exec_module(queue)

env=queue.learning_preferred_env("catalogue_inline_token_resolver_v2","chain_terminal_gap")
assert env=={
 "NUVIO_BRAIN_LEARNING_PREFERRED_PROFILE":"catalogue_inline_token_resolver_v2",
 "NUVIO_BRAIN_LEARNING_PREFERRED_FAILURE_CLASS":"chain_terminal_gap",
}
for args in [
 ("catalogue_inline_token_resolver_v2",""),
 ("","chain_terminal_gap"),
 ("bad-profile","chain_terminal_gap"),
]:
 try: queue.learning_preferred_env(*args)
 except ValueError: pass
 else: raise AssertionError("invalid Learning preferred handoff accepted")

policy={"production":{
 "negativeExperimentMemory":{"rotateExperimentAfterFailures":1,"maxVariantsPerSignature":5,"finalVariantGeneration":2,"maxLearningGenerationsPerSignature":5},
 "maxHypotheses":3,"maxMutationsPerProvider":2,"maxRepeatedSignature":2,
 "maxGeneratedBytesPerProvider":180000,"maxElapsedMsPerProvider":45000,
},"skillMaturity":{}}
candidate={"canonical_id":"resolver-representative","censusPrior":{"status":"CHAIN REACHED","dominantIssue":"provider_network_zero_result","evidenceDepth":["anime=chain_reached"]},"metadata":{"supportedTypes":["anime"]}}
result={"status":"no_streams","evidence":{"streams_playable":0,"streams_returned":0},"tests":[{"fixture":{"mediaType":"anime","category":"anime","title":"Synthetic"},"failure_class":"content_lookup_completed_no_streams","status":"no_streams","network_observations":[],"streams_playable":0,"stream_count":0}]}
def plan(mode="learning",profile="",failure="",negative_memory=None,causal_failure=""):
 payload={"mode":mode,"explorationChain":True,"forcePreferredStrategy":"","learningPreferredStrategy":profile,"learningPreferredFailureClass":failure,"learningCausalFailureClass":causal_failure,"policy":policy,"learnedSkills":{},"negativeMemory":list(negative_memory or []),"items":[{"key":"published:resolver-representative","candidate":candidate,"result":result,"state":{}}]}
 cp=subprocess.run(["node",str(PLANNER)],cwd=ROOT,input=json.dumps(payload),capture_output=True,text=True,check=True,timeout=20)
 return next(iter(json.loads(cp.stdout)["plans"].values()))
selected=plan(profile="catalogue_inline_token_resolver_v2",failure="chain_terminal_gap")
assert selected["learningPreferredRequested"]=="catalogue_inline_token_resolver_v2",selected
assert selected["learningPreferredFailureClass"]=="chain_terminal_gap",selected
assert selected["learningPreferredSelected"] is True,selected
assert selected["postExhaustionStrategyProfile"]=="catalogue_inline_token_resolver_v2",selected
assert selected["allowedProfiles"]==["catalogue_inline_token_resolver_v2"],selected
assert selected["action"]=="probe-targeted-repair" and selected["repairScope"]=="learning",selected
assert selected["forcePreferredSelected"] is False,selected

# Cross-run contract: once the installed resolver really produced bytes and was
# rejected, the persisted negative memory must prevent it from being treated as
# a fresh installed capability on the next Learning run. The planner may return
# to a base experiment or rotate causally, but it must not select V2 again.
executed_negative=[{
 "providerId":"resolver-representative",
 "failureClass":"",
 "signature":"",
 "profile":"catalogue_inline_token_resolver_v2",
 "strategyImplementationFingerprint":selected["strategyImplementationFingerprint"],
 "experimentVariant":4,
 "experimentGeneration":5,
 "attempts":1,"successes":0,"failures":1,"consecutiveFailures":1,
 "lastOutcome":"rejected","executionObserved":True,
}]
after_negative=plan(
 profile="catalogue_inline_token_resolver_v2",
 failure="chain_terminal_gap",
 negative_memory=executed_negative,
)
assert after_negative["learningPreferredRequested"]=="catalogue_inline_token_resolver_v2",after_negative
assert after_negative["learningPreferredSelected"] is False,after_negative
assert after_negative["postExhaustionStrategyProfile"]!="catalogue_inline_token_resolver_v2",after_negative
assert "catalogue_inline_token_resolver_v2" not in after_negative["allowedProfiles"],after_negative

player_frontier=plan(causal_failure="media_extraction_gap")
assert player_frontier["failureClass"]=="media_extraction_gap",player_frontier
assert player_frontier["learningCausalFailureRequested"]=="media_extraction_gap",player_frontier
assert player_frontier["learningCausalFailureApplied"] is True,player_frontier
assert player_frontier["learningPreferredRequested"]=="",player_frontier
assert queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE not in player_frontier["postExhaustionCandidateProfiles"],player_frontier

# A sanitized exact-parent scripted player with request bootstrap should reuse
# the already-installed document request-contract Lego before Architecture
# FORCE invents another player extractor family.
request_contract=plan(
 profile=queue.PLAYER_REQUEST_CONTRACT_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
)
assert request_contract["learningPreferredRequested"]=="document_request_contract_mining_v2",request_contract
assert request_contract["learningPreferredFailureClass"]=="media_extraction_gap",request_contract
assert request_contract["learningPreferredSelected"] is True,request_contract
assert request_contract["postExhaustionStrategyProfile"]=="document_request_contract_mining_v2",request_contract
assert request_contract["allowedProfiles"]==["document_request_contract_mining_v2"],request_contract
assert request_contract["failureClass"]=="media_extraction_gap",request_contract

# Once this exact installed Lego was genuinely executed and rejected, the same
# preferred handoff must fail closed and rotate instead of looking fresh again.
request_contract_v1_negative=[{
 "providerId":"resolver-representative",
 "failureClass":"media_extraction_gap",
 "signature":"",
 "profile":"document_request_contract_mining_v1",
 "strategyImplementationFingerprint":"1"*64,
 "experimentVariant":4,
 "experimentGeneration":5,
 "attempts":1,"successes":0,"failures":1,"consecutiveFailures":1,
 "lastOutcome":"rejected","executionObserved":True,
}]
request_contract_with_legacy_negative=plan(
 profile=queue.PLAYER_REQUEST_CONTRACT_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=request_contract_v1_negative,
)
assert request_contract_with_legacy_negative["learningPreferredSelected"] is True,request_contract_with_legacy_negative
assert request_contract_with_legacy_negative["postExhaustionStrategyProfile"]=="document_request_contract_mining_v2",request_contract_with_legacy_negative

request_contract_negative=[{
 "providerId":"resolver-representative",
 "failureClass":"media_extraction_gap",
 "signature":"",
 "profile":"document_request_contract_mining_v2",
 "strategyImplementationFingerprint":request_contract["strategyImplementationFingerprint"],
 "experimentVariant":4,
 "experimentGeneration":5,
 "attempts":1,"successes":0,"failures":1,"consecutiveFailures":1,
 "lastOutcome":"rejected","executionObserved":True,
}]
# A rejected older implementation of the same Bloc does not poison materially
# changed scoped bytes. This is the exact migration exercised by resolver+V2
# composition: old V2 remains historical, current V2 gets one real replay.
stale_request_contract_negative=[{
 **request_contract_negative[0],
 "strategyImplementationFingerprint":"a"*64,
}]
request_contract_after_stale_impl=plan(
 profile=queue.PLAYER_REQUEST_CONTRACT_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=stale_request_contract_negative,
)
assert request_contract_after_stale_impl["learningPreferredSelected"] is True,request_contract_after_stale_impl
assert request_contract_after_stale_impl["postExhaustionStrategyProfile"]==queue.PLAYER_REQUEST_CONTRACT_PROFILE,request_contract_after_stale_impl
assert request_contract_after_stale_impl["strategyImplementationFingerprint"]==request_contract["strategyImplementationFingerprint"],request_contract_after_stale_impl

# Executed bytes that did not causally exercise the Bloc are not a failure,
# but the exact implementation fingerprint must not loop forever. A materially
# new fingerprint remains eligible.
request_contract_inconclusive=[{
 **request_contract_negative[0],
 "attempts":1,"successes":0,"failures":0,"consecutiveFailures":0,
 "lastOutcome":"executed_inconclusive","executionObserved":True,
 "causalExerciseObserved":False,
}]
request_contract_after_inconclusive=plan(
 profile=queue.PLAYER_REQUEST_CONTRACT_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=request_contract_inconclusive,
)
assert request_contract_after_inconclusive["learningPreferredSelected"] is False,request_contract_after_inconclusive
assert request_contract_after_inconclusive["postExhaustionStrategyProfile"]!=queue.PLAYER_REQUEST_CONTRACT_PROFILE,request_contract_after_inconclusive
assert queue.PLAYER_REQUEST_CONTRACT_PROFILE not in request_contract_after_inconclusive["allowedProfiles"],request_contract_after_inconclusive

stale_request_contract_inconclusive=[{
 **request_contract_inconclusive[0],
 "strategyImplementationFingerprint":"c"*64,
}]
request_contract_after_stale_inconclusive=plan(
 profile=queue.PLAYER_REQUEST_CONTRACT_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=stale_request_contract_inconclusive,
)
assert request_contract_after_stale_inconclusive["learningPreferredSelected"] is True,request_contract_after_stale_inconclusive
assert request_contract_after_stale_inconclusive["postExhaustionStrategyProfile"]==queue.PLAYER_REQUEST_CONTRACT_PROFILE,request_contract_after_stale_inconclusive

request_contract_after_negative=plan(
 profile=queue.PLAYER_REQUEST_CONTRACT_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=request_contract_negative,
)
assert request_contract_after_negative["learningPreferredRequested"]=="document_request_contract_mining_v2",request_contract_after_negative
assert request_contract_after_negative["learningPreferredSelected"] is False,request_contract_after_negative
assert request_contract_after_negative["postExhaustionStrategyProfile"]!="document_request_contract_mining_v2",request_contract_after_negative
assert "document_request_contract_mining_v2" not in request_contract_after_negative["allowedProfiles"],request_contract_after_negative

# Sanitized network telemetry may promote the existing session-bootstrap Lego
# as the next one-shot hypothesis inside the same media-extraction family.
session_followup=plan(
 profile=queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=request_contract_negative,
)
assert session_followup["learningPreferredRequested"]==queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,session_followup
assert session_followup["learningPreferredSelected"] is True,session_followup
assert session_followup["postExhaustionStrategyProfile"]==queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,session_followup
assert session_followup["allowedProfiles"]==[queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE],session_followup

session_negative=[{
 "providerId":"resolver-representative",
 "failureClass":"media_extraction_gap",
 "signature":"",
 "profile":queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,
 "strategyImplementationFingerprint":session_followup["strategyImplementationFingerprint"],
 "experimentVariant":4,
 "experimentGeneration":5,
 "attempts":1,"successes":0,"failures":1,"consecutiveFailures":1,
 "lastOutcome":"rejected","executionObserved":True,
}]
session_after_negative=plan(
 profile=queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,
 failure=queue.PLAYER_REQUEST_CONTRACT_FAILURE,
 causal_failure="media_extraction_gap",
 negative_memory=[*request_contract_negative,*session_negative],
)
assert session_after_negative["learningPreferredSelected"] is False,session_after_negative
assert session_after_negative["postExhaustionStrategyProfile"]!=queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,session_after_negative
assert queue.SESSION_BOOTSTRAP_FOLLOWUP_PROFILE not in session_after_negative["allowedProfiles"],session_after_negative

wrong=plan(profile="catalogue_inline_token_resolver_v2",failure="search_gap")
assert wrong["learningPreferredSelected"] is False,wrong
assert "catalogue_inline_token_resolver_v2" not in wrong["allowedProfiles"],wrong
prod=plan(mode="repair",profile="catalogue_inline_token_resolver_v2",failure="chain_terminal_gap")
assert prod["learningPreferredSelected"] is False,prod
assert prod["learningPreferredRequested"]=="",prod
prod_causal=plan(mode="repair",causal_failure="media_extraction_gap")
assert prod_causal["learningCausalFailureRequested"]=="",prod_causal
assert prod_causal["learningCausalFailureApplied"] is False,prod_causal
assert "catalogue_inline_token_resolver_v2" not in prod["allowedProfiles"],prod
print("Learning installed resolver replay contract passed")
