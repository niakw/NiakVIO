#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"merge_waf_census_transport.py"
spec=importlib.util.spec_from_file_location("merge_transport",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

zero_baseline={
    "schemaVersion":3,
    "repairQueue":["net-zero"],
    "environmentQueue":[],
    "harnessQueue":[],
    "symptomaticProviders":["net-zero"],
    "brainQueue":["net-zero"],
    "providers":[{
        "provider":"net-zero",
        "status":"PROVIDER NETWORK BLOCKED",
        "color":"🟤",
        "routeProof":["1 live routes / anime"],
        "evidenceDepth":["anime=lookup_only"],
        "authorityRepairEligible":True,
        "authorityAction":"KEEP_PROVEN_SITE",
        "authorityClass":"structured-site-plus-route-proof",
        "repairEligible":True,
        "brainCheckRequired":True,
    }],
}
zero_waf={
    "rows":[],
    "residentialProviderReplay":{
        "available":True,
        "rows":[{
            "provider":"net-zero",
            "lane":"anime",
            "status":"no_streams",
            "debugStage":"provider_network_zero_result",
            "raw":0,"playable":0,"verified":0,"contradictions":0,
            "identitySafe":True,
        }],
    },
}
zero=mod.merge_transport(zero_baseline,zero_waf)
row=zero["providers"][0]
assert row["status"]=="ROUTE PROVEN",row
assert row["repairEligible"] is True,row
assert row["residentialProviderReplayReclassified"] is True,row
assert zero["repairQueue"]==["net-zero"],zero
assert zero["environmentQueue"]==[],zero

tls_baseline={
    "schemaVersion":3,
    "repairQueue":["tls-browser-only"],
    "environmentQueue":[],
    "harnessQueue":[],
    "symptomaticProviders":["tls-browser-only"],
    "brainQueue":["tls-browser-only"],
    "providers":[{
        "provider":"tls-browser-only",
        "status":"PROVIDER NETWORK BLOCKED",
        "color":"🟤",
        "routeProof":["1 live routes / anime"],
        "evidenceDepth":["anime=none"],
        "authorityRepairEligible":True,
        "authorityAction":"KEEP_DIRECT",
        "authorityClass":"direct",
        "repairEligible":True,
        "brainCheckRequired":True,
    }],
}
tls_waf={
    "rows":[{
        "provider":"tls-browser-only",
        "lane":"anime",
        "seedKind":"network-failure-replay",
        "outcome":"browser_content_reached",
        "directHttpProfile":{"outcome":"direct_http_error"},
        "okHttpJvmProfile":{"outcome":"okhttp_jvm_error"},
        "residentialExitNodeProfile":{
            "outcome":"browser_content_reached",
            "directHttpProfile":{"outcome":"direct_http_error"},
            "okHttpJvmProfile":{"outcome":"okhttp_jvm_error"},
        },
    }],
    "residentialProviderReplay":{
        "available":True,
        "rows":[{
            "provider":"tls-browser-only",
            "lane":"anime",
            "status":"no_streams",
            "debugStage":"provider_network_exception",
            "raw":0,"playable":0,"verified":0,"contradictions":0,
            "identitySafe":True,
        }],
    },
}
tls=mod.merge_transport(tls_baseline,tls_waf)
row=tls["providers"][0]
assert row["status"]=="HARNESS MISMATCH",row
assert row["harnessTransportClass"]=="browser-profile-only-both-networks",row
assert row["repairEligible"] is False,row
assert tls["repairQueue"]==[],tls
assert tls["environmentQueue"]==["tls-browser-only"],tls

print("residential zero-result and browser-only transport reclassification tests passed")
