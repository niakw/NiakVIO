#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_provider_routes_from_upstreams as recovery  # noqa: E402
import materialize_provider_v3_all as materializer  # noqa: E402


def record(
    *,
    origin: str,
    route: str,
    role: str,
    media: str,
    index: int,
    streams: int = 1,
    last: int = 3,
    spec: dict | None = None,
) -> dict:
    return {
        "origin": origin,
        "route": route,
        "role": role,
        "semanticType": media,
        "fixture": f"fixture-{media}",
        "requestIndex": index,
        "taskLastRequestIndex": last,
        "taskStreamCount": streams,
        "taskRawStreamCount": streams,
        "requestSpecReusable": True,
        "requestSpec": spec or {"method": "GET"},
        "providerValueCorrelation": False,
        "proofModelVersion": 5,
    }


# FrenchStream-shaped partial recipe: movie has a representable terminal route,
# while the positive TV lane continues through a family-specific dataflow. The
# recipe must remain a fast movie path but fail open to Source Plan for TV.
base = "https://french-stream.one"
rows = [
    record(
        origin=base,
        route="/index.php",
        role="search",
        media="movie",
        index=0,
        last=2,
        spec={
            "method": "POST",
            "bodyKind": "form",
            "body": {"do": "search", "subaction": "search", "story": "{query}"},
        },
    ),
    record(origin=base, route="/engine/ajax/film_api.php?id={id}", role="api", media="movie", index=2, last=2),
    record(
        origin=base,
        route="/index.php",
        role="search",
        media="tv",
        index=0,
        last=4,
        spec={
            "method": "POST",
            "bodyKind": "form",
            "body": {"do": "search", "subaction": "search", "story": "{query}"},
        },
    ),
    # Positive TV evidence is intentionally not representable as episodeRoute.
    record(origin=base, route="/index.php?newsid={id}", role="detail", media="tv", index=2, last=4),
]
recipe = recovery.build_simple_api_recipe(rows)
assert isinstance(recipe, dict), recipe
assert recipe.get("movieRoute") == "/engine/ajax/film_api.php?id={id}", recipe
assert recipe.get("allowGenericFallback") is True, recipe
assert "tv" in (recipe.get("partialCoverageFallback") or []), recipe


# Proof-owned search authority must use live provider origins, exclude metadata
# helpers, and honor already-promoted runtime domain replacements.
proof_rows = [
    record(
        origin="https://new5.movies4u.clinic",
        route="/?s={query}",
        role="search",
        media="movie",
        index=0,
        last=8,
    ),
    record(
        origin="https://arm.haglund.dev",
        route="/api/v2/themoviedb?id={tmdbId}",
        role="search",
        media="movie",
        index=0,
        last=8,
    ),
]
bases = recovery._positive_proof_search_bases(proof_rows, {})
assert bases == ["https://new5.movies4u.clinic"], bases

rewritten = recovery._positive_proof_search_bases(
    [record(origin=base, route="/index.php", role="search", media="movie", index=0, last=2)],
    {"runtime_domain_replacements": {"french-stream.one": "fs23.lol"}},
)
assert rewritten == ["https://fs23.lol"], rewritten


# Explicit runtime replacements are executable DATA and are merged with existing
# domain substitutions; historical generic replacement maps are deliberately not.
substitutions = materializer._runtime_domain_substitutions({
    "domain_substitutions": {"old.example": "current.example"},
    "runtime_domain_replacements": {
        "https://french-stream.one": "https://fs23.lol",
        "new2.movies4u.tube": "new5.movies4u.clinic",
    },
    "replacements": {"candidate-only.example": "must-not-promote.example"},
})
assert substitutions["old.example"] == "current.example", substitutions
assert substitutions["french-stream.one"] == "fs23.lol", substitutions
assert substitutions["new2.movies4u.tube"] == "new5.movies4u.clinic", substitutions
assert "candidate-only.example" not in substitutions, substitutions


base_text = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
for marker in (
    "NIAKVIO_PROVIDER_SOURCE_PLAN_V10",
    "NIAKVIO_PROVIDER_MODEL.proofSearchBases",
    "_spv10SeasonUrlScore",
    "_substituteDomain(spec.headers[key])",
    "]).map(_substituteDomain).filter",
    "signin|signup|collapse",
):
    assert marker in base_text, marker

print("provider source plan v10 regression passed")
