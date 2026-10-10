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

def plan(memory, mode="repair", preferred_profile=""):
    payload={
        "mode":mode,
        "forcePreferredStrategy":preferred_profile,
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

# After the bounded g2..g5 family is exhausted, Learning must not stop at a
# label-only architecture gap. It enters a finite second-order strategy family
# with its own profile identity and method.
base_exhausted=[*old,row(4,2),row(4,3),row(4,4),row(4,5)]
learning_escalated=plan(base_exhausted,"learning")
assert learning_escalated["experimentGeneration"]==5,learning_escalated
assert learning_escalated["baseExperimentExhausted"] is True,learning_escalated
assert learning_escalated["experimentExhausted"] is False,learning_escalated
assert learning_escalated["strategyEscalated"] is True,learning_escalated
assert learning_escalated["postExhaustionStrategyProfile"]=="terminal_transition_graph_v1",learning_escalated
assert learning_escalated["postExhaustionStrategyMethod"]=="terminal-response-transition-graph",learning_escalated
assert learning_escalated["repairType"]=="evolved_strategy",learning_escalated
assert learning_escalated["action"]=="probe-targeted-repair",learning_escalated
assert learning_escalated["allowedProfiles"]==["terminal_transition_graph_v1"],learning_escalated
assert learning_escalated["learningDisposition"]=="execute_bounded_evolved_strategy",learning_escalated

# When a new Brain architecture is explicitly promoted, its exact strategy
# must be replayed first on the representative, not buried after many older
# strategies. It is still subject to both causal membership and executed
# negative memory; an unavailable profile cannot be forced.
preferred=plan(base_exhausted,"learning","terminal_request_program_inference_v1")
assert preferred["postExhaustionStrategyProfile"]=="terminal_request_program_inference_v1",preferred
unknown=plan(base_exhausted,"learning","invented_unsafe_provider_v9")
assert unknown["postExhaustionStrategyProfile"]=="terminal_transition_graph_v1",unknown

terminal_fp=learning_escalated["strategyImplementationFingerprint"]
assert len(terminal_fp)==64 and all(ch in "0123456789abcdef" for ch in terminal_fp),learning_escalated

# Legacy negative memory without an implementation fingerprint is fail-closed:
# the profile id already failed. Materially new behavior must use a new profile
# generation/id rather than silently resurrecting the same v1 implementation.
stale_first_escalation_failed={
    **row(4,5),
    "profile":"terminal_transition_graph_v1",
    # Only executed negative evidence can exhaust a strategy. Without this
    # field the planner correctly treats the row as an unexecuted proposal.
    "executionObserved":True,
}
stale_retry=plan([*base_exhausted,stale_first_escalation_failed],"learning")
# terminal_transition_graph_v2 is now a genuinely installed executable
# successor. It must be replayed with actual evidence BEFORE progressing to
# terminal_request_program_inference_v1.
assert stale_retry["postExhaustionStrategyProfile"]=="terminal_transition_graph_v2",stale_retry
assert stale_retry["allowedProfiles"]==["terminal_transition_graph_v2"],stale_retry
assert stale_retry["strategyImplementationFingerprint"]
assert stale_retry["postExhaustionStrategyProfile"]!="terminal_transition_graph_v1",stale_retry

unobserved_retry=plan([*base_exhausted,{**stale_first_escalation_failed,"executionObserved":False}],"learning")
assert unobserved_retry["postExhaustionStrategyProfile"]=="terminal_transition_graph_v1",unobserved_retry

first_escalation_failed={
    **stale_first_escalation_failed,
    "strategyImplementationFingerprint":terminal_fp,
}
# An evolving Brain may install terminal graph v3, v4, ... after v2.
# Do not hardcode the next fallback to terminal_request_program_inference_v1
# when an installed, untried sibling has a real executable fingerprint.
# Replay each installed graph and explicitly mark its execution-observed
# failure before advancing to the next causal strategy; this stays valid for
# future model-generated profiles without modifying the test for every vN.
installed_v2_failed={
    **row(4,5),
    "profile":"terminal_transition_graph_v2",
    "executionObserved":True,
    "strategyImplementationFingerprint":stale_retry["strategyImplementationFingerprint"],
}
terminal_graph_failures=[installed_v2_failed]
seen_graph_profiles={"terminal_transition_graph_v1","terminal_transition_graph_v2"}
for _graph_generation in range(2,20):
    next_graph=plan([*base_exhausted,first_escalation_failed,*terminal_graph_failures],"learning")
    next_profile=str(next_graph.get("postExhaustionStrategyProfile") or "")
    if not next_profile.startswith("terminal_transition_graph_v"):
        break
    graph_number=next_profile.removeprefix("terminal_transition_graph_v")
    assert graph_number.isdecimal() and int(graph_number)>2, next_graph
    assert next_profile not in seen_graph_profiles, "already-executed graph incorrectly reselected"
    fingerprint=str(next_graph.get("strategyImplementationFingerprint") or "")
    assert len(fingerprint)==64 and next_graph.get("strategyEscalated") is True,next_graph
    seen_graph_profiles.add(next_profile)
    terminal_graph_failures.append({
        **row(4,5),
        "failureClass":str(next_graph.get("postExhaustionSourceFailureClass") or "chain_terminal_gap"),
        "profile":next_profile,
        "executionObserved":True,
        "strategyImplementationFingerprint":fingerprint,
    })
else:
    raise AssertionError("Brain terminal graph profiles failed to reach next causal family")
learning_escalated_2=plan([*base_exhausted,first_escalation_failed,*terminal_graph_failures],"learning")
assert learning_escalated_2["experimentExhausted"] is False,learning_escalated_2
assert learning_escalated_2["postExhaustionStrategyProfile"]=="terminal_request_program_inference_v1",learning_escalated_2
assert learning_escalated_2["allowedProfiles"]==["terminal_request_program_inference_v1"],learning_escalated_2
request_fp=learning_escalated_2["strategyImplementationFingerprint"]
assert len(request_fp)==64 and request_fp!=terminal_fp,learning_escalated_2

second_escalation_failed={
    **row(4,5),
    "profile":"terminal_request_program_inference_v1",
    "executionObserved":True,
    "strategyImplementationFingerprint":request_fp,
}
already_failed_preference=plan(
    [*base_exhausted,first_escalation_failed,*terminal_graph_failures,second_escalation_failed],
    "learning","terminal_request_program_inference_v1",
)
assert already_failed_preference["postExhaustionStrategyProfile"]!="terminal_request_program_inference_v1",already_failed_preference
after_second=plan([*base_exhausted,first_escalation_failed,*terminal_graph_failures,second_escalation_failed],"learning")
assert after_second["experimentExhausted"] is False,after_second
assert after_second["postExhaustionStrategyProfile"]=="runtime_response_salvage_v1",after_second
assert after_second["allowedProfiles"]==["runtime_response_salvage_v1"],after_second
salvage_fp=after_second["strategyImplementationFingerprint"]
assert len(salvage_fp)==64 and salvage_fp not in {terminal_fp,request_fp},after_second

third_escalation_failed={
    **row(4,5),
    "profile":"runtime_response_salvage_v1",
    "executionObserved":True,
    "strategyImplementationFingerprint":salvage_fp,
}
after_third=plan(
    [*base_exhausted,first_escalation_failed,*terminal_graph_failures,second_escalation_failed,third_escalation_failed],
    "learning",
)
assert after_third["experimentExhausted"] is False,after_third
assert after_third["postExhaustionStrategyProfile"]=="document_request_contract_mining_v1",after_third
assert after_third["allowedProfiles"]==["document_request_contract_mining_v1"],after_third
document_fp=after_third["strategyImplementationFingerprint"]
assert len(document_fp)==64 and document_fp not in {terminal_fp,request_fp,salvage_fp},after_third

fourth_escalation_failed={
    **row(4,5),
    "profile":"document_request_contract_mining_v1",
    "executionObserved":True,
    "strategyImplementationFingerprint":document_fp,
}
# Causal-family evolution may legitimately discover additional terminal-media
# executors owned by sibling failure labels (for example media_extraction_gap).
# Exhaust every distinct implementation before declaring architecture debt.
evolved_memory=[
    *base_exhausted,
    first_escalation_failed,
    *terminal_graph_failures,
    second_escalation_failed,
    third_escalation_failed,
    fourth_escalation_failed,
]
seen_evolved_profiles={
    *seen_graph_profiles,
    "terminal_request_program_inference_v1",
    "runtime_response_salvage_v1",
    "document_request_contract_mining_v1",
}
learning_exhausted=None
for _attempt in range(24):
    learning_exhausted=plan(evolved_memory,"learning")
    assert learning_exhausted["experimentGeneration"]==5,learning_exhausted
    assert learning_exhausted["baseExperimentExhausted"] is True,learning_exhausted
    if not learning_exhausted.get("strategyEscalated"):
        break
    profile=learning_exhausted.get("postExhaustionStrategyProfile") or ""
    implementation_fp=learning_exhausted.get("strategyImplementationFingerprint") or ""
    source_failure=learning_exhausted.get("postExhaustionSourceFailureClass") or "chain_terminal_gap"
    assert profile and implementation_fp,learning_exhausted
    seen_evolved_profiles.add(profile)
    failed_row={
        **row(4,5),
        "failureClass":source_failure,
        "profile":profile,
        "executionObserved":True,
        "strategyImplementationFingerprint":implementation_fp,
    }
    evolved_memory.append(failed_row)
else:
    raise AssertionError(("causal-family evolved strategies did not exhaust",learning_exhausted))
assert learning_exhausted is not None
assert "player_protocol_family_replay_v1" in seen_evolved_profiles,seen_evolved_profiles
assert learning_exhausted["experimentExhausted"] is True,learning_exhausted
assert learning_exhausted["strategyEscalated"] is False,learning_exhausted
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
