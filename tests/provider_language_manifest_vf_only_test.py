#!/usr/bin/env python3
"""France-only catalog projection must survive deterministic VF generation."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_language_manifests import build_manifest, france_only_catalog_rows, build_no_anime_manifest


def sample_catalog(root: Path, row: dict) -> None:
    (root / "provider_catalog.json").write_text(json.dumps({
        "sourceOfTruth": True,
        "providers": [{"canonicalId": row["id"], "scraper": row, "projections": {"general": False, "vf": True}}],
    }), encoding="utf-8")


with tempfile.TemporaryDirectory(prefix="niakvio-vf-only-contract-") as directory:
    root = Path(directory)
    french = {
        "id": "france-only-test", "name": "France-only test",
        "supportedTypes": ["movie", "tv"],
        "contentLanguage": ["fr"], "filename": "providers/france-only-test--v3.js",
        "enabled": False, "disabledPlatforms": [],
    }
    source = {
        "name": "NiakVIO synthetic", "version": "1.2.3",
        "scrapers": [{
            "id": "global-only", "name": "Global test",
            "supportedTypes": ["movie", "tv"],
            "contentLanguage": ["en"], "filename": "providers/global-only--v3.js",
            "enabled": True,
        }],
    }
    sample_catalog(root, french)
    assert france_only_catalog_rows(root=root) == [french]
    projected = build_manifest(source, {}, {"vf"}, "VF uniquement", root=root)
    assert [row["id"] for row in projected["scrapers"]] == ["france-only-test"], projected
    assert projected["scrapers"][0]["filename"] == "../providers/france-only-test--v3.js"
    assert projected["scrapers"][0]["enabled"] is False
    without_anime = build_no_anime_manifest(projected)
    assert len(without_anime["scrapers"]) == 1
    assert without_anime["scrapers"][0]["filename"] == "../providers/france-only-test--v3.js"

    anime = {
        **french, "id": "anime-only-fr",
        "filename": "providers/anime-only-fr--v3.js",
        "supportedTypes": ["anime"],
    }
    sample_catalog(root, anime)
    rows = france_only_catalog_rows(root=root)
    assert rows[0]["supportedTypes"] == ["anime", "tv"]
    assert rows[0]["canonicalSupportedTypes"] == ["anime"]
    projected = build_manifest(source, {}, {"vf"}, "VF uniquement", root=root)
    assert projected["scrapers"][0]["supportedTypes"] == ["anime", "tv"]
    assert build_no_anime_manifest(projected)["scrapers"] == []

    sample_catalog(root, {**french, "contentLanguage": ["en"]})
    try:
        france_only_catalog_rows(root=root)
    except ValueError as exc:
        assert "declared French" in str(exc)
    else:
        raise AssertionError("unqualified language accepted as France-only")

    sample_catalog(root, french)
    duplicate = {
        **source, "scrapers": [
            {**source["scrapers"][0], "id": "france-only-test"},
        ],
    }
    try:
        build_manifest(duplicate, {}, {"vf"}, "VF uniquement", root=root)
    except ValueError as exc:
        assert "duplicated in Global" in str(exc)
    else:
        raise AssertionError("France-only row leaked into Global")

print("France-only catalog/projection contract passed: no duplicates, correct paths, anime alias preserved")
