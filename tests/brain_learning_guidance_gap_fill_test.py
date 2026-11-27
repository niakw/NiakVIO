#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"fill_brain_learning_guidance_gaps.py"
spec=importlib.util.spec_from_file_location("fill_learning_guidance",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

payload={
    "schemaVersion":2,
    "sourceSha":"1"*40,
    "brainLlmSha":"2"*40,
    "publicationAuthority":False,
    "directMutationAuthority":False,
    "proofAuthority":False,
    "rawMutationContentRetained":False,
    "minConfidence":0.8,
    "providerCount":0,
    "rows":[],
}
census={
    "repairQueue":["moviebox"],
    "providers":[{
        "provider":"moviebox",
        "status":"ROUTE PROVEN",
        "dominantIssue":"route_proven_gap",
        "evidenceDepth":["route_proven"],
    }],
}
memory={"entries":[]}
for index in range(3):
    memory["entries"].append({
        "providerId":"moviebox",
        "failureClass":"route_proven_gap",
        "profile":"proven_route_terminal_traversal_v1",
        "llmAdvisorExperimentFingerprint":f"{index+1:064x}",
        "experimentVariant":4,
        "experimentGeneration":2,
        "failures":1,
        "consecutiveFailures":1,
        "progresses":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"exploration_progress_nonpublishable",
        "lastReason":"required_category_playable_proof:movie",
    })

filled,added=mod.fill(
    payload,
    providers=["moviebox"],
    current_sha="3"*40,
    census=census,
    memory=memory,
)
assert added==["moviebox"],(filled,added)
assert filled["providerCount"]==1,filled
row=filled["rows"][0]
assert row["providerId"]=="moviebox",row
assert row["failureClass"]=="route_proven_gap",row
assert row["profile"]=="search_contract_inference_v1",row
assert row["strategy"]=="meta-gap-search-contract-fallback",row
assert row["priorOnly"] is True,row
assert len(row["experimentFingerprint"])==64,row
assert set(row)==mod.ROW_FIELDS,row
assert filled["sourceSha"]=="3"*40,filled

# Existing surviving guidance wins. Gap filling must not add a second advisor
# merely because another profile could be synthesized.
kept={**payload,"providerCount":1,"rows":[row]}
unchanged,added=mod.fill(
    kept,
    providers=["moviebox"],
    current_sha="3"*40,
    census=census,
    memory=memory,
)
assert added==[],(unchanged,added)
assert unchanged["rows"]==kept["rows"],(unchanged,kept)
assert unchanged["providerCount"]==kept["providerCount"],(unchanged,kept)
assert unchanged["sourceSha"]=="3"*40,unchanged

# Providers outside current Repair debt never receive synthetic guidance.
not_debt,added=mod.fill(
    payload,
    providers=["not-in-repair"],
    current_sha="3"*40,
    census=census,
    memory=memory,
)
assert added==[],(not_debt,added)
assert not_debt["providerCount"]==0,not_debt


# Cross-day Learning memory is causal input to the same synthesizer as canonical
# Repair memory. A fingerprint rejected only in previous Learning must not be
# presented again merely because automation/brain-repair-memory.json lags it.
cross_day={
    "experimentMemory":{"entries":[{
        "providerId":"moviebox",
        "failureClass":"route_proven_gap",
        "profile":"search_contract_inference_v1",
        "llmAdvisorExperimentFingerprint":"f"*64,
        "experimentVariant":4,
        "experimentGeneration":2,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"inferior_to_selected_variant",
    }]}
}
repair={"entries":[{
    "providerId":"moviebox",
    "failureClass":"route_proven_gap",
    "profile":"proven_route_terminal_traversal_v1",
    "llmAdvisorExperimentFingerprint":"e"*64,
    "experimentVariant":4,
    "experimentGeneration":2,
    "failures":1,
    "consecutiveFailures":1,
    "successes":0,
    "executionObserved":True,
    "lastOutcome":"rejected",
    "lastReason":"required_category_playable_proof:movie",
}]}
merged=mod.merge_memory_payloads([cross_day,repair])
assert len(merged["entries"])==2,merged
assert {row["llmAdvisorExperimentFingerprint"] for row in merged["entries"]}=={"e"*64,"f"*64},merged

# Stronger regression: synthesize the actual first route-proven meta-gap,
# record exactly that fingerprint only in cross-day Learning memory, then
# require the same synthesizer to advance to a different experiment.
empty_first=mod.synthesize_rows(census=census,memory={"entries":[]},current_sha="3"*40,max_rows=128)
first_moviebox=next(row for row in empty_first if row["providerId"]=="moviebox")
cross_day_only={
    "experimentMemory":{"entries":[{
        "providerId":"moviebox",
        "failureClass":first_moviebox["failureClass"],
        "profile":first_moviebox["profile"],
        "llmAdvisorExperimentFingerprint":first_moviebox["experimentFingerprint"],
        "experimentVariant":4,
        "experimentGeneration":2,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
        "lastOutcome":"rejected",
        "lastReason":"inferior_to_selected_variant",
    }]}
}
rotated_memory=mod.merge_memory_payloads([cross_day_only,{"entries":[]}])
rotated=mod.synthesize_rows(census=census,memory=rotated_memory,current_sha="3"*40,max_rows=128)
rotated_moviebox=next(row for row in rotated if row["providerId"]=="moviebox")
assert rotated_moviebox["experimentFingerprint"]!=first_moviebox["experimentFingerprint"],(
    first_moviebox,rotated_moviebox
)

print("Brain Learning post-eviction gap-fill contract passed")
