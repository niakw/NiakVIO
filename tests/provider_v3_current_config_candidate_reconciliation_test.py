#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile_provider_v3_current_config_candidates import reconcile  # noqa: E402


def provider_js(model: dict) -> str:
    return (
        "const NIAKVIO_PROVIDER_MODEL = Object.freeze("
        + json.dumps(model, separators=(",", ":"))
        + ");\n"
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "providers").mkdir()
        manifest = {
            "scrapers": [
                {"id": "A", "filename": "providers/a.js"},
                {"id": "B", "filename": "providers/b.js"},
            ]
        }
        (root / "providers/a.js").write_text(
            provider_js({
                "providerId": "a",
                "knownSite": "https://old.example",
                "officialSite": "https://old.example",
                "routes": ["/embedded-stale/{id}"],
                "apiRecipe": {"searchRoute": "/embedded-search/{query}"},
            }),
            encoding="utf-8",
        )
        (root / "providers/b.js").write_text(
            provider_js({
                "providerId": "b",
                "knownSite": "https://embedded-b.example",
                "officialSite": "https://embedded-b.example",
                "routes": ["/embedded-current/{slug}"],
                "apiRecipe": None,
            }),
            encoding="utf-8",
        )

        knowledge = {
            "providers": {
                "a": {
                    "model": {
                        "routes": ["/old-model"],
                        "candidateRoutes": ["/dead-candidate", "/live-old/{id}"],
                        "candidateRouteData": [
                            {"route": "/dead-candidate", "validationState": "failed-live"},
                            {
                                "route": "/live-old/{id}",
                                "validationState": "live-validated",
                                "reusable": True,
                                "executedEvidence": True,
                                "httpUsed": True,
                            },
                        ],
                    }
                },
                "b": {
                    "model": {
                        "candidateRoutes": ["/obsolete"],
                        "candidateRouteData": [
                            {"route": "/obsolete", "validationState": "candidate-not-executed"}
                        ],
                    }
                },
            }
        }
        overrides = {
            "provider_patches": {
                "a": {
                    "official_site": "https://override-a.example",
                    "learned_routes": ["/override-search/{query}"],
                    "api_recipe": {
                        "searchRoute": "/override-search/{query}",
                        "movieRoute": "/stream/{id}",
                    },
                    "runtime_domain_replacements": {"old.example": "override-a.example"},
                },
                "b": {},
            }
        }
        recognition_seeds = {
            "schemaVersion": 1,
            "providerJavaScriptExecuted": False,
            "providers": {
                "a": {
                    "knownSite": "https://seed-a.example",
                    "routes": ["/seed-a-should-lose/{query}"],
                    "requests": [
                        {
                            "route": "/seed-a-should-lose/{query}",
                            "role": "search",
                            "method": "GET",
                            "executedEvidence": True,
                            "evidence": "niakvio-static-contract",
                        }
                    ],
                },
                "b": {
                    "knownSite": "https://seed-b.example",
                    "officialSite": "https://seed-b.example",
                    "origins": ["https://seed-b.example"],
                    "routes": ["/?s={query}"],
                    "requests": [
                        {
                            "route": "/?s={query}",
                            "role": "search",
                            "method": "POST",
                            "bodyFields": ["q"],
                            "formEncoded": False,
                            "jsonEncoded": True,
                            "refererRequired": True,
                            "originRequired": False,
                            "response": "json",
                            "executedEvidence": True,
                            "evidence": "niakvio-static-contract",
                            "confidence": 1.0,
                        }
                    ],
                },
            },
        }

        stats = reconcile(root, manifest, knowledge, overrides, recognition_seeds)
        a = knowledge["providers"]["a"]["model"]
        b = knowledge["providers"]["b"]["model"]
        patch_a = overrides["provider_patches"]["a"]
        patch_b = overrides["provider_patches"]["b"]

        # Explicit override wins over both seed and embedded Provider JS.
        assert a["knownSite"] == "https://override-a.example", a
        assert a["officialSite"] == "https://override-a.example", a
        assert a["domainSubstitutions"]["old.example"] == "override-a.example", a
        assert "/dead-candidate" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/embedded-stale/{id}" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/embedded-search/{query}" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/seed-a-should-lose/{query}" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/override-search/{query}" in a["candidateRoutes"], a["candidateRoutes"]
        assert "/stream/{id}" in a["candidateRoutes"], a["candidateRoutes"]
        assert "/live-old/{id}" in a["candidateRoutes"], a["candidateRoutes"]
        live = next(row for row in a["candidateRouteData"] if row["route"] == "/live-old/{id}")
        assert live["preservedByLiveValidation"] is True, live
        assert a["candidateApiRecipe"]["movieRoute"] == "/stream/{id}", a
        assert patch_a["candidate_learned_routes"] == ["/override-search/{query}", "/live-old/{id}"], patch_a
        assert patch_a["candidate_api_recipe"]["searchRoute"] == "/override-search/{query}", patch_a
        assert a["candidateReconciliation"]["routePlanSource"] == "provider-overrides", a

        # Recognition seed wins over stale embedded JS when there is no explicit override.
        assert b["knownSite"] == "https://seed-b.example", b
        assert b["officialSite"] == "https://seed-b.example", b
        assert b["origins"] == ["https://seed-b.example"], b
        assert b["candidateRoutes"] == ["/?s={query}"], b["candidateRoutes"]
        seed_row = b["candidateRouteData"][0]
        assert seed_row["candidateCurrentConfig"] is True, seed_row
        assert seed_row["candidateConfigSource"] == "provider-v3-recognition-seeds", seed_row
        assert seed_row["method"] == "POST", seed_row
        assert seed_row["jsonEncoded"] is True, seed_row
        assert seed_row["refererRequired"] is True, seed_row
        assert seed_row["recognitionSeedExecutedEvidence"] is True, seed_row
        # Static seed evidence must never be upgraded to actual live HTTP proof.
        assert seed_row["executedEvidence"] is False, seed_row
        assert seed_row["httpUsed"] is False, seed_row
        assert seed_row.get("validationState") != "live-validated", seed_row
        assert "/embedded-current/{slug}" not in b["candidateRoutes"], b["candidateRoutes"]
        assert "/obsolete" not in b["candidateRoutes"], b["candidateRoutes"]
        assert patch_b["candidate_learned_routes"] == ["/?s={query}"], patch_b
        assert b["candidateReconciliation"]["recognitionSeedPresent"] is True, b
        assert b["candidateReconciliation"]["recognitionSeedIsHttpProof"] is False, b

        assert stats["providersReconciled"] == 2, stats
        assert stats["recognitionSeedsUsed"] == 2, stats
        assert stats["recognitionSeedRoutes"] == 2, stats
        assert stats["recognitionSeedRequests"] == 2, stats
        assert stats["staleCandidatesSuppressed"] >= 2, stats
        assert stats["liveValidatedRoutesPreserved"] == 1, stats
        assert stats["recipesReconciled"] == 1, stats

    print("provider current config candidate reconciliation tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
