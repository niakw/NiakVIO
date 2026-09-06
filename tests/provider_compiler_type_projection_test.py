#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_compiler import provider_contract  # noqa: E402


# Transport aliases exposed to Nuvio clients must never become semantic
# ProviderBase capabilities. canonicalSupportedTypes is authoritative whenever
# it is present.
row = {
    "id": "anime-semantic",
    "name": "Anime Semantic",
    "supportedTypes": ["anime", "tv", "series"],
    "canonicalSupportedTypes": ["anime"],
}
contract = provider_contract("anime-semantic", row, {}, {})
assert contract["supported_types"] == ["anime"], contract

row_movie_anime = {
    "id": "anime-movie",
    "name": "Anime Movie",
    "supportedTypes": ["movie", "anime", "tv", "series"],
    "canonicalSupportedTypes": ["movie", "anime"],
}
contract = provider_contract("anime-movie", row_movie_anime, {}, {})
assert contract["supported_types"] == ["movie", "anime"], contract

row_tv = {
    "id": "ordinary-tv",
    "name": "Ordinary TV",
    "supportedTypes": ["movie", "tv", "series"],
    "canonicalSupportedTypes": ["movie", "tv"],
}
contract = provider_contract("ordinary-tv", row_tv, {}, {})
assert contract["supported_types"] == ["movie", "tv"], contract

# Legacy rows without canonicalSupportedTypes retain their historical semantic
# interpretation; `series` is intentionally not a semantic ProviderBase type.
legacy = {
    "id": "legacy",
    "name": "Legacy",
    "supportedTypes": ["movie", "tv", "series"],
}
contract = provider_contract("legacy", legacy, {}, {})
assert contract["supported_types"] == ["movie", "tv"], contract

print("provider compiler semantic/transport type projection tests passed")
