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
        {"provider":"all-blocked","status":"HARNESS/ENV BLOCKED"},
        {"provider":"green","status":"FULL OK"},
        {"provider":"route","status":"ROUTE PROVEN"},
    ],
    "environmentQueue":["waf-only","all-blocked"],
    "repairQueue":["yflix","route"],
}
selected=mod.select(report,status)
assert selected==["all-blocked","waf-only","yflix"],selected
assert "green" not in selected and "route" not in selected

unavailable={"residentialExitNodeEvidence":{"available":False}}
assert mod.select(unavailable,status)==[]
assert mod.ELIGIBLE_STATUSES=={
    "HARNESS MISMATCH","HARNESS/ENV BLOCKED","PROVIDER NETWORK BLOCKED"
}

print("residential full-provider replay selection contract passed")
