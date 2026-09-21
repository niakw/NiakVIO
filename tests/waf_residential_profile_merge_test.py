#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

spec=importlib.util.spec_from_file_location("merge_residential", ROOT/"scripts/merge_waf_network_profiles.py")
assert spec and spec.loader
merge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)

spec2=importlib.util.spec_from_file_location("render_census", ROOT/"scripts/render_provider_census_status.py")
assert spec2 and spec2.loader
render=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(render)

baseline={
    "rows":[{
        "provider":"allwish",
        "lane":"movie",
        "outcome":"browser_challenge_persisted",
        "clientProfileMatrix":[
            {"profile":"github-default-browser","outcome":"browser_challenge_persisted"},
            {"profile":"nuvio-tv-ua-browser","outcome":"browser_challenge_persisted"},
        ],
        "directHttpProfile":{"profile":"nuvio-tv-direct-http-approx","outcome":"direct_http_challenge_persisted"},
        "okHttpJvmProfile":{"profile":"nuvio-tv-okhttp-jvm","outcome":"okhttp_jvm_challenge_persisted"},
    }]
}
residential={
    "rows":[{
        "provider":"allwish",
        "lane":"movie",
        "outcome":"browser_content_reached",
        "clientProfileMatrix":[
            {"profile":"github-default-browser","outcome":"browser_content_reached","attempts":[{"status":200}]},
            {"profile":"nuvio-tv-ua-browser","outcome":"browser_content_reached","attempts":[{"status":200}]},
        ],
        "directHttpProfile":{"profile":"nuvio-tv-direct-http-approx","outcome":"direct_http_content_reached","attempts":[{"status":200}]},
        "okHttpJvmProfile":{"profile":"nuvio-tv-okhttp-jvm","outcome":"okhttp_jvm_content_reached","attempts":[{"status":200}]},
        "privateExitNodeName":"must-never-survive",
        "publicIp":"203.0.113.123",
    }]
}
merged=merge.merge_profiles(baseline,residential)
row=merged["rows"][0]
profile=row["residentialExitNodeProfile"]
assert profile["profile"]=="tailscale-residential-exit",profile
assert profile["okHttpJvmProfile"]["outcome"]=="okhttp_jvm_content_reached",profile
serialized=repr(merged)
assert "must-never-survive" not in serialized
assert "203.0.113.123" not in serialized
privacy=merged["residentialExitNodeEvidence"]["privacy"]
assert privacy["exitNodeNamePersisted"] is False
assert privacy["residentialPublicIpPersisted"] is False

diag=render.harness_transport_diagnostic(merged,"allwish")
assert diag["classification"]=="residential-exit-native-reachable",diag
assert render.browser_harness_status(merged,"allwish")=="HARNESS MISMATCH"

blocked=merge.merge_profiles(
    baseline,
    {"rows":[{
        "provider":"allwish","lane":"movie","outcome":"browser_challenge_persisted",
        "clientProfileMatrix":[
            {"profile":"github-default-browser","outcome":"browser_challenge_persisted"},
            {"profile":"nuvio-tv-ua-browser","outcome":"browser_challenge_persisted"},
        ],
        "directHttpProfile":{"profile":"nuvio-tv-direct-http-approx","outcome":"direct_http_challenge_persisted"},
        "okHttpJvmProfile":{"profile":"nuvio-tv-okhttp-jvm","outcome":"okhttp_jvm_challenge_persisted"},
    }]}
)
diag2=render.harness_transport_diagnostic(blocked,"allwish")
assert diag2["classification"]=="residential-exit-all-challenged",diag2
assert render.browser_harness_status(blocked,"allwish")=="HARNESS/ENV BLOCKED"

fallback=merge.mark_residential_unavailable(baseline,reason="tailscale-connect-failed")
assert fallback["residentialExitNodeEvidence"]["available"] is False
assert fallback["residentialExitNodeEvidence"]["reason"]=="tailscale-connect-failed"
serialized_fallback=repr(fallback)
assert "203.0.113.123" not in serialized_fallback
assert render.harness_transport_diagnostic(fallback,"allwish")["classification"]=="github-all-transports-challenged"

print("WAF private residential exit evidence merge contract passed")
