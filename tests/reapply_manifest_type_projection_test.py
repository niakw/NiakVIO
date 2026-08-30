#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reapply_published_overrides import (  # noqa: E402
    apply_manifest_type_projection,
    manifest_type_projection_matches,
    projected_transport_types,
    semantic_manifest_types,
)


assert projected_transport_types(["anime"]) == ["anime", "movie", "tv"]
assert projected_transport_types(["movie", "anime"]) == ["movie", "anime", "tv"]
assert projected_transport_types(["tv", "anime"]) == ["tv", "anime", "movie"]
assert projected_transport_types(["movie", "tv"]) == ["movie", "tv"]

anime_only = {"supportedTypes": ["anime"]}
assert apply_manifest_type_projection(anime_only, ["anime"]) is True
assert anime_only == {
    "supportedTypes": ["anime", "movie", "tv"],
    "canonicalSupportedTypes": ["anime"],
}
assert semantic_manifest_types(anime_only) == ["anime"]
assert manifest_type_projection_matches(anime_only, ["anime"])
assert apply_manifest_type_projection(anime_only, ["anime"]) is False

anime_movie = {"supportedTypes": ["movie", "anime"]}
assert apply_manifest_type_projection(anime_movie, ["movie", "anime"]) is True
assert anime_movie == {
    "supportedTypes": ["movie", "anime", "tv"],
    "canonicalSupportedTypes": ["movie", "anime"],
}
assert manifest_type_projection_matches(anime_movie, ["movie", "anime"])

ordinary = {
    "supportedTypes": ["movie", "tv"],
    "canonicalSupportedTypes": ["movie", "tv"],
}
assert apply_manifest_type_projection(ordinary, ["movie", "tv"]) is True
assert ordinary == {"supportedTypes": ["movie", "tv"]}
assert manifest_type_projection_matches(ordinary, ["movie", "tv"])

stale_transport_only = {"supportedTypes": ["anime", "movie", "tv"]}
assert semantic_manifest_types(stale_transport_only) == ["anime", "movie", "tv"]
assert not manifest_type_projection_matches(stale_transport_only, ["anime"])
assert apply_manifest_type_projection(stale_transport_only, ["anime"]) is True
assert stale_transport_only["canonicalSupportedTypes"] == ["anime"]
assert manifest_type_projection_matches(stale_transport_only, ["anime"])

print("reapply manifest semantic/transport projection tests passed")
