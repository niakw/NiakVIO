#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_nuvio_client_lab_matrix import expand_push_source  # noqa: E402

manifest = {
    "scrapers": [
        {"id": "movie-a", "enabled": True, "supportedTypes": ["movie"]},
        {"id": "movie-tv", "enabled": True, "supportedTypes": ["movie", "tv"]},
        {"id": "tv-a", "enabled": True, "supportedTypes": ["tv"]},
        {"id": "anime-a", "enabled": True, "supportedTypes": ["anime"]},
        {"id": "disabled-movie", "enabled": False, "supportedTypes": ["movie"]},
    ]
}
source = {
    "fixtures": [
        {"slug": "interstellar", "providers": ["stale"], "fixture": {"mediaType": "movie", "category": "movie"}},
        {"slug": "breaking-bad", "providers": ["stale"], "fixture": {"mediaType": "tv", "category": "tv"}},
        {"slug": "jjk", "providers": ["stale"], "fixture": {"mediaType": "tv", "category": "anime"}},
    ]
}

expanded = expand_push_source(source, manifest)
rows = {row["slug"]: row for row in expanded["fixtures"]}
assert rows["interstellar"]["providers"] == ["movie-a", "movie-tv"]
assert rows["breaking-bad"]["providers"] == ["movie-tv", "tv-a"]
assert rows["jjk"]["providers"] == ["anime-a"]
assert all(row["provider_selection"] == "all_enabled_compatible" for row in rows.values())
assert expanded["provider_selection"] == "all_enabled_compatible"

print("nuvio client lab dynamic provider selection test passed")
