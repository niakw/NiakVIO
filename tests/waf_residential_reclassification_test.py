#!/usr/bin/env python3
from __future__ import annotations

import copy
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

harness_zero_baseline={
    "schemaVersion":3,
    "repairQueue":[],
    "environmentQueue":["env-zero"],
    "harnessQueue":["env-zero"],
    "symptomaticProviders":["env-zero"],
    "brainQueue":["env-zero"],
    "providers":[{
        "provider":"env-zero",
        "status":"HARNESS/ENV BLOCKED",
        "color":"🟫",
        "routeProof":["1 live routes / movie"],
        "evidenceDepth":["movie=lookup_only"],
        "authorityRepairEligible":True,
        "authorityAction":"KEEP_ROUTE_AUTHORITY",
        "authorityClass":"hub-or-redirect",
        "repairEligible":False,
        "brainCheckRequired":True,
    }],
}
harness_zero_waf={
    "rows":[{
        "provider":"env-zero",
        "lane":"movie",
        "outcome":"browser_challenge_persisted",
        "residentialExitNodeProfile":{
            "outcome":"browser_challenge_persisted",
            "directHttpProfile":{"outcome":"direct_http_challenge_persisted"},
            "okHttpJvmProfile":{"outcome":"okhttp_jvm_challenge_persisted"},
        },
    }],
    "residentialProviderReplay":{
        "available":True,
        "rows":[{
            "provider":"env-zero",
            "lane":"movie",
            "status":"no_streams",
            "debugStage":"provider_network_zero_result",
            "raw":0,"playable":0,"verified":0,"contradictions":0,
            "identitySafe":True,
        }],
    },
}
harness_zero=mod.merge_transport(harness_zero_baseline,harness_zero_waf)
row=harness_zero["providers"][0]
assert row["status"]=="ROUTE PROVEN",row
assert row["repairEligible"] is True,row
assert row["residentialProviderReplayReclassified"] is True,row
assert harness_zero["repairQueue"]==["env-zero"],harness_zero
assert harness_zero["environmentQueue"]==[],harness_zero

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
assert row["status"]=="CLIENT TRANSPORT GAP",row
assert row["harnessTransportClass"]=="browser-profile-only-both-networks",row
assert row["repairEligible"] is False,row
assert row["testedThisRun"] is True,row
assert tls["repairQueue"]==[],tls
assert tls["environmentQueue"]==["tls-browser-only"],tls
assert tls["clientTransportGapQueue"]==["tls-browser-only"],tls

# Current-byte replays may reclassify, but a stale/MISSING digest cannot
# silently promote a previously blocked new JS generation on main.
for measured_sha, expected_reclassified in (
    ("", False),
    ("b" * 64, False),
    ("a" * 64, True),
):
    baseline = copy.deepcopy(harness_zero_baseline)
    baseline["providers"][0]["providerArtifactSha256"] = "a" * 64
    waf = copy.deepcopy(harness_zero_waf)
    waf["residentialProviderReplay"]["rows"][0]["providerArtifactSha256"] = measured_sha
    result = mod.merge_transport(baseline, waf)
    provider = result["providers"][0]
    assert bool(provider.get("residentialProviderReplayReclassified")) is expected_reclassified, (
        measured_sha, provider,
    )
    assert ("env-zero" in result.get("residentialProviderReplayReclassifiedProviders", [])) is expected_reclassified
    if not expected_reclassified:
        assert not provider.get("residentialProviderReplayClass"), provider

print("residential zero-result and browser-only transport reclassification tests passed")
