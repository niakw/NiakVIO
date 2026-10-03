#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"build_provider_execution_plan.py"
spec=importlib.util.spec_from_file_location("provider_execution_plan",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

batch={
    "sourceRunId":"run",
    "groups":[
        {"groupId":"candidate","repairScope":"candidate-replay","providers":["candidate"],"capabilityStrategy":"direct_media"},
        {"groupId":"route","repairScope":"route-to-terminal","providers":["route"],"capabilityStrategy":"html_scraper"},
        {"groupId":"chain","repairScope":"terminal-extraction","providers":["chain"],"capabilityStrategy":"direct_media"},
        {"groupId":"transport","repairScope":"transport","providers":["network","domain"],"capabilityStrategy":"html_scraper"},
        {"groupId":"tls","repairScope":"harness-compatibility","providers":["tls"],"capabilityStrategy":"mixed_embed_resolver","transportSignature":"browser-profile-only-both-networks"},
        {"groupId":"challenge","repairScope":"harness-compatibility","providers":["challenge"],"capabilityStrategy":"html_scraper","transportSignature":"residential-exit-all-challenged"},
        {"groupId":"variant","repairScope":"variant-coverage","providers":["green"],"capabilityStrategy":"html_scraper","selectionAuthorities":["provider-census-sharded-latest.json:dynamic-variant-debt"],"dynamicVariantProviders":["green"]},
        {"groupId":"learn","repairScope":"learning","providers":["unknown"],"capabilityStrategy":"unknown"},
    ],
}
status={
    "runId":"run",
    "triggerSha":"sha",
    "repairQueue":["candidate","route","chain","network","domain","unknown"],
    "providers":[
        {"provider":"network","authorityAction":"KEEP_PROVEN_SITE"},
        {"provider":"domain","authorityAction":"KEEP_DIAGNOSTIC"},
    ],
    "environmentQueue":["tls"],
    "targetedTransportBlockedQueue":["challenge"],
}
out=mod.build(batch,status,{"green"})
by={row["groupId"]:row for row in out["executions"]}
assert by["candidate"]["lane"]=="REMAT_TEST" and by["candidate"]["fallbackLane"]=="FAST_REPAIR"
assert by["route"]["lane"]=="FAST_REPAIR"
assert by["chain"]["lane"]=="FAST_REPAIR"
transport_rows=[row for row in out["executions"] if row["repairScope"]=="transport"]
network_row=next(row for row in transport_rows if row["providers"]==["network"])
domain_row=next(row for row in transport_rows if row["providers"]==["domain"])
assert network_row["lane"]=="BRAIN_LEARNING" and network_row["strategyBlueprint"]=="qualified_authority_transport_learning_v1"
assert domain_row["lane"]=="DOMAIN_REFRESH" and domain_row["authorityQualified"] is False
assert by["tls"]["lane"]=="CORE_CLIENT_LEARNING"
assert by["tls"]["strategyBlueprint"]=="native_tls_browser_differential_v1"
assert by["tls"]["dispatchAllowed"] is True
assert by["tls"]["workflow"]=="provider-waf-browser-session.yml"
assert by["tls"]["mutatesProduction"] is False
assert by["tls"]["applicationValidated"] is False
assert by["challenge"]["strategyBlueprint"]=="persistent_challenge_session_boundary_v1"
assert by["variant"]["lane"]=="BRAIN_LEARNING"
assert by["variant"]["dispatchAllowed"] is True
assert by["variant"]["mutatesProduction"] is False
assert by["learn"]["lane"]=="BRAIN_LEARNING"
assert out["providerCount"]==9
assert out["blockedExecutionCount"]==0

# A stale/mismatched batch may never auto-dispatch.
bad_status={**status,"repairQueue":["route","chain","network","domain","unknown"]}
bad=mod.build(batch,bad_status,{"green"})
candidate=next(row for row in bad["executions"] if row["groupId"]=="candidate")
assert candidate["dispatchAllowed"] is False
assert candidate["queueMismatchProviders"]==["candidate"]
no_dynamic=mod.build(batch,status,set())
variant=next(row for row in no_dynamic["executions"] if row["groupId"]=="variant")
assert variant["dispatchAllowed"] is False
assert variant["queueMismatchProviders"]==["green"]

refined={
    "sourceRunId":"run",
    "groups":[
        {**row,"groupId":str(row["groupId"])+"#r1"}
        for row in batch["groups"]
    ],
}
selected,source_name=mod.select_batch_plan(batch,refined,status,{"green"})
assert source_name=="sharded-refined"
assert mod.plan_providers(selected)==mod.plan_providers(batch)

stale={**refined,"sourceRunId":"old"}
selected,source_name=mod.select_batch_plan(batch,stale,status,{"green"})
assert selected is batch and source_name=="canonical-stale-refined"

missing={**refined,"groups":refined["groups"][:-1]}
selected,source_name=mod.select_batch_plan(batch,missing,status,{"green"})
assert selected is batch and source_name=="canonical-refined-provider-mismatch"

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "causal-owner-router",
    "deepest-current-proof-owns-lane",
    "CORE_CLIENT_LEARNING",
    "REMAT_TEST",
    "FAST_REPAIR",
    "DOMAIN_REFRESH",
    "BRAIN_LEARNING",
    "variant-coverage",
    "provider-census-sharded-latest.json",
    "sharded-refined",
    "targetedTransportBlockedQueue",
):
    assert required in source,required

print("provider causal execution router contract passed")
