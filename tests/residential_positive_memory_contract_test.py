#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"reconcile_residential_positive_memory.py"
spec=importlib.util.spec_from_file_location("residential_positive_memory",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

manifest={"scrapers":[{"id":"alpha","filename":"providers/alpha--nuvio--aaaaaaaaaaaaaaaa.js"}]}
memory={
    "schemaVersion":1,
    "rows":[{
        "provider":"alpha","lane":"movie","status":"playable_verified",
        "debugStage":"provider_returned_streams","raw":1,"playable":1,"verified":1,
        "contradictions":0,"identitySafe":True,
        "publishedFile":"providers/alpha--nuvio--aaaaaaaaaaaaaaaa.js",
        "sourceSha":"a"*40,
    }],
}
pre_provider={
    "residentialProviderReplay":{
        "rows":[{
            "provider":"alpha","lane":"movie","status":"no_streams",
            "debugStage":"provider_zero_before_provider_network",
            "raw":0,"playable":0,"verified":0,"contradictions":0,"identitySafe":True,
        }]
    }
}
merged,next_memory=mod.reconcile(pre_provider,memory,manifest,source_sha="b"*40)
row=merged["residentialProviderReplay"]["rows"][0]
assert row["status"]=="playable_verified",row
assert row["verified"]==1,row
assert row["retainedFromResidentialPositiveMemory"] is True,row
assert row["currentAttemptStage"]=="provider_zero_before_provider_network",row
assert merged["residentialProviderReplay"]["verifiedProviders"]==["alpha"],merged
assert len(next_memory["rows"])==1,next_memory

# A real provider/network result can supersede the retained proof.
post_provider={
    "residentialProviderReplay":{
        "rows":[{
            "provider":"alpha","lane":"movie","status":"no_streams",
            "debugStage":"provider_network_zero_result",
            "raw":0,"playable":0,"verified":0,"contradictions":0,"identitySafe":True,
        }]
    }
}
merged2,memory2=mod.reconcile(post_provider,memory,manifest,source_sha="c"*40)
assert merged2["residentialProviderReplay"]["rows"][0]["verified"]==0,merged2
assert memory2["rows"]==[],memory2
assert merged2["residentialProviderReplay"]["positiveMemoryInvalidated"]==["alpha:movie"],merged2

# Content-addressed filename changes invalidate the old proof before overlay.
changed={"scrapers":[{"id":"alpha","filename":"providers/alpha--nuvio--bbbbbbbbbbbbbbbb.js"}]}
merged3,memory3=mod.reconcile(pre_provider,memory,changed,source_sha="d"*40)
assert merged3["residentialProviderReplay"]["rows"][0]["verified"]==0,merged3
assert memory3["rows"]==[],memory3

print("Residential positive memory contract passed")
