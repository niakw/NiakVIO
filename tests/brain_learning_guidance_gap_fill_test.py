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
assert unchanged==kept,(unchanged,kept)

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

print("Brain Learning post-eviction gap-fill contract passed")
