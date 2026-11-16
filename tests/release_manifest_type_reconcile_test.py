#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
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

catalog = {
    "providers": [
        {
            "canonicalId": "purstream",
            "scraper": {"id": "purstream", "supportedTypes": ["movie"], "enabled": True},
            "projections": {"general": True, "vf": True},
        },
        {
            "canonicalId": "fr-only",
            "scraper": {"id": "fr-only", "supportedTypes": ["movie"], "enabled": True},
            "projections": {"general": False, "vf": True},
        },
    ]
}
catalog_config = {
    **config,
    "provider_patches": {
        **config["provider_patches"],
        "fr-only": {"published_types": ["anime"]},
    },
}
catalog_changed = mod.reconcile_catalog(catalog, catalog_config)
assert catalog_changed == ["fr-only", "purstream"], catalog_changed
catalog_rows = {row["canonicalId"]: row["scraper"] for row in catalog["providers"]}
assert catalog_rows["purstream"]["supportedTypes"] == ["movie", "tv"]
assert catalog_rows["fr-only"]["supportedTypes"] == ["anime", "tv"]
assert catalog_rows["fr-only"]["canonicalSupportedTypes"] == ["anime"]
print("RELEASE_MANIFEST_TYPE_RECONCILE_OK")
