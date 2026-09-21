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
    "rows":[
        {
            "provider":"yflix","lane":"movie","seedKind":"network-failure-replay",
            "outcome":"browser_timeout",
            "directHttpProfile":{"outcome":"direct_http_timeout"},
            "okHttpJvmProfile":{"outcome":"okhttp_jvm_timeout"},
            "residentialExitNodeProfile":{
                "outcome":"browser_content_reached",
                "directHttpProfile":{"outcome":"direct_http_content_reached"},
                "okHttpJvmProfile":{"outcome":"okhttp_jvm_content_reached"},
            },
        },
        {
            "provider":"already-github","lane":"movie","seedKind":"network-failure-replay",
            "directHttpProfile":{"outcome":"direct_http_content_reached"},
            "okHttpJvmProfile":{"outcome":"okhttp_jvm_content_reached"},
            "residentialExitNodeProfile":{
                "directHttpProfile":{"outcome":"direct_http_content_reached"},
                "okHttpJvmProfile":{"outcome":"okhttp_jvm_content_reached"},
            },
        },
        {
            "provider":"waf-only","lane":"movie","seedKind":"metadata-homepage",
            "directHttpProfile":{"outcome":"direct_http_timeout"},
            "residentialExitNodeProfile":{
                "directHttpProfile":{"outcome":"direct_http_content_reached"},
            },
        },
        {
            "provider":"still-blocked","lane":"movie","seedKind":"network-failure-replay",
            "directHttpProfile":{"outcome":"direct_http_timeout"},
            "okHttpJvmProfile":{"outcome":"okhttp_jvm_timeout"},
            "residentialExitNodeProfile":{
                "directHttpProfile":{"outcome":"direct_http_timeout"},
                "okHttpJvmProfile":{"outcome":"okhttp_jvm_timeout"},
            },
        },
    ]
}
status={"environmentQueue":["waf-only","still-blocked"]}
assert mod.select(report,status)==["waf-only","yflix"],mod.select(report,status)

# Residential/native reachability that was already present on GitHub is not a
# differential and must not trigger a redundant full provider replay.
assert "already-github" not in mod.select(report,status)
print("residential full-provider replay selection contract passed")
