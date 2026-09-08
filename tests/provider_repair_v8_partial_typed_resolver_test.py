#!/usr/bin/env python3
"""Regression: a positive typed TV lane must not be blocked by a zero movie lane."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_provider_routes_from_upstreams as recovery  # noqa: E402
import materialize_provider_v3_all as materialize  # noqa: E402


def record(*, semantic: str, route: str, streams: int, index: int = 0, last: int = 0) -> dict:
    return {
        "route": route,
        "origin": "https://resolver.example",
        "role": "player",
        "method": "GET",
        "semanticType": semantic,
        "fixture": f"fixture-{semantic}",
        "requestIndex": index,
        "providerValueCorrelation": False,
        "requestSpec": {"method": "GET", "headers": {"referer": "https://resolver.example/"}},
        "requestSpecReusable": True,
        "status": 200,
        "contentType": "application/json",
        "proofModelVersion": 5,
        "taskStreamCount": streams,
        "taskRawStreamCount": streams,
        "taskLastRequestIndex": last,
    }


def main() -> int:
    recipe = recovery.build_simple_api_recipe([
        record(semantic="movie", route="/api/embed-tmdb/{tmdbId}", streams=0),
        record(
            semantic="tv",
            route="/api/embed-tmdb/{tmdbId}?type=tv&s={season}&e={episode}",
            streams=4,
        ),
    ])
    assert isinstance(recipe, dict), recipe
    assert "movieRoute" not in recipe, recipe
    assert recipe.get("episodeRoute") == "https://resolver.example/api/embed-tmdb/{tmdbId}?type=tv&s={season}&e={episode}", recipe
    assert recipe.get("recipeKind") == "typed-resolver-api", recipe

    patch = {
        "capability": "quarantined",
        "official_site": "https://resolver.example",
        "learned_routes": ["/search.php?s={query}"],
        "route_proof_version": 5,
    }
    capability = {"strategy": "mixed_embed_resolver"}
    static_row = {
        "model": {
            "routeProofVersion": 5,
            "routes": ["/search.php?s={query}"],
            "apiRecipe": recipe,
            "sourceRuntimeFamily": "catalogue-html-embed",
        }
    }
    model = materialize.provider_model("synthetic", patch, capability, static_row)
    identity = model.get("identityInput") or {}
    assert identity.get("mode") == "tmdb_direct", model
    assert identity.get("requiresTmdbBeforeRun") is False, model
    assert identity.get("requiredFields") == ["tmdbId", "mediaType"], model

    print("provider repair v8 partial typed resolver regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
