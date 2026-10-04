#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"import_persistent_brain_learning_guidance.py"
spec=importlib.util.spec_from_file_location("persistent_learning_import",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CURRENT="2"*40
SOURCE="1"*40
FP="a"*64

def payload(source=CURRENT):
    return {
        "schemaVersion":2,
        "sourceSha":source,
        "brainLlmSha":"b"*40,
        "publicationAuthority":False,
        "directMutationAuthority":False,
        "proofAuthority":False,
        "rawMutationContentRetained":False,
        "minConfidence":0.8,
        "providerCount":1,
        "rows":[{
            "providerId":"moviebox",
            "failureClass":"route_proven_gap",
            "targetLayer":"provider",
            "strategy":"meta-gap-search-contract-fallback",
            "profile":"search_contract_inference_v1",
            "confidence":0.86,
            "priorOnly":True,
            "experiment":{
                "routePolicy":"owned_plus_peer",
                "recipePolicy":"current_only",
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
            "experimentFingerprint":FP,
        }],
    }

normalized,stats=mod.normalize(payload(),current_sha=CURRENT,repo_root=ROOT,negative_memory={})
assert normalized["sourceSha"]==CURRENT,normalized
assert normalized["providerCount"]==1,normalized
row=normalized["rows"][0]
assert row["providerId"]=="moviebox",row
assert row["profile"]=="search_contract_inference_v1",row
assert row["experimentFingerprint"]==FP,row
assert row["guidanceKind"]=="meta-gap-synthesis",row
assert stats["droppedProviderDriftRows"]==0,stats

failed_memory={"entries":[{
    "providerId":"moviebox",
    "profile":"search_contract_inference_v1",
    "llmAdvisorExperimentFingerprint":FP,
    "consecutiveFailures":1,
    "executionObserved":True,
}]}
filtered,stats=mod.normalize(payload(),current_sha=CURRENT,repo_root=ROOT,negative_memory=failed_memory)
assert filtered["providerCount"]==0,filtered
assert filtered["rows"]==[],filtered
assert stats["droppedFailedFingerprintRows"]==1,stats

original=mod.source_drift
try:
    mod.source_drift=lambda _root,_source,_current:(["MEMORY.md"],{"moviebox"})
    drifted,stats=mod.normalize(payload(SOURCE),current_sha=CURRENT,repo_root=ROOT,negative_memory={})
finally:
    mod.source_drift=original
assert drifted["providerCount"]==0,drifted
assert drifted["rows"]==[],drifted
assert stats["droppedProviderDriftRows"]==1,stats

unsafe=payload()
unsafe["publicationAuthority"]=True
try:
    mod.normalize(unsafe,current_sha=CURRENT,repo_root=ROOT,negative_memory={})
except ValueError:
    pass
else:
    raise AssertionError("unsafe persistent Learning authority must be rejected")

print("Persistent Brain Learning guidance import contract passed")
