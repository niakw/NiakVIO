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
                "knownSite": "https://b.example",
                "officialSite": "https://b.example",
                "routes": ["/current/{slug}"],
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
                    "official_site": "https://new.example",
                    "learned_routes": ["/new-search/{query}"],
                    "api_recipe": {
                        "searchRoute": "/new-search/{query}",
                        "movieRoute": "/stream/{id}",
                    },
                    "runtime_domain_replacements": {"old.example": "new.example"},
                },
                "b": {},
            }
        }

        stats = reconcile(root, manifest, knowledge, overrides)
        a = knowledge["providers"]["a"]["model"]
        b = knowledge["providers"]["b"]["model"]
        patch_a = overrides["provider_patches"]["a"]

        assert a["knownSite"] == "https://new.example", a
        assert a["officialSite"] == "https://new.example", a
        assert a["domainSubstitutions"]["old.example"] == "new.example", a
        assert "/dead-candidate" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/embedded-stale/{id}" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/embedded-search/{query}" not in a["candidateRoutes"], a["candidateRoutes"]
        assert "/new-search/{query}" in a["candidateRoutes"], a["candidateRoutes"]
        assert "/stream/{id}" in a["candidateRoutes"], a["candidateRoutes"]
        assert "/live-old/{id}" in a["candidateRoutes"], a["candidateRoutes"]
        live = next(row for row in a["candidateRouteData"] if row["route"] == "/live-old/{id}")
        assert live["preservedByLiveValidation"] is True, live
        assert a["candidateApiRecipe"]["movieRoute"] == "/stream/{id}", a
        assert patch_a["candidate_learned_routes"] == ["/new-search/{query}", "/live-old/{id}"], patch_a
        assert patch_a["candidate_api_recipe"]["searchRoute"] == "/new-search/{query}", patch_a

        assert b["candidateRoutes"] == ["/current/{slug}"], b["candidateRoutes"]
        assert b["candidateRouteData"][0]["candidateCurrentConfig"] is True, b
        assert b["candidateRouteData"][0]["executedEvidence"] is False, b
        assert b["candidateRouteData"][0]["httpUsed"] is False, b
        assert b["candidateReconciliation"]["staleCandidateCountSuppressed"] == 1, b

        assert stats["providersReconciled"] == 2, stats
        assert stats["staleCandidatesSuppressed"] >= 2, stats
        assert stats["liveValidatedRoutesPreserved"] == 1, stats
        assert stats["recipesReconciled"] == 1, stats

    print("provider current config candidate reconciliation tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
