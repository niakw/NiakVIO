#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"filter_brain_learning_guidance.py"
spec=importlib.util.spec_from_file_location("learning_guidance_filter",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

dead="16ad894fc3c03be89539c14fb749def9501831b455f58f6f6f475b20acd36ad6"
live="a"*64
payload={
    "schemaVersion":2,
    "sourceSha":"1"*40,
    "brainLlmSha":"2"*40,
    "publicationAuthority":False,
    "directMutationAuthority":False,
    "proofAuthority":False,
    "rawMutationContentRetained":False,
    "providerCount":2,
    "rows":[
        {
            "providerId":"moviebox",
            "failureClass":"route-proven-gap",
            "targetLayer":"provider",
            "strategy":"search-detail-player-terminal-traversal",
            "profile":"proven_route_terminal_traversal_v1",
            "confidence":0.96,
            "priorOnly":True,
            "experiment":{},
            "experimentFingerprint":dead,
        },
        {
            "providerId":"vidfast",
            "failureClass":"route-proven-gap",
            "targetLayer":"provider",
            "strategy":"discover-api-from-current-page-and-bundles",
            "profile":"search_contract_inference_v1",
            "confidence":0.96,
            "priorOnly":True,
            "experiment":{},
            "experimentFingerprint":live,
        },
    ],
}
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"repair-memory.json"
    memory.write_text(json.dumps({
        "entries":[{
            "providerId":"moviebox",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":dead,
            "consecutiveFailures":1,
            "failures":1,
            "executionObserved":True,
            "lastOutcome":"rejected",
            "lastReason":"introduced_runtime_error",
        }]
    }),encoding="utf-8")
    filtered,dropped=mod.filter_guidance(payload,[memory])

assert dropped==1,(filtered,dropped)
assert filtered["providerCount"]==1,filtered
assert [r["providerId"] for r in filtered["rows"]]==["vidfast"],filtered
assert filtered["rows"][0]["experimentFingerprint"]==live

# Non-executed/unavailable attempts are not exact negative execution proof and
# must not poison a future executable hypothesis.
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"repair-memory.json"
    memory.write_text(json.dumps({
        "entries":[{
            "providerId":"moviebox",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":dead,
            "consecutiveFailures":0,
            "failures":1,
            "executionObserved":False,
            "lastOutcome":"profile_unavailable",
        }]
    }),encoding="utf-8")
    filtered,dropped=mod.filter_guidance(payload,[memory])
assert dropped==0,(filtered,dropped)
assert filtered["providerCount"]==2,filtered

print("Brain Learning negative-guidance filter contract passed")
