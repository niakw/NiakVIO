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
        {"groupId":"transport","repairScope":"transport","providers":["network"],"capabilityStrategy":"html_scraper"},
        {"groupId":"tls","repairScope":"harness-compatibility","providers":["tls"],"capabilityStrategy":"mixed_embed_resolver","transportSignature":"browser-profile-only-both-networks"},
        {"groupId":"challenge","repairScope":"harness-compatibility","providers":["challenge"],"capabilityStrategy":"html_scraper","transportSignature":"residential-exit-all-challenged"},
        {"groupId":"learn","repairScope":"learning","providers":["unknown"],"capabilityStrategy":"unknown"},
    ],
}
status={
    "runId":"run",
    "triggerSha":"sha",
    "repairQueue":["candidate","route","chain","network","unknown"],
    "environmentQueue":["tls","challenge"],
}
out=mod.build(batch,status)
by={row["groupId"]:row for row in out["executions"]}
assert by["candidate"]["lane"]=="REMAT_TEST" and by["candidate"]["fallbackLane"]=="FAST_REPAIR"
assert by["route"]["lane"]=="FAST_REPAIR"
assert by["chain"]["lane"]=="FAST_REPAIR"
assert by["transport"]["lane"]=="DOMAIN_REFRESH"
assert by["tls"]["lane"]=="CORE_CLIENT_LEARNING"
assert by["tls"]["strategyBlueprint"]=="native_tls_browser_differential_v1"
assert by["tls"]["dispatchAllowed"] is True
assert by["tls"]["workflow"]=="provider-waf-browser-session.yml"
assert by["tls"]["mutatesProduction"] is False
assert by["tls"]["applicationValidated"] is False
assert by["challenge"]["strategyBlueprint"]=="persistent_challenge_session_boundary_v1"
assert by["learn"]["lane"]=="BRAIN_LEARNING"
assert out["providerCount"]==7
assert out["blockedExecutionCount"]==0

# A stale/mismatched batch may never auto-dispatch.
bad_status={**status,"repairQueue":["route","chain","network","unknown"]}
bad=mod.build(batch,bad_status)
candidate=next(row for row in bad["executions"] if row["groupId"]=="candidate")
assert candidate["dispatchAllowed"] is False
assert candidate["queueMismatchProviders"]==["candidate"]

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "causal-owner-router",
    "deepest-current-proof-owns-lane",
    "CORE_CLIENT_LEARNING",
    "REMAT_TEST",
    "FAST_REPAIR",
    "DOMAIN_REFRESH",
    "BRAIN_LEARNING",
):
    assert required in source,required

print("provider causal execution router contract passed")
