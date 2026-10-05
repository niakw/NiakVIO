#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"fill_brain_learning_guidance_gaps.py"
spec=importlib.util.spec_from_file_location("fill_guidance",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

old_row={
    "providerId":"moviebox",
    "failureClass":"route_proven_gap",
    "targetLayer":"provider",
    "strategy":"meta-gap-search-contract-fallback",
    "profile":"search_contract_inference_v1",
    "confidence":0.86,
    "priorOnly":True,
    "experiment":{"routePolicy":"owned_plus_peer"},
    "experimentFingerprint":"a"*64,
}
next_row={
    "providerId":"moviebox",
    "failureClass":"route_proven_gap",
    "targetLayer":"provider",
    "strategy":"meta-gap-adaptive-runtime-fallback",
    "profile":"adaptive_runtime_recovery",
    "confidence":0.86,
    "priorOnly":True,
    "experiment":{"routePolicy":"owned_only"},
    "experimentFingerprint":"b"*64,
    "guidanceKind":"meta-gap-synthesis",
    "sourceSha":"1"*40,
}
payload={
    "schemaVersion":2,
    "sourceSha":"0"*40,
    "brainLlmSha":"2"*40,
    "publicationAuthority":False,
    "directMutationAuthority":False,
    "proofAuthority":False,
    "rawMutationContentRetained":False,
    "providerCount":1,
    "rows":[old_row],
}
original=mod.synthesize_rows
try:
    mod.synthesize_rows=lambda **_kwargs:[next_row]
    out,advanced=mod.fill(
        payload,
        providers=["moviebox"],
        current_sha="1"*40,
        census={"repairQueue":["moviebox"],"providers":[]},
        memory={"entries":[]},
    )
    assert advanced==["moviebox"],advanced
    assert out["providerCount"]==1,out
    profiles=[row["profile"] for row in out["rows"]]
    assert profiles==["search_contract_inference_v1","adaptive_runtime_recovery"],profiles
    assert out["sourceSha"]=="1"*40,out["sourceSha"]
    # Public persistence strips internal synthesis-only metadata.
    assert set(out["rows"][-1])==mod.ROW_FIELDS,out["rows"][-1]

    # The same synthesized executor/fingerprint is idempotent.
    out2,advanced2=mod.fill(
        out,
        providers=["moviebox"],
        current_sha="1"*40,
        census={"repairQueue":["moviebox"],"providers":[]},
        memory={"entries":[]},
    )
    assert advanced2==[],advanced2
    assert len(out2["rows"])==2,out2["rows"]
finally:
    mod.synthesize_rows=original

print("Brain Learning guidance executor-advance contract passed")
