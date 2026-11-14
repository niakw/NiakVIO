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


# The independent filesystem scope audit must count a France-only identity
# exactly once without mutating the Global manifest or executing any asset.
from current_provider_scope import audit_projection_scope

with tempfile.TemporaryDirectory(prefix="niakvio-projection-scope-") as directory:
    root = Path(directory)
    for folder in ("providers", "provider-disabled", "vf"):
        (root / folder).mkdir()
    for filename in ("providers/shared.js", "providers/global.js",
                     "providers/france.js", "provider-disabled/retained.js"):
        (root / filename).write_text("/* synthetic non-executable fixture */\n", encoding="utf-8")

    def row(pid, filename, enabled=True):
        return {"id": pid, "filename": filename, "enabled": enabled}

    global_rows = [row("shared", "providers/shared.js"),
                   row("global", "providers/global.js")]
    french_rows = [row("SHARED", "../providers/shared.js"),
                   row("france", "../providers/france.js"),
                   row("retained", "../provider-disabled/retained.js", False)]

    def write_manifests(g, v):
        (root / "manifest.json").write_text(json.dumps({"scrapers": g}), encoding="utf-8")
        (root / "vf/manifest.json").write_text(json.dumps({"scrapers": v}), encoding="utf-8")

    write_manifests(global_rows, french_rows)
    assert audit_projection_scope(root) == {
        "global_visible": 2, "global_active": 2, "france_visible": 3,
        "france_active": 2, "shared": 1, "global_only": 1,
        "france_only": 2, "union_visible": 4, "union_active": 3,
    }
    for invalid in (
        [*french_rows, row("FRANCE", "../providers/france.js")],
        [row("shared", "../providers/france.js")],
        [row("shared", "../providers/shared.js", False)],
        [row("escaped", "../../providers/shared.js")],
        [row("escaped", "https://example.invalid/provider.js")],
        [row("missing", "../providers/nonexistent.js")],
        [row("shared", "../providers/shared.js"), row("alias", "../providers/shared.js")],
        [row("retained", "../provider-disabled/retained.js", True)],
    ):
        write_manifests(global_rows, invalid)
        try:
            audit_projection_scope(root)
        except RuntimeError:
            pass
        else:
            raise AssertionError(("invalid manifest accepted", invalid))

actual_scope = audit_projection_scope(ROOT)
assert actual_scope["union_visible"] == (
    actual_scope["global_only"] + actual_scope["france_only"] + actual_scope["shared"]
)
print("Projection filesystem scope audit passed:", actual_scope)


# Targeted projection sync must obey the same France-only authority as the
# complete deterministic rebuild, and reject unknown or leaked identities.
from sync_manifest_projection_rows import synced_vf

with tempfile.TemporaryDirectory(prefix="niakvio-vf-targeted-sync-") as directory:
    root = Path(directory)
    general = {"name": "Synthetic", "version": "1.2.3", "scrapers": [
        {"id": "shared", "filename": "providers/shared.js", "enabled": True,
         "contentLanguage": ["fr", "en"], "supportedTypes": ["movie"]},
        {"id": "global", "filename": "providers/global.js", "enabled": True,
         "contentLanguage": ["en"], "supportedTypes": ["movie"]},
    ]}
    french = {"id": "fr-only", "filename": "provider-disabled/fr-only.js",
              "enabled": False, "contentLanguage": ["fr"], "supportedTypes": ["movie"]}
    sample_catalog(root, french)
    stale = {"scrapers": [
        {"id": "FR-ONLY", "filename": "../providers/stale.js", "enabled": True},
        {"id": "SHARED", "filename": "../providers/stale-shared.js", "enabled": False},
    ]}
    full = build_manifest(general, {}, {"vf"}, "VF uniquement", root=root)
    assert synced_vf(general, stale, root=root) == full
    assert synced_vf(general, {"scrapers": [stale["scrapers"][1]]}, root=root) == full
    assert synced_vf(general, full, root=root) == full
    assert [row["id"] for row in general["scrapers"]] == ["shared", "global"]
    for invalid in (
        {"scrapers": [{"id": "unknown"}]},
        {"scrapers": [{"id": "shared"}, {"id": "SHARED"}]},
    ):
        try:
            synced_vf(general, invalid, root=root)
        except SystemExit:
            pass
        else:
            raise AssertionError("unowned or duplicate VF entry accepted")
    leaked = {**general, "scrapers": [*general["scrapers"], french]}
    try:
        synced_vf(leaked, stale, root=root)
    except SystemExit:
        pass
    else:
        raise AssertionError("France-only ID leaked into Global")

print("Targeted VF synchronization authority contract passed")
