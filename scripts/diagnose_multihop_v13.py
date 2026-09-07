#!/usr/bin/env python3
"""Print bounded, non-secret diagnostics for current multi-hop route proof.

This script never promotes DATA. It only explains where proof information is lost
between routeData, generic executionRoutes, and the projected provider model.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "automation" / "v13-multihop-recovery.json"
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_request(spec):
    if not isinstance(spec, dict):
        return None
    return {
        "method": spec.get("method"),
        "bodyKind": spec.get("bodyKind"),
        "headerNames": sorted((spec.get("headers") or {}).keys()) if isinstance(spec.get("headers"), dict) else [],
    }


report = load(REPORT)
for provider in report.get("providers") or []:
    pid = provider.get("providerId")
    if pid not in {"movies4u", "papadustream", "animekai", "frenchstream"}:
        continue
    print("V13_PROVIDER", pid,
          "routes=" + json.dumps(provider.get("routes") or []),
          "executionRoutes=" + json.dumps(provider.get("executionRoutes") or []),
          "recipe=" + json.dumps(provider.get("apiRecipe"), sort_keys=True))
    for row in provider.get("routeData") or []:
        if not isinstance(row, dict):
            continue
        print("V13_ROUTE", pid,
              "media=" + str(row.get("semanticType")),
              "fixture=" + str(row.get("fixture")),
              "idx=" + str(row.get("requestIndex")),
              "last=" + str(row.get("taskLastRequestIndex")),
              "streams=" + str(row.get("taskStreamCount")),
              "origin=" + str(row.get("origin")),
              "role=" + str(row.get("role")),
              "route=" + str(row.get("route")),
              "reusable=" + str(row.get("requestSpecReusable")),
              "providerCorr=" + str(row.get("providerValueCorrelation")),
              "externalCorr=" + str(row.get("externalIdentityCorrelation")),
              "request=" + json.dumps(safe_request(row.get("requestSpec")), sort_keys=True))

overrides = load(OVERRIDES).get("provider_patches") or {}
knowledge = load(KNOWLEDGE).get("providers") or {}
for pid in ("movies4u", "papadustream", "animekai", "frenchstream"):
    patch = overrides.get(pid) if isinstance(overrides.get(pid), dict) else {}
    static = knowledge.get(pid) if isinstance(knowledge.get(pid), dict) else {}
    model = static.get("model") if isinstance(static.get("model"), dict) else {}
    print("V13_PROJECTED", pid,
          "learned=" + json.dumps(patch.get("learned_routes") or []),
          "proofSearchBases=" + json.dumps(patch.get("proof_search_bases") or model.get("proofSearchBases") or []),
          "proofDetailBases=" + json.dumps(patch.get("proof_detail_bases") or model.get("proofDetailBases") or []),
          "modelRoutes=" + json.dumps(model.get("routes") or []),
          "identity=" + json.dumps(model.get("identityInput") or {}, sort_keys=True),
          "family=" + str(model.get("sourceRuntimeFamily")))
