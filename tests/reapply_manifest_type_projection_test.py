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

# Published transport mirrors semantic capability except for the single
# Nuvio episodic-anime compatibility alias anime -> tv.
assert projected_transport_types(["anime"]) == ["anime", "tv"]
assert projected_transport_types(["movie", "anime"]) == ["movie", "anime", "tv"]
assert projected_transport_types(["tv", "anime"]) == ["tv", "anime"]
assert projected_transport_types(["movie", "tv"]) == ["movie", "tv"]

anime_only = {"supportedTypes": ["anime"]}
assert apply_manifest_type_projection(anime_only, ["anime"]) is True
assert anime_only == {
    "supportedTypes": ["anime", "tv"],
    "canonicalSupportedTypes": ["anime"],
}
assert semantic_manifest_types(anime_only) == ["anime"]
assert manifest_type_projection_matches(anime_only, ["anime"])
assert apply_manifest_type_projection(anime_only, ["anime"]) is False

ordinary = {"supportedTypes": ["movie", "tv"]}
assert apply_manifest_type_projection(ordinary, ["movie", "tv"]) is False
assert ordinary == {"supportedTypes": ["movie", "tv"]}
assert semantic_manifest_types(ordinary) == ["movie", "tv"]
assert manifest_type_projection_matches(ordinary, ["movie", "tv"])

# Legacy series transport must be treated as stale rather than silently kept.
stale_transport = {
    "supportedTypes": ["tv", "series"],
    "canonicalSupportedTypes": ["tv"],
}
assert semantic_manifest_types(stale_transport) == ["tv"]
assert not manifest_type_projection_matches(stale_transport, ["tv"])
assert apply_manifest_type_projection(stale_transport, ["tv"]) is True
assert stale_transport == {"supportedTypes": ["tv"]}
assert manifest_type_projection_matches(stale_transport, ["tv"])

print("reapply manifest semantic/transport projection tests passed")
