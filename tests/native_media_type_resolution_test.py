#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "native_media_type_contract",
    ROOT / "scripts" / "native_media_type_contract.py",
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.canonical_media_type("series") == "tv"
assert mod.canonical_media_type("show") == "tv"
assert mod.canonical_media_type("other") == "tv"
assert mod.canonical_media_type("tv") == "tv"
assert mod.canonical_media_type("anime") == "anime"
assert mod.canonical_media_type("movie") == "movie"

# Naruto-like Nuvio input: generic series/tv surface, trusted TMDB metadata says
# Japanese animation -> canonical route must remain anime.
naruto_tmdb = {
    "id": 46260,
    "genres": [{"id": 16, "name": "Animation"}, {"id": 10759, "name": "Action & Adventure"}],
    "original_language": "ja",
    "origin_country": ["JP"],
}
assert mod.tmdb_metadata_indicates_anime(naruto_tmdb) is True
assert mod.canonical_media_type("series", metadata=naruto_tmdb) == "anime"
assert mod.canonical_media_type("tv", metadata=naruto_tmdb) == "anime"

# Animation by itself is not anime.
western_animation = {
    "genres": [{"id": 16, "name": "Animation"}],
    "original_language": "en",
    "origin_country": ["US"],
}
assert mod.tmdb_metadata_indicates_anime(western_animation) is False
assert mod.canonical_media_type("series", metadata=western_animation) == "tv"

# Explicit trusted category is sufficient even when Nuvio sent series.
assert mod.fixture_media_type({"mediaType": "series", "category": "anime"}) == "anime"
assert mod.fixture_media_type({"mediaType": "series", "category": "tv"}) == "tv"

# TMDB keyword is direct evidence.
assert mod.canonical_media_type(
    "tv",
    metadata={"keywords": {"results": [{"name": "anime"}]}},
) == "anime"

print("native media type contract passed: series=tv, trusted anime metadata=>anime")
