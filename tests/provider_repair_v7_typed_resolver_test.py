#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_provider_routes_from_upstreams as recovery  # noqa: E402


def row(*, route: str, origin: str, role: str, semantic: str, index: int,
        streams: int = 3, last: int = 0, correlated: bool = False) -> dict:
    return {
        "route": route,
        "origin": origin,
        "role": role,
        "semanticType": semantic,
        "requestIndex": index,
        "providerValueCorrelation": correlated,
        "requestSpecReusable": True,
        "requestSpec": {"method": "GET", "headers": {"origin": "https://player.example"}},
        "taskStreamCount": streams,
        "taskRawStreamCount": streams,
        "taskLastRequestIndex": last,
    }


# PlayIMDb-shaped proof: TMDB goes straight into a terminal typed resolver API.
playimdb = recovery.build_simple_api_recipe([
    row(
        route="/api.php?tmdb={tmdbId}&type=movie",
        origin="https://streamdata.vaplayer.ru",
        role="api",
        semantic="movie",
        index=0,
    ),
    row(
        route="/api.php?tmdb={tmdbId}&type=tv&season={season}&episode={episode}",
        origin="https://streamdata.vaplayer.ru",
        role="api",
        semantic="tv",
        index=0,
    ),
])
assert playimdb is not None, playimdb
assert playimdb.get("recipeKind") == "typed-resolver-api", playimdb
assert "directRoute" not in playimdb, playimdb


# A route whose identity/value came from an earlier provider response is a
# multi-hop chain even when it happens to contain TMDB. It must not get the
# direct typed-resolver bypass.
correlated = recovery.build_simple_api_recipe([
    row(
        route="/resolver?tmdb={tmdbId}&id={id}",
        origin="https://resolver.example",
        role="api",
        semantic="movie",
        index=2,
        last=2,
        correlated=True,
    ),
])
assert correlated is not None, correlated
assert correlated.get("recipeKind") != "typed-resolver-api", correlated

print("provider repair v7 typed resolver classification passed")
