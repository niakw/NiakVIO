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
        "networkDifferentialClass": "stale-network-overlay",
        "networkDifferentialEvidence": ["stale"],
        "residentialProviderReplayClass": "verified",
        "residentialProviderReplayEvidence": ["stale"],
        "residentialProviderReplayPromoted": True,
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
assert net["networkDifferentialEvidence"] != ["stale"], net
assert "residentialProviderReplayClass" not in net, net
assert "residentialProviderReplayEvidence" not in net, net
assert "residentialProviderReplayPromoted" not in net, net
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

# Native-like reachability plus a full provider replay that fails after
# entering provider runtime is no longer environment-only. This does NOT grant
# a repair; it transfers the provider to the normal Brain queue.
post_harness_baseline = {
    "repairQueue": [],
    "authorityBlockedQueue": ["authority-blocked-runtime"],
    "environmentQueue": ["wooka-like", "browser-only-runtime", "timeout-runtime", "authority-blocked-runtime"],
    "harnessQueue": ["wooka-like", "browser-only-runtime", "timeout-runtime", "authority-blocked-runtime"],
    "symptomaticProviders": ["wooka-like", "browser-only-runtime", "timeout-runtime", "authority-blocked-runtime"],
    "brainQueue": ["wooka-like", "browser-only-runtime", "timeout-runtime", "authority-blocked-runtime"],
    "providers": [
        {
            "provider": "wooka-like",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["movie", "tv"],
            "currentVerifiedLanes": [],
            "routeProof": ["2 live routes / movie, tv"],
            "evidenceDepth": ["movie=lookup_only", "tv=chain_reached"],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
        {
            "provider": "browser-only-runtime",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["anime"],
            "currentVerifiedLanes": [],
            "evidenceDepth": ["anime=lookup_only"],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
        {
            "provider": "timeout-runtime",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["movie"],
            "currentVerifiedLanes": [],
            "evidenceDepth": ["movie=lookup_only"],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
        {
            "provider": "authority-blocked-runtime",
            "status": "HARNESS MISMATCH",
            "color": "🟧",
            "declaredLanes": ["movie"],
            "currentVerifiedLanes": [],
            "routeProof": ["1 live routes / movie"],
            "evidenceDepth": ["movie=lookup_only"],
            "authorityRepairEligible": False,
            "authorityAction": "REDISCOVER_SEARCH",
            "authorityClass": "unproven-direct-candidate",
            "authorityConfidence": "low",
            "authorityReasons": ["direct_candidate_unproven", "search_supplement_only"],
            "repairEligible": False,
            "brainCheckRequired": True,
        },
    ],
}
post_harness_waf = {
    "rows": [
        {
            "provider": "wooka-like",
            "lane": "movie",
            "outcome": "browser_content_reached",
            "directHttpProfile": {"outcome": "direct_http_content_reached"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_content_reached"},
        },
        {
            "provider": "wooka-like",
            "lane": "tv",
            "outcome": "browser_content_reached",
            "directHttpProfile": {"outcome": "direct_http_content_reached"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_content_reached"},
        },
        {
            "provider": "browser-only-runtime",
            "lane": "anime",
            "outcome": "browser_content_reached",
            "clientProfileMatrix": [{"profile": "nuvio-tv-ua-browser", "outcome": "browser_content_reached"}],
            "directHttpProfile": {"outcome": "direct_http_challenge_persisted"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_challenge_persisted"},
        },
        {
            "provider": "timeout-runtime",
            "lane": "movie",
            "outcome": "browser_content_reached",
            "directHttpProfile": {"outcome": "direct_http_content_reached"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_content_reached"},
        },
        {
            "provider": "authority-blocked-runtime",
            "lane": "movie",
            "outcome": "browser_content_reached",
            "directHttpProfile": {"outcome": "direct_http_content_reached"},
            "okHttpJvmProfile": {"outcome": "okhttp_jvm_content_reached"},
        },
    ],
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {"provider": "wooka-like", "lane": "movie", "status": "no_streams", "debugStage": "provider_network_exception", "raw": 0, "playable": 0, "verified": 0, "identitySafe": True},
            {"provider": "wooka-like", "lane": "tv", "status": "no_streams", "debugStage": "provider_network_exception", "raw": 0, "playable": 0, "verified": 0, "identitySafe": True},
            {"provider": "browser-only-runtime", "lane": "anime", "status": "no_streams", "debugStage": "provider_network_exception", "raw": 0, "playable": 0, "verified": 0, "identitySafe": True},
            {"provider": "timeout-runtime", "lane": "movie", "status": "timeout", "debugStage": "timeout", "raw": 0, "playable": 0, "verified": 0, "identitySafe": False},
            {"provider": "authority-blocked-runtime", "lane": "movie", "status": "no_streams", "debugStage": "provider_network_exception", "raw": 0, "playable": 0, "verified": 0, "identitySafe": True},
        ],
    },
}
post_harness = mod.merge_transport(post_harness_baseline, post_harness_waf)
post_by_id = {row["provider"]: row for row in post_harness["providers"]}
assert post_by_id["wooka-like"]["status"] == "PROVIDER NETWORK BLOCKED", post_by_id["wooka-like"]
assert post_by_id["wooka-like"]["repairEligible"] is True
assert post_by_id["wooka-like"]["residentialProviderReplayReclassified"] is True
assert "wooka-like" in post_harness["repairQueue"]
assert "wooka-like" not in post_harness["environmentQueue"]
assert "wooka-like" not in post_harness["harnessQueue"]
assert post_harness["residentialProviderReplayReclassifiedProviders"] == ["authority-blocked-runtime", "wooka-like"]
assert post_harness["residentialProviderReplayRepairableProviders"] == ["wooka-like"]
blocked = post_by_id["authority-blocked-runtime"]
assert blocked["status"] == "PROVIDER NETWORK BLOCKED", blocked
assert blocked["statusRepairEligible"] is True, blocked
assert blocked["authorityRepairEligible"] is False, blocked
assert blocked["repairEligible"] is False, blocked
assert blocked["authorityAction"] == "REDISCOVER_SEARCH", blocked
assert "rediscovery required before Repair" in blocked["action"], blocked
assert "authority-blocked-runtime" not in post_harness["repairQueue"], post_harness
assert "authority-blocked-runtime" not in post_harness["environmentQueue"], post_harness
assert "authority-blocked-runtime" not in post_harness["harnessQueue"], post_harness
assert "authority-blocked-runtime" in post_harness["brainQueue"], post_harness
assert post_harness["authorityBlockedQueue"] == ["authority-blocked-runtime"], post_harness
assert post_by_id["browser-only-runtime"]["status"] == "HARNESS MISMATCH"
assert post_by_id["browser-only-runtime"]["repairEligible"] is False
assert "browser-only-runtime" in post_harness["environmentQueue"]
assert post_by_id["timeout-runtime"]["status"] == "HARNESS MISMATCH"
assert post_by_id["timeout-runtime"]["repairEligible"] is False
assert "timeout-runtime" in post_harness["environmentQueue"]


# Canonical census ownership also strips WAF-only fields from a carried row.
# Otherwise a later census can correctly reclassify status while still showing
# a stale "residential replay verified" annotation from an older overlay.
canonical_carried = {
    "providers": [{
        "provider": "carried-overlay",
        "status": "FULL OK",
        "color": "🟢",
        "declaredLanes": ["movie"],
        "currentVerifiedLanes": ["movie"],
        "historicalProof": [],
        "candidateProof": [],
        "routeProof": [],
        "latestLaneVerdicts": ["movie=OK"],
        "dominantIssue": "none",
        "searchProgress": ["movie: retained"],
        "evidenceDepth": ["movie=none"],
        "harnessTransportClass": "not-applicable",
        "harnessTransportEvidence": [],
        "repairEligible": False,
        "brainCheckRequired": False,
        "testedThisRun": True,
        "residentialProviderReplayClass": "verified",
        "residentialProviderReplayEvidence": ["stale"],
        "residentialProviderReplayPromoted": True,
        "networkDifferentialClass": "stale",
        "networkDifferentialEvidence": ["stale"],
    }]
}
canonical_rows = mod.census.build_status_rows(
    {"provider_count": 0, "rows": []},
    {},
    canonical_carried,
    {},
    {},
    {},
    {},
)
canonical = canonical_rows[0]
for field in mod.census.TRANSPORT_OVERLAY_ROW_FIELDS:
    assert field not in canonical, (field, canonical)

print("WAF census transport-only merge contract passed")
