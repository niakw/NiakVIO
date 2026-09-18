#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/certify_provider_playable_lanes.py"
spec = importlib.util.spec_from_file_location("certifier", MODULE)
assert spec and spec.loader
cert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cert)

fixtures = cert.fixture_index()
assert "sinners-2025" in fixtures
assert "interstellar" in fixtures
registry = {
    "providers": {
        "movieshunt": {
            "lanes": {
                "movie": {
                    "fixtureSlug": "sinners-2025",
                    "knownPositiveFixtures": ["sinners-2025"],
                }
            }
        }
    }
}
targets = {("movieshunt", "movie"): ["interstellar"]}
rows = cert.candidate_fixtures(
    "movieshunt",
    "movie",
    registry=registry,
    fixtures=fixtures,
    targets=targets,
    seed="test",
    limit=6,
)
slugs = [row["slug"] for row in rows]
assert slugs[0] == "sinners-2025", slugs
assert slugs[1] == "interstellar", slugs
assert len(slugs) == len(set(slugs)), slugs
assert all(cert.canonical_lane(row) == "movie" for row in rows)

manifest_row = {
    "id": "ANIME-SAMA",
    "supportedTypes": ["anime", "tv"],
    "canonicalSupportedTypes": ["anime"],
}
assert cert.semantic_types(manifest_row) == ["anime"]
assert cert.fixture_runtime_media_type({
    "tmdbId": "95479",
    "mediaType": "anime",
    "category": "anime",
    "title": "Jujutsu Kaisen",
    "season": 1,
    "episode": 1,
}) == "tv"
assert cert.fixture_runtime_media_type({
    "tmdbId": "157336",
    "mediaType": "movie",
    "category": "movie",
    "title": "Interstellar",
}) == "movie"


manifest = cert.load(ROOT / "manifest.json", {}) or {}
manifest_rows = [
    row for row in manifest.get("scrapers") or []
    if isinstance(row, dict) and cert.canonical(row.get("id"))
]
assert len(manifest_rows) == 46, len(manifest_rows)
assert sum(1 for row in manifest_rows if row.get("enabled") is not False) == 44

print("provider playable certification ordering tests passed")
