#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "merge_waf_census_transport.py"
spec = importlib.util.spec_from_file_location("merge_waf_census_transport", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

baseline = {
    "schemaVersion": 2,
    "runId": "repair-authority",
    "triggerSha": "repair-sha",
    "providers": [
        {
            "provider": "green",
            "status": "FULL OK",
            "color": "🟢",
            "currentVerifiedLanes": ["movie"],
            "repairEligible": False,
            "testedThisRun": True,
        },
        {
            "provider": "browser-only",
            "status": "HARNESS/ENV BLOCKED",
            "color": "🟫",
            "dominantIssue": "provider_waf_challenge",
            "repairEligible": False,
            "testedThisRun": False,
        },
        {
            "provider": "all-blocked",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "dominantIssue": "provider_waf_challenge",
            "repairEligible": False,
            "testedThisRun": False,
        },
        {
            "provider": "repairable",
            "status": "ROUTE PROVEN",
            "color": "🟪",
            "repairEligible": True,
            "testedThisRun": True,
        },
    ],
    "counts": {
        "FULL OK": 1,
        "HARNESS MISMATCH": 1,
        "HARNESS/ENV BLOCKED": 1,
        "ROUTE PROVEN": 1,
    },
    "symptomaticProviders": ["all-blocked", "browser-only", "repairable"],
    "brainQueue": ["all-blocked", "browser-only", "repairable"],
    "repairQueue": ["repairable"],
    "environmentQueue": ["all-blocked", "browser-only"],
    "harnessQueue": ["all-blocked", "browser-only"],
}
original = copy.deepcopy(baseline)

waf = {
    "rows": [
        {
            "provider": "browser-only",
            "lane": "movie",
            "outcome": "browser_challenge_persisted",
            "clientProfileMatrix": [
                {
                    "profile": "nuvio-tv-ua-browser",
                    "outcome": "browser_content_reached",
                }
            ],
            "directHttpProfile": {"outcome": "direct_http_challenge_persisted"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_challenge_persisted"},
        },
        {
            "provider": "all-blocked",
            "lane": "movie",
            "outcome": "browser_challenge_persisted",
            "clientProfileMatrix": [
                {
                    "profile": "nuvio-tv-ua-browser",
                    "outcome": "browser_challenge_persisted",
                }
            ],
            "directHttpProfile": {"outcome": "direct_http_challenge_persisted"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_challenge_persisted"},
        },
        # A transport probe result may never rewrite unrelated provider evidence.
        {
            "provider": "green",
            "lane": "movie",
            "outcome": "browser_challenge_persisted",
            "clientProfileMatrix": [],
            "directHttpProfile": {"outcome": "direct_http_challenge_persisted"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_challenge_persisted"},
        },
    ]
}

merged = mod.merge_transport(
    baseline,
    waf,
    evidence_run_id="waf-run",
    evidence_sha="waf-sha",
)

by_id = {row["provider"]: row for row in merged["providers"]}
assert by_id["green"] == original["providers"][0], by_id["green"]
assert by_id["repairable"] == original["providers"][3], by_id["repairable"]

assert by_id["browser-only"]["status"] == "HARNESS MISMATCH", by_id["browser-only"]
assert by_id["browser-only"]["harnessTransportClass"] == "browser-profile-only"
assert by_id["browser-only"]["repairEligible"] is False

assert by_id["all-blocked"]["status"] == "HARNESS/ENV BLOCKED", by_id["all-blocked"]
assert by_id["all-blocked"]["harnessTransportClass"] == "github-all-transports-challenged"
assert by_id["all-blocked"]["repairEligible"] is False

for key in (
    "repairQueue",
    "environmentQueue",
    "harnessQueue",
    "symptomaticProviders",
    "brainQueue",
):
    assert merged[key] == original[key], (key, merged[key], original[key])

assert merged["counts"] == {
    "FULL OK": 1,
    "HARNESS MISMATCH": 1,
    "HARNESS/ENV BLOCKED": 1,
    "ROUTE PROVEN": 1,
}, merged["counts"]
assert merged["runId"] == "repair-authority"
assert merged["triggerSha"] == "repair-sha"
assert merged["harnessEvidenceRunId"] == "waf-run"
assert merged["harnessEvidenceSha"] == "waf-sha"
assert merged["harnessTransportUpdatedProviders"] == ["all-blocked", "browser-only"]



network_baseline = {
    "runId": "repair-authority",
    "triggerSha": "repair-sha",
    "repairQueue": ["net"],
    "environmentQueue": [],
    "harnessQueue": [],
    "symptomaticProviders": ["net"],
    "brainQueue": ["net"],
    "providers": [{
        "provider": "net",
        "status": "PROVIDER NETWORK BLOCKED",
        "color": "🟤",
        "repairEligible": True,
        "brainCheckRequired": True,
    }],
}
network_waf = {
    "rows": [{
        "provider": "net",
        "lane": "movie",
        "seedKind": "network-failure-replay",
        "outcome": "browser_timeout",
        "directHttpProfile": {"outcome": "direct_http_timeout"},
        "okHttpJvmProfile": {"outcome": "okhttp_jvm_timeout"},
        "residentialExitNodeProfile": {
            "outcome": "browser_content_reached",
            "directHttpProfile": {"outcome": "direct_http_content_reached"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_content_reached"},
        },
    }],
}
network_merged = mod.merge_transport(network_baseline, network_waf)
net = network_merged["providers"][0]
assert net["status"] == "PROVIDER NETWORK BLOCKED", net
assert net["repairEligible"] is True, net
assert net["networkDifferentialClass"] == "residential-native-route-reachable", net
assert network_merged["repairQueue"] == ["net"], network_merged
assert network_merged["environmentQueue"] == [], network_merged
assert network_merged["networkDifferentialUpdatedProviders"] == ["net"], network_merged



# A full residential provider replay is stronger than the narrow transport
# overlay, but only strict current playable + identity-safe proof may promote.
functional_baseline = {
    "runId": "repair-authority",
    "triggerSha": "repair-sha",
    "repairQueue": ["net-ok"],
    "environmentQueue": ["harness-ok", "partial", "unsafe"],
    "harnessQueue": ["harness-ok", "partial", "unsafe"],
    "symptomaticProviders": ["net-ok", "harness-ok", "partial", "unsafe"],
    "brainQueue": ["net-ok", "harness-ok", "partial", "unsafe"],
    "providers": [
        {
            "provider": "net-ok",
            "status": "PROVIDER NETWORK BLOCKED",
            "color": "🟤",
            "declaredLanes": ["movie"],
            "currentVerifiedLanes": [],
            "repairEligible": True,
            "brainCheckRequired": True,
        },
        {
            "provider": "harness-ok",
            "status": "HARNESS/ENV BLOCKED",
            "color": "🟫",
            "declaredLanes": ["anime"],
            "currentVerifiedLanes": [],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
        {
            "provider": "partial",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["movie", "tv"],
            "currentVerifiedLanes": [],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
        {
            "provider": "unsafe",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["tv"],
            "currentVerifiedLanes": [],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
    ],
}
functional_waf = {
    "rows": [],
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {"provider": "net-ok", "lane": "movie", "raw": 2, "playable": 1, "verified": 1, "contradictions": 0, "identitySafe": True},
            {"provider": "harness-ok", "lane": "anime", "raw": 1, "playable": 1, "verified": 1, "contradictions": 0, "identitySafe": True},
            {"provider": "partial", "lane": "movie", "raw": 1, "playable": 1, "verified": 1, "contradictions": 0, "identitySafe": True},
            {"provider": "partial", "lane": "tv", "raw": 0, "playable": 0, "verified": 0, "contradictions": 0, "identitySafe": False},
            {"provider": "unsafe", "lane": "tv", "raw": 1, "playable": 1, "verified": 1, "contradictions": 0, "identitySafe": False},
        ],
    },
}
functional = mod.merge_transport(functional_baseline, functional_waf)
functional_by_id = {row["provider"]: row for row in functional["providers"]}

assert functional_by_id["net-ok"]["status"] == "FULL OK", functional_by_id["net-ok"]
assert functional_by_id["harness-ok"]["status"] == "FULL OK", functional_by_id["harness-ok"]
assert functional_by_id["partial"]["status"] == "PARTIAL OK", functional_by_id["partial"]
assert functional_by_id["unsafe"]["status"] == "HARNESS MISMATCH", functional_by_id["unsafe"]
assert functional_by_id["unsafe"]["residentialProviderReplayClass"] == "playable-unverified"

for provider in ("net-ok", "harness-ok", "partial"):
    row = functional_by_id[provider]
    assert row["residentialProviderReplayPromoted"] is True, row
    assert row["repairEligible"] is False, row
    assert row["brainCheckRequired"] is False, row
    assert row["testedThisRun"] is True, row

assert functional_by_id["net-ok"]["currentVerifiedLanes"] == ["movie"]
assert functional_by_id["harness-ok"]["currentVerifiedLanes"] == ["anime"]
assert functional_by_id["partial"]["currentVerifiedLanes"] == ["movie"]
assert functional["residentialProviderReplayPromotedProviders"] == ["harness-ok", "net-ok", "partial"]
assert functional["repairQueue"] == []
assert functional["environmentQueue"] == ["unsafe"]
assert functional["harnessQueue"] == ["unsafe"]
assert functional["symptomaticProviders"] == ["unsafe"]
assert functional["brainQueue"] == ["unsafe"]
assert functional["counts"] == {
    "FULL OK": 2,
    "HARNESS MISMATCH": 1,
    "PARTIAL OK": 1,
}, functional["counts"]

print("WAF census transport-only merge contract passed")
