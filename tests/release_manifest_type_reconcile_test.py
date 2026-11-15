#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "reconcile_release_manifest_types.py"
spec = importlib.util.spec_from_file_location("reconcile_release_manifest_types", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

manifest = {
    "scrapers": [
        {"id": "purstream", "supportedTypes": ["movie"], "enabled": True},
        {"id": "anime-demo", "supportedTypes": ["anime"], "enabled": True},
        {"id": "stable", "supportedTypes": ["movie", "tv"], "enabled": True},
    ]
}
config = {
    "provider_patches": {
        "purstream": {"published_types": ["movie", "tv"]},
        "anime-demo": {"published_types": ["anime"]},
    },
    "provider_capabilities": {
        "stable": {"catalogue_types": ["movie", "tv"]},
    },
}
changed = mod.reconcile_document(manifest, config)
rows = {row["id"]: row for row in manifest["scrapers"]}
assert changed == ["anime-demo", "purstream"], changed
assert rows["purstream"]["supportedTypes"] == ["movie", "tv"]
assert "canonicalSupportedTypes" not in rows["purstream"]
assert rows["anime-demo"]["supportedTypes"] == ["anime", "tv"]
assert rows["anime-demo"]["canonicalSupportedTypes"] == ["anime"]
assert rows["stable"]["supportedTypes"] == ["movie", "tv"]
print("RELEASE_MANIFEST_TYPE_RECONCILE_OK")
