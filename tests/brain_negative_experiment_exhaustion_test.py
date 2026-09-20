#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"

candidate={
    "canonical_id":"synthetic-exhaustion",
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
        },
        "maxHypotheses":3,
        "maxMutationsPerProvider":2,
        "maxRepeatedSignature":2,
        "maxGeneratedBytesPerProvider":180000,
        "maxElapsedMsPerProvider":45000,
    },
    "skillMaturity":{},
}

def run(memory):
    payload={
        "mode":"repair",
        "policy":policy,
        "learnedSkills":{},
        "negativeMemory":memory,
        "items":[{"key":"published:synthetic-exhaustion","candidate":candidate,"result":result,"state":{}}],
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
    plans=parsed.get("plans") or {}
    assert len(plans)==1,parsed
    return next(iter(plans.values()))

base=lambda variant:{
    "providerId":"synthetic-exhaustion",
    "failureClass":"chain_terminal_gap",
    "experimentVariant":variant,
    "failures":1,
    "consecutiveFailures":1,
    "successes":0,
}

three=run([base(0),base(1),base(2)])
assert three["failureClass"]=="chain_terminal_gap",three
assert three["experimentVariant"]==3,three
assert three["experimentExhausted"] is False,three
assert three["repairScope"]=="capability",three
assert three["action"]=="probe-targeted-repair",three
assert "adaptive_runtime_recovery" in three["allowedProfiles"],three

four=run([base(0),base(1),base(2),base(3)])
assert four["failureClass"]=="chain_terminal_gap",four
assert four["experimentVariant"]==4,four
assert four["experimentExhausted"] is False,four
assert four["repairScope"]=="capability",four
assert four["action"]=="probe-targeted-repair",four
assert "adaptive_runtime_recovery" in four["allowedProfiles"],four

five=run([base(0),base(1),base(2),base(3),base(4)])
assert five["failureClass"]=="chain_terminal_gap",five
assert five["experimentExhausted"] is True,five
assert five["repairScope"]=="deferred",five
assert five["repairType"]=="experiment_strategy_exhausted",five
assert five["repairEngine"]=="independent_learning_queue",five
assert five["pipelineStage"]=="deferred_learning",five
assert five["learningDisposition"]=="queue_new_strategy_after_variant_exhaustion",five
assert five["action"]=="deferred_retry",five
assert five["exitReason"]=="experiment_variants_exhausted",five
assert five["hypotheses"]==[],five
assert five["allowedProfiles"]==[],five

print("Brain negative experiment exhaustion contract passed")
