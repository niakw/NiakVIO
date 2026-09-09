#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_route_proof_lkg.py"

spec = importlib.util.spec_from_file_location("route_lkg", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load provider route proof LKG")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def source(sha: str) -> dict:
    return {
        "kind": "upstream",
        "sourceId": "neutral-source",
        "sha256": sha,
        "currentSha256": sha,
        "wantedSha256": sha,
        "providerUrl": "https://example.invalid/provider.js",
    }


def proof(route: str, index: int, *, sha: str, correlated: bool = False, streams: int = 1) -> dict:
    return {
        "route": route,
        "origin": "https://example.invalid",
        "role": "search" if index == 1 else "detail",
        "method": "GET",
        "semanticType": "tv",
        "fixture": "neutral-s01e01",
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
            ],
            "routes": ["/search", "/detail/{slug}", "/player?id={id}"],
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
assert "/player?id={id}" in entry["routes"], entry
assert stats["retainedRows"] == 1, stats

enriched, retained = module.augment_provider_row(current_report["providers"][0], entry)
assert retained == 1, enriched
assert "/player?id={id}" in enriched["routes"], enriched
assert enriched["routeCount"] == 3, enriched

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

merge_text = (ROOT / "scripts" / "merge_provider_repair_report_v6.py").read_text(encoding="utf-8")
assert "route_lkg.merge_report_into_registry" in merge_text
assert "route_lkg.augment_provider_row" in merge_text
assert "routeProofLkgRetainedRows" in merge_text

print("provider route proof LKG tests passed")
