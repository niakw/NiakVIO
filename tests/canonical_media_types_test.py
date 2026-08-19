#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = {"movie", "tv", "anime"}


def validate_manifest(path: Path) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    anime = 0
    for index, row in enumerate(data.get("scrapers", [])):
        if not isinstance(row, dict):
            raise AssertionError(f"{path}: scraper[{index}] must be an object")
        provider_id = str(row.get("id") or "").strip()
        assert provider_id, f"{path}: scraper[{index}] has no id"
        key = provider_id.casefold()
        assert key not in seen, f"{path}: duplicate provider id {provider_id!r}"
        seen.add(key)
        raw = row.get("supportedTypes")
        assert isinstance(raw, list) and raw, f"{path}: {provider_id} must publish supportedTypes"
        types = [str(value).strip().lower() for value in raw]
        assert len(types) == len(set(types)), f"{path}: {provider_id} repeats supportedTypes {types}"
        invalid = [value for value in types if value not in CANONICAL]
        assert not invalid, (
            f"{path}: {provider_id} publishes non-canonical media types {invalid}; "
            "manifest vocabulary is movie|tv|anime and client aliases belong at the input boundary"
        )
        anime += int("anime" in types)
    assert seen, f"{path}: no providers"
    return len(seen), anime


canonical_count, canonical_anime = validate_manifest(ROOT / "manifest.json")
assert canonical_count >= 80, canonical_count
assert canonical_anime > 0, "canonical manifest must retain anime providers"

hotfix = ROOT / "playback-hotfix/manifest.json"
if hotfix.is_file():
    hotfix_count, _ = validate_manifest(hotfix)
    assert hotfix_count > 0

corpus = json.loads((ROOT / ".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))
fixtures = {row["slug"]: row["fixture"] for row in corpus.get("fixtures", []) if isinstance(row, dict) and isinstance(row.get("fixture"), dict)}
for slug in ("jujutsu-kaisen-s01e01", "mushoku-tensei-s01e01"):
    fixture = fixtures[slug]
    assert str(fixture.get("category") or "").lower() == "anime", (slug, fixture)
    # The concrete catalogue path may still be tv. The device lab expands anime
    # fixtures per-provider to anime and/or tv according to declared capabilities.
    assert str(fixture.get("mediaType") or "").lower() in {"tv", "anime"}, (slug, fixture)

print(
    "canonical media type tests passed: "
    f"providers={canonical_count} anime_capable={canonical_anime} vocabulary=movie|tv|anime"
)
