#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_compiler import provider_contract  # noqa: E402
from apply_provider_overrides import _tmdb_preflight_required  # noqa: E402


row = {
    "id": "anime-semantic",
    "name": "Anime Semantic",
    "supportedTypes": ["anime", "movie", "tv"],
    "canonicalSupportedTypes": ["anime"],
}
contract = provider_contract("anime-semantic", row, {}, {})
assert contract["supported_types"] == ["anime"], contract

row_movie_anime = {
    "id": "anime-movie",
    "name": "Anime Movie",
    "supportedTypes": ["movie", "anime", "tv"],
    "canonicalSupportedTypes": ["movie", "anime"],
}
contract = provider_contract("anime-movie", row_movie_anime, {}, {})
assert contract["supported_types"] == ["movie", "anime"], contract

legacy = {"id": "legacy", "name": "Legacy", "supportedTypes": ["movie", "tv"]}
contract = provider_contract("legacy", legacy, {}, {})
assert contract["supported_types"] == ["movie", "tv"], contract

catalogue_config = {
    "catalogue_resolution_policy": {
        "enabled": True,
        "capabilities": ["html_scraper", "mixed_embed_resolver"],
    }
}
assert _tmdb_preflight_required(
    "anime-semantic",
    {"published_types": ["anime"]},
    {"strategy": "api_stream_resolver"},
    catalogue_config,
) is True
assert _tmdb_preflight_required(
    "ordinary-id",
    {"published_types": ["movie", "tv"]},
    {"strategy": "api_stream_resolver"},
    catalogue_config,
) is False
assert _tmdb_preflight_required(
    "title-recovery",
    {
        "published_types": ["movie", "tv"],
        "capability": "html_scraper",
        "official_site": "https://example.test",
    },
    {},
    catalogue_config,
) is True

print("provider compiler semantic/transport type projection tests passed")
