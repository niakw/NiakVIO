#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
INDEX = ROOT / "assets/providers/index.json"
TARGETS = {
    "72x32": (72, 32),
    "96x40": (96, 40),
    "96x96": (96, 96),
}

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
index = json.loads(INDEX.read_text(encoding="utf-8"))
rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
manifest_ids = {str(row.get("id") or "").strip().casefold() for row in rows}
providers = index.get("providers")
assert isinstance(providers, dict)
assert set(providers) == manifest_ids, {
    "missing": sorted(manifest_ids - set(providers)),
    "unknown": sorted(set(providers) - manifest_ids),
}
assert index.get("futurePolicy") == "committed-assets-only-no-network-regeneration"
assert index.get("format") == "webp-lossless"
assert set(index.get("targets") or []) == set(TARGETS)
assert index.get("missingCount") == 0, index.get("missing")
assert int(index.get("providerCount") or 0) == len(rows)

for provider_id, row in providers.items():
    assets = row.get("assets") or {}
    urls = row.get("urls") or {}
    for key, size in TARGETS.items():
        rel = str(assets.get(key) or "")
        assert rel == f"assets/providers/{key}/{provider_id}.webp", (provider_id, key, rel)
        path = ROOT / rel
        assert path.is_file(), (provider_id, path)
        with Image.open(path) as image:
            assert image.format == "WEBP", (provider_id, key, image.format)
            assert image.size == size, (provider_id, key, image.size)
        assert str(urls.get(key) or "").endswith(f"/assets/providers/{key}/{provider_id}.webp")

for row in rows:
    provider_id = str(row.get("id") or "").strip().casefold()
    expected = f"https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/96x96/{provider_id}.webp"
    assert row.get("logo") == expected, (provider_id, row.get("logo"), expected)

print(
    f"provider logo asset contract passed: providers={len(rows)} "
    "targets=72x32,96x40,96x96 manifest_logo=96x96"
)
