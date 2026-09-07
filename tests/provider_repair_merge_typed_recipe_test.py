#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from merge_provider_repair_report_v6 import normalize_typed_api_recipe  # noqa: E402


legacy = {
    "providerId": "synthetic",
    "apiRecipe": {
        "proofModelVersion": 5,
        "movieRoute": "https://api.example/item?tmdb={tmdbId}&type=movie",
        "movieRequest": {"method": "GET"},
        "episodeRoute": "https://api.example/item?tmdb={tmdbId}&type=tv&season={season}&episode={episode}",
        "episodeRequest": {"method": "GET"},
        "directRoute": "/item?tmdb={tmdbId}&type=movie",
        "directRequest": {"method": "GET"},
    },
}
original = copy.deepcopy(legacy)
normalized, changed = normalize_typed_api_recipe(legacy)
assert changed is True
assert legacy == original, "normalizer must not mutate baseline proof row"
assert normalized["apiRecipe"]["movieRoute"] == original["apiRecipe"]["movieRoute"]
assert normalized["apiRecipe"]["episodeRoute"] == original["apiRecipe"]["episodeRoute"]
assert "directRoute" not in normalized["apiRecipe"]
assert "directRequest" not in normalized["apiRecipe"]

# A one-lane recipe may still legitimately use a generic direct fallback. V6 only
# removes the generic route when both semantic lanes are explicitly represented.
partial = {
    "providerId": "partial",
    "apiRecipe": {
        "movieRoute": "/movie/{tmdbId}",
        "directRoute": "/resolve/{tmdbId}",
        "directRequest": {"method": "GET"},
    },
}
partial_out, partial_changed = normalize_typed_api_recipe(partial)
assert partial_changed is False
assert partial_out == partial

print("provider repair merged typed-recipe precedence regression passed")
