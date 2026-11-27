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
def plan(mode="learning",profile="",failure=""):
 payload={"mode":mode,"explorationChain":True,"forcePreferredStrategy":"","learningPreferredStrategy":profile,"learningPreferredFailureClass":failure,"policy":policy,"learnedSkills":{},"negativeMemory":[],"items":[{"key":"published:resolver-representative","candidate":candidate,"result":result,"state":{}}]}
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
wrong=plan(profile="catalogue_inline_token_resolver_v2",failure="search_gap")
assert wrong["learningPreferredSelected"] is False,wrong
assert "catalogue_inline_token_resolver_v2" not in wrong["allowedProfiles"],wrong
prod=plan(mode="repair",profile="catalogue_inline_token_resolver_v2",failure="chain_terminal_gap")
assert prod["learningPreferredSelected"] is False,prod
assert prod["learningPreferredRequested"]=="",prod
assert "catalogue_inline_token_resolver_v2" not in prod["allowedProfiles"],prod
print("Learning installed resolver replay contract passed")
