#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]

anime_only = []
for row in rows:
    canonical = {
        str(value or "").strip().casefold()
        for value in row.get("canonicalSupportedTypes") or []
        if str(value or "").strip()
    }
    if canonical == {"anime"}:
        anime_only.append(row)

assert anime_only, "expected at least one canonically anime-only provider"
for row in anime_only:
    provider_id = str(row.get("id") or "<unknown>")
    assert row.get("canonicalSupportedTypes") == ["anime"], (
        provider_id,
        row.get("canonicalSupportedTypes"),
    )
    transport = [
        str(value or "").strip().casefold()
        for value in row.get("supportedTypes") or []
    ]
    assert transport == ["anime", "tv", "movie"], (
        f"{provider_id}: anime semantic provider must expose anime+tv+movie launch compatibility",
        transport,
    )

core = (ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py").read_text(encoding="utf-8")
assert 'if(canonical==="anime")return namespace==="movie"?"movie":"tv";' in core
assert 'return"anime";\n  }\n  return canonical==="movie"?"movie":"tv";' not in core
assert 'tmdb-data-contract-launch-gate-v27-anime-semantic-transport' in core

materializer = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")
assert "def normalize_anime_transport_compatibility(" in materializer
assert 'wanted = ["anime", "tv", "movie"]' in materializer

finalizer = (ROOT / "scripts" / "finalize_gowaru_provider_v3_source_plans.py").read_text(encoding="utf-8")
assert 'route.rstrip(";,)]")' in finalizer
assert 'route.rstrip(";,)]}")' not in finalizer

print(
    "provider anime semantic/transport contract passed "
    f"anime_only={len(anime_only)} canonical=anime transport=anime,tv,movie"
)
