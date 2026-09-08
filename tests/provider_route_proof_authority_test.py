#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_route_proof import (  # noqa: E402
    derive_task_routes,
    filter_recipe_by_live_routes,
    iter_recipe_routes,
)


def fixture() -> dict:
    return {
        "tmdbId": "94997",
        "mediaType": "tv",
        "title": "House of the Dragon",
        "season": 3,
        "episode": 1,
        "aliases": ["House of the Dragon"],
    }


# Search -> provider internal id -> episode route. The internal id becomes {id}
# only because the earlier provider response proves that exact value.
task = {
    "fixture": fixture(),
    "fetches": [
        {
            "url": "https://api.example.test/search-bar/search/House%20of%20the%20Dragon",
            "final_url": "https://api.example.test/search-bar/search/House%20of%20the%20Dragon",
            "method": "GET",
            "status": 200,
            "content_type": "application/json",
            "response_value_hints": [{"key": "id", "value": "525"}],
        },
        {
            "url": "https://api.example.test/stream/525/episode?season=3&episode=1",
            "final_url": "https://api.example.test/stream/525/episode?season=3&episode=1",
            "method": "GET",
            "status": 200,
            "content_type": "application/json",
        },
    ],
}
rows = derive_task_routes(task)
assert len(rows) == 2, rows
assert rows[1]["route"] == "/stream/{id}/episode?season={season}&episode={episode}", rows[1]
assert rows[1]["derivation"]["providerValueCorrelation"] is True, rows[1]
assert rows[1]["derivation"]["reusable"] is True, rows[1]

# The same literal internal id without prior response evidence must never be guessed.
unproven = copy.deepcopy(task)
unproven["fetches"] = [unproven["fetches"][1]]
unproven_row = derive_task_routes(unproven)[0]
assert unproven_row["route"] is None, unproven_row
assert "525" in unproven_row["derivation"]["unresolvedOpaqueSegments"], unproven_row

# TMDB/season/episode fixture values may be abstracted directly from the fixture.
direct_task = {
    "fixture": fixture(),
    "fetches": [{
        "url": "https://provider.example/api/tv/94997?season=3&episode=1",
        "final_url": "https://provider.example/api/tv/94997?season=3&episode=1",
        "method": "GET",
        "status": 200,
    }],
}
direct = derive_task_routes(direct_task)[0]
assert direct["route"] == "/api/tv/{tmdbId}?season={season}&episode={episode}", direct

# Candidate recipes may keep metadata, but only live-proven route fields become executable.
recipe = {
    "base": "https://api.example.test/api",
    "referer": "https://example.test/",
    "searchRoute": "/search/{query}",
    "movieRoute": "/stream/{id}",
    "episodeRoute": "/stream/{id}/episode?season={season}&episode={episode}",
    "requestTimeoutMs": 5000,
}
filtered = filter_recipe_by_live_routes(
    recipe,
    {"/search/{query}", "/stream/{id}/episode?season={season}&episode={episode}"},
)
assert filtered is not None
assert filtered["base"] == recipe["base"]
assert filtered["searchRoute"] == recipe["searchRoute"]
assert "movieRoute" not in filtered
assert filtered["episodeRoute"] == recipe["episodeRoute"]
assert set(iter_recipe_routes(filtered)) == {
    "/search/{query}",
    "/stream/{id}/episode?season={season}&episode={episode}",
}

print("provider route proof authority tests passed")
