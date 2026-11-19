#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/select_residential_provider_replay.py"
spec=importlib.util.spec_from_file_location("select_residential",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

report={
    "residentialExitNodeEvidence":{"available":True},
    "rows":[
        {
            "provider":"yflix","lane":"movie","seedKind":"network-failure-replay",
            "directHttpProfile":{"outcome":"direct_http_content_reached"},
            "residentialExitNodeProfile":{"directHttpProfile":{"outcome":"direct_http_content_reached"}},
        },
        {
            "provider":"waf-only","lane":"movie","seedKind":"metadata-homepage",
            "directHttpProfile":{"outcome":"direct_http_challenge_persisted"},
            "residentialExitNodeProfile":{"directHttpProfile":{"outcome":"direct_http_challenge_persisted"}},
        },
    ],
}
status={
    "providers":[
        {"provider":"yflix","status":"PROVIDER NETWORK BLOCKED"},
        {"provider":"waf-only","status":"HARNESS MISMATCH"},
        {"provider":"client-gap","status":"CLIENT TRANSPORT GAP"},
        {"provider":"all-blocked","status":"HARNESS/ENV BLOCKED","authorityRepairEligible":True},
        {"provider":"authority-blocked","status":"HARNESS/ENV BLOCKED","authorityRepairEligible":False},
        {"provider":"green","status":"FULL OK"},
        {"provider":"route","status":"ROUTE PROVEN"},
    ],
    "environmentQueue":["waf-only","client-gap","all-blocked"],
    "repairQueue":["yflix","route"],
}
selected=mod.select(report,status)
assert selected==["all-blocked","client-gap","waf-only","yflix"],selected
assert "green" not in selected and "route" not in selected
assert "authority-blocked" not in selected

explicit=mod.select(report,status,["route","green","authority-blocked","missing"])
assert explicit==["all-blocked","client-gap","green","route","waf-only","yflix"],explicit
assert "green" in explicit and "route" in explicit
assert "authority-blocked" not in explicit

bounded=mod.select(report,status,["route","green","authority-blocked","missing"],restrict_to_explicit=True)
assert bounded==["green","route"],bounded
assert "all-blocked" not in bounded

# Explicit diagnostic execution authority is distinct from Repair mutation
# authority. An active canonical provider may be full-replayed read-only even
# while authorityRepairEligible remains false. Merely naming an inactive/missing
# provider still grants nothing.
active_bounded=mod.select(
    report,status,["authority-blocked","missing"],
    active_transport_allowed={"authority-blocked"},
    restrict_to_explicit=True,
)
assert active_bounded==["authority-blocked"],active_bounded
active_unbounded=mod.select(
    report,status,["authority-blocked"],
    active_transport_allowed={"authority-blocked"},
)
assert active_unbounded==["all-blocked","authority-blocked","client-gap","waf-only","yflix"],active_unbounded
assert status["providers"][4]["authorityRepairEligible"] is False
try:
    mod.select(report,status,restrict_to_explicit=True)
except ValueError:
    pass
else:
    raise AssertionError("empty explicit replay must fail closed")

# Exact-byte offline activation may authorize residential transport replay without
# granting Repair authority. This is transport-only and must be explicitly bounded.
offline=mod.select(
    report,status,["authority-blocked"],
    offline_transport_allowed={"authority-blocked"},
)
assert offline==["all-blocked","authority-blocked","client-gap","waf-only","yflix"],offline
offline_bounded=mod.select(
    report,status,["authority-blocked"],
    offline_transport_allowed={"authority-blocked"},
    restrict_to_explicit=True,
)
assert offline_bounded==["authority-blocked"],offline_bounded

unavailable={"residentialExitNodeEvidence":{"available":False}}
assert mod.select(unavailable,status)==[]
assert mod.ELIGIBLE_STATUSES=={
    "HARNESS MISMATCH","CLIENT TRANSPORT GAP","HARNESS/ENV BLOCKED","PROVIDER NETWORK BLOCKED"
}

print("residential full-provider replay selection contract passed")
