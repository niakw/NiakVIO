#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "activate_bulk_offline_proven_providers.py"

spec = importlib.util.spec_from_file_location("bulk_activation_catalog_contract", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = {
    "id": "reanime-to",
    "name": "ReAnime",
    "supportedTypes": ["anime", "tv"],
    "canonicalSupportedTypes": ["anime"],
    "filename": "providers/reanime-to--nuvio--abc.js",
    "enabled": True,
    "disabledPlatforms": ["android-tv"],
}
result = module.canonical_catalog_scraper(source)

assert "canonicalSupportedTypes" not in result, result
assert result["supportedTypes"] == ["anime"], result
assert result["disabledPlatforms"] == [], result
assert source["canonicalSupportedTypes"] == ["anime"], "helper mutated source row"
assert source["supportedTypes"] == ["anime", "tv"], "helper mutated source transport aliases"

text = SCRIPT.read_text(encoding="utf-8")
assert 'catalog_entry["scraper"] = canonical_catalog_scraper(manifest_row)' in text
assert 'catalog_entry["scraper"] = dict(manifest_row)' not in text

print("PROVIDER_BULK_ACTIVATION_CATALOG_PROJECTION_OK")
