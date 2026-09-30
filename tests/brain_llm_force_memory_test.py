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
    }],
}
one=mod.merge(base,failed)
assert len(one["entries"])==1
row=one["entries"][0]
assert row["failures"]==1
assert row["consecutiveFailures"]==1
assert row["successes"]==0
assert row["lastOutcome"]=="rejected"

two=mod.merge(one,failed)
row=two["entries"][0]
assert row["failures"]==2
assert row["consecutiveFailures"]==2

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
