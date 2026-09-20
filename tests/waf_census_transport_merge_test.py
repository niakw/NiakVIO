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

print("WAF census transport-only merge contract passed")
