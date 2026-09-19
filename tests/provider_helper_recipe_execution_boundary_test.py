#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_provider_v3_all import provider_model

helper_patch = {
    "official_site": "https://provider.example",
    "route_proof_version": 5,
    "learned_routes": ["/api/v2/themoviedb?id={tmdbId}", "/search?q={query}"],
    "api_recipe": {
        "proofModelVersion": 5,
        "allowGenericFallback": False,
        "base": "https://arm.haglund.dev",
        "directRoute": "/api/v2/themoviedb?id={tmdbId}",
    },
}
model = provider_model("demo", helper_patch, {"capability": "mixed_embed_resolver"}, {"model": {}})
assert model["apiRecipe"] is None, model["apiRecipe"]
assert "/api/v2/themoviedb?id={tmdbId}" not in model["routes"], model["routes"]
assert "/search?q={query}" in model["routes"], model["routes"]

normal_patch = {
    "official_site": "https://provider.example",
    "route_proof_version": 5,
    "learned_routes": ["/stream/{tmdbId}"],
    "api_recipe": {
        "proofModelVersion": 5,
        "allowGenericFallback": False,
        "base": "https://api.provider.example",
        "directRoute": "/stream/{tmdbId}",
    },
}
normal = provider_model("demo", normal_patch, {"capability": "api_stream_resolver"}, {"model": {}})
assert normal["apiRecipe"]["base"] == "https://api.provider.example"
assert normal["routes"] == ["/stream/{tmdbId}"]

print("provider helper apiRecipe execution boundary passed")
