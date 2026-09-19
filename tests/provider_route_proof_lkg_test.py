#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "provider_route_proof_lkg.py"
MERGE_SCRIPT = ROOT / "scripts" / "merge_provider_repair_report_v6.py"

spec = importlib.util.spec_from_file_location("route_lkg", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load provider route proof LKG")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

merge_spec = importlib.util.spec_from_file_location("route_merge", MERGE_SCRIPT)
if merge_spec is None or merge_spec.loader is None:
    raise SystemExit("unable to load provider route proof merge")
merge_module = importlib.util.module_from_spec(merge_spec)
merge_spec.loader.exec_module(merge_module)


def source(sha: str) -> dict:
    return {
        "kind": "upstream",
        "sourceId": "neutral-source",
        "sha256": sha,
        "currentSha256": sha,
        "wantedSha256": sha,
        "providerUrl": "https://example.invalid/provider.js",
    }


def proof(route: str, index: int, *, sha: str, semantic: str = "tv", correlated: bool = False, streams: int = 1) -> dict:
    return {
        "route": route,
        "origin": "https://example.invalid",
        "role": "search" if index == 1 else "detail",
        "method": "GET",
        "semanticType": semantic,
        "fixture": "neutral-s01e01" if semantic != "movie" else "neutral-movie",
        "requestIndex": index,
        "providerValueCorrelation": correlated,
        "externalIdentityCorrelation": False,
        "requestSpec": {"method": "GET"},
        "requestSpecReusable": True,
        "status": 200,
        "contentType": "text/html",
        "proofModelVersion": 5,
        "source": source(sha),
        "taskStreamCount": streams,
        "taskRawStreamCount": streams,
        "taskLastRequestIndex": 4,
    }


sha_a = "a" * 64
sha_b = "b" * 64
old_registry = {
    "schemaVersion": 1,
    "providers": {
        "neutral-provider": {
            "source": source(sha_a),
            "routeData": [
                proof("/search", 1, sha=sha_a),
                proof("/detail/{slug}", 2, sha=sha_a, correlated=True),
                proof("/player?id={id}", 3, sha=sha_a, correlated=True),
                proof("/movie/{id}", 1, sha=sha_a, semantic="movie", correlated=True),
            ],
            "routes": ["/search", "/detail/{slug}", "/player?id={id}", "/movie/{id}"],
        }
    },
}
current_report = {
    "providers": [{
        "providerId": "neutral-provider",
        "source": source(sha_a),
        "routeData": [
            proof("/search", 1, sha=sha_a),
            proof("/detail/{slug}", 2, sha=sha_a, correlated=True),
        ],
        "routes": ["/search", "/detail/{slug}"],
    }]
}

merged_registry, stats = module.merge_report_into_registry(old_registry, current_report)
entry = merged_registry["providers"]["neutral-provider"]
# Registry remains proof memory and keeps same-source historical evidence.
assert "/player?id={id}" in entry["routes"], entry
assert "/movie/{id}" in entry["routes"], entry
assert stats["retainedRows"] == 2, stats

# Active reconstruction is lane-aware: fresh-positive TV is authoritative, so
# its obsolete player row is not reintroduced; unproven movie may still use LKG.
enriched, retained = module.augment_provider_row(current_report["providers"][0], entry)
assert retained == 1, enriched
assert "/player?id={id}" not in enriched["routes"], enriched
assert "/movie/{id}" in enriched["routes"], enriched
assert enriched["routeCount"] == 3, enriched
assert enriched["routeProofFreshPositiveLanes"] == ["tv"], enriched

changed_report = copy.deepcopy(current_report)
changed_report["providers"][0]["source"] = source(sha_b)
changed_report["providers"][0]["routeData"] = [proof("/new-search", 1, sha=sha_b)]
changed_report["providers"][0]["routes"] = ["/new-search"]
reset_registry, reset_stats = module.merge_report_into_registry(merged_registry, changed_report)
assert reset_stats["sourceResets"] == 1, reset_stats
assert reset_registry["providers"]["neutral-provider"]["routes"] == ["/new-search"], reset_registry

non_positive = copy.deepcopy(current_report)
non_positive["providers"][0]["routeData"] = [proof("/not-positive", 1, sha=sha_a, streams=0)]
empty_registry, _ = module.merge_report_into_registry({"schemaVersion": 1, "providers": {}}, non_positive)
assert "neutral-provider" not in empty_registry["providers"], empty_registry

uncorrelated = copy.deepcopy(current_report)
uncorrelated["providers"][0]["routeData"] = [proof("/detail/{id}", 1, sha=sha_a, correlated=False)]
empty_registry, _ = module.merge_report_into_registry({"schemaVersion": 1, "providers": {}}, uncorrelated)
assert "neutral-provider" not in empty_registry["providers"], empty_registry

# Historical bootstrap is not general authority: it is visible only while the
# provider is targeted now with the exact same source identity.
seed = {
    "providers": [
        {"providerId": "neutral-provider", "source": source(sha_a), "routeData": [proof("/historical/{id}", 4, sha=sha_a, correlated=True)]},
        {"providerId": "other-provider", "source": source(sha_a), "routeData": [proof("/other/{id}", 4, sha=sha_a, correlated=True)]},
    ]
}
eligible = merge_module.eligible_bootstrap(seed, current_report)
assert [row["providerId"] for row in eligible["providers"]] == ["neutral-provider"], eligible
changed_target = copy.deepcopy(current_report)
changed_target["providers"][0]["source"] = source(sha_b)
assert merge_module.eligible_bootstrap(seed, changed_target)["providers"] == [], seed

merge_text = MERGE_SCRIPT.read_text(encoding="utf-8")
assert "route_lkg.merge_report_into_registry" in merge_text
assert "route_lkg.augment_provider_row" in merge_text
assert "def eligible_bootstrap" in merge_text
assert "routeProofBootstrapMatchedProviders" in merge_text
assert "routeProofLkgRetainedRows" in merge_text

print("provider route proof LKG tests passed: fresh-positive lanes override stale same-source execution rows")
