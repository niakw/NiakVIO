#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"update_brain_llm_force_memory.py"
spec=importlib.util.spec_from_file_location("force_memory",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

fp_a="a"*64
ctx_a="b"*64
base={"schemaVersion":1,"entries":[]}
failed={
    "currentSha":"c"*40,
    "sourceNiakvioSha":"d"*40,
    "sourceBrainLlmSha":"e"*40,
    "rows":[{
        "provider":"demo",
        "mutationFingerprint":fp_a,
        "mutationContextFingerprint":ctx_a,
        "accepted":False,
        "reason":"insufficient_playable_stream_proof",
        "baseline":{
            "streamsReturned":7,
            "streamsPlayable":5,
            "identityContradictions":0,
            "variantCoverage":{
                "qualityHeights":[480,720],
                "announcedQualityHeights":[480,720,1080,2160],
                "maxPlayableHeight":720,
                "announcedPlayerCandidates":20,
                "announcedVariantCandidates":40,
                "exploredPlayerRequests":16,
                "reachableHosts":["a.example","b.example"],
                "fanoutStates":["returned-subset","explored-not-resolved"],
            },
        },
        "candidate":{
            "streamsReturned":5,
            "streamsPlayable":5,
            "identityContradictions":0,
            "variantCoverage":{
                "qualityHeights":[480],
                "announcedQualityHeights":[480,720,1080,2160],
                "maxPlayableHeight":480,
                "announcedPlayerCandidates":20,
                "announcedVariantCandidates":27,
                "exploredPlayerRequests":8,
                "reachableHosts":["a.example"],
                "fanoutStates":["returned-subset"],
            },
        },
    }],
}
one=mod.merge(base,failed)
assert len(one["entries"])==1
row=one["entries"][0]
assert row["failures"]==1
assert row["consecutiveFailures"]==1
assert row["successes"]==0
assert row["lastOutcome"]=="rejected"
assert row["lastBaselineCoverage"]=={
    "streamsReturned":7,
    "streamsPlayable":5,
    "identityContradictions":0,
    "qualityHeights":[480,720],
    "announcedQualityHeights":[480,720,1080,2160],
    "maxPlayableHeight":720,
    "announcedPlayerCandidates":20,
    "announcedVariantCandidates":40,
    "exploredPlayerRequests":16,
    "reachableHostCount":2,
    "fanoutStates":["explored-not-resolved","returned-subset"],
}
assert row["lastCandidateCoverage"]["qualityHeights"]==[480]
assert row["lastCandidateCoverage"]["maxPlayableHeight"]==480
assert row["lastCoverageDelta"]["streamsReturned"]==-2
assert row["lastCoverageDelta"]["streamsPlayable"]==0
assert row["lastCoverageDelta"]["maxPlayableHeight"]==-240
assert row["lastCoverageDelta"]["announcedVariantCandidates"]==-13
assert row["lastCoverageDelta"]["exploredPlayerRequests"]==-8
assert row["lastCoverageDelta"]["qualityHeightCount"]==-1
assert "a.example" not in str(row)
assert "b.example" not in str(row)

two=mod.merge(one,failed)
row=two["entries"][0]
assert row["failures"]==2
assert row["consecutiveFailures"]==2

not_executed={
    **failed,
    "rows":[{
        **failed["rows"][0],
        "mutationFingerprint":"9"*64,
        "mutationContextFingerprint":"8"*64,
        "accepted":False,
        "executionObserved":False,
        "reason":"skipped_after_provider_winner",
    }],
}
unchanged=mod.merge(two,not_executed)
assert len(unchanged["entries"])==1
assert unchanged["entries"][0]["mutationFingerprint"]==fp_a
assert unchanged["entries"][0]["failures"]==2

accepted={
    **failed,
    "rows":[{
        **failed["rows"][0],
        "accepted":True,
        "reason":"strict_playable_stream_improvement",
        "repairFamily":{
            "version":1,
            "key":"1"*64,
            "failure":"route-proven-gap",
            "status":"route-proven",
            "archetype":"route-proven-gap:mixed-tag-nested-container",
            "mediaTypes":["movie","tv"],
            "signals":["mixed-tag-nested-container"],
            "stages":["provider-network-zero-result"],
            "mutationSurfaces":["provider-patch"],
        },
        "mechanismFamily":"balanced-class-container",
    }],
}
three=mod.merge(two,accepted)
row=three["entries"][0]
assert row["failures"]==2
assert row["successes"]==1
assert row["consecutiveFailures"]==0
assert row["lastOutcome"]=="accepted"
assert three["schemaVersion"]==2
assert three["validatedFamilyCount"]==1
family=three["validatedFamilies"][0]
assert family["repairFamily"]["key"]=="1"*64
assert family["mechanismFamily"]=="balanced-class-container"
assert family["successCount"]==1
assert family["providers"]==["demo"]
assert family["autoApply"] is False

changed_context={
    **failed,
    "rows":[{
        **failed["rows"][0],
        "mutationContextFingerprint":"f"*64,
    }],
}
four=mod.merge(three,changed_context)
assert len(four["entries"])==2
assert {
    row["mutationContextFingerprint"] for row in four["entries"]
}=={ctx_a,"f"*64}

print("Brain LLM Force candidate memory tests passed")
