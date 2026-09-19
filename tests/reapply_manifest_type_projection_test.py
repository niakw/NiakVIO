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

assert projected_transport_types(["anime"]) == ["anime", "tv", "series"]
assert projected_transport_types(["movie", "anime"]) == ["movie", "anime", "tv", "series"]
assert projected_transport_types(["tv", "anime"]) == ["tv", "anime", "series"]
assert projected_transport_types(["movie", "tv"]) == ["movie", "tv", "series"]

anime_only = {"supportedTypes": ["anime"]}
assert apply_manifest_type_projection(anime_only, ["anime"]) is True
assert anime_only == {"supportedTypes": ["anime", "tv", "series"], "canonicalSupportedTypes": ["anime"]}
assert semantic_manifest_types(anime_only) == ["anime"]
assert manifest_type_projection_matches(anime_only, ["anime"])
assert apply_manifest_type_projection(anime_only, ["anime"]) is False

ordinary = {"supportedTypes": ["movie", "tv"]}
assert apply_manifest_type_projection(ordinary, ["movie", "tv"]) is True
assert ordinary == {"supportedTypes": ["movie", "tv", "series"], "canonicalSupportedTypes": ["movie", "tv"]}
assert semantic_manifest_types(ordinary) == ["movie", "tv"]
assert manifest_type_projection_matches(ordinary, ["movie", "tv"])
assert apply_manifest_type_projection(ordinary, ["movie", "tv"]) is False

stale_transport = {"supportedTypes": ["tv", "series"], "canonicalSupportedTypes": ["tv"]}
assert semantic_manifest_types(stale_transport) == ["tv"]
assert manifest_type_projection_matches(stale_transport, ["tv"])
print("reapply manifest semantic/transport projection tests passed")
