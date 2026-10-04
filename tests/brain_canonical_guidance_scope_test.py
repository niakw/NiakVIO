#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"scope_brain_guidance_to_repair_cohort.py"
spec=importlib.util.spec_from_file_location("scope_guidance",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

payload={
    "schemaVersion":2,
    "providerCount":2,
    "rows":[
        {"providerId":"coflix","profile":"player_media_extractor_v1"},
        {"providerId":"moviebox","profile":"search_contract_inference_v1"},
    ],
}
scoped,present=mod.scope_payload(payload,["MovieBox"])
assert scoped["providerCount"]==1,(scoped,present)
assert present==["moviebox"],present
assert [row["providerId"] for row in scoped["rows"]]==["moviebox"],scoped

missing,present=mod.scope_payload(payload,["mallumv"])
assert missing["providerCount"]==0,(missing,present)
assert present==[],present
assert missing["rows"]==[],missing

global_payload,present=mod.scope_payload(payload,[])
assert global_payload["providerCount"]==2,(global_payload,present)
assert present==["coflix","moviebox"],present
assert len(global_payload["rows"])==2,global_payload

print("Canonical Repair guidance cohort scope contract passed")
