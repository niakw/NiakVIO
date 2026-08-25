#!/usr/bin/env python3
"""Validate the fully materialized NiakVIO badge system."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
REPORT = ROOT / "assets/docs/BADGE_QA.json"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
badges = [row for row in (catalog.get("badges") or []) if isinstance(row, dict)]
assert len(badges) == 74, f"expected 74 redesigned badges including generic VF, got {len(badges)}"
by_id = {str(row.get("id") or ""): row for row in badges}
assert len(by_id) == len(badges)
assert {"vf", "vff", "vfq", "vo", "multi", "vostfr"} <= set(by_id)
assert by_id["vf"]["pattern"] != by_id["vff"]["pattern"]

checked = 0
for badge_id, row in by_id.items():
    for theme in ("transparent", "dark", "light"):
        for size in ("72x32", "96x40"):
            rel = str((((row.get("assets") or {}).get(theme) or {}).get(size) or ""))
            assert rel == f"assets/{theme}/{size}/{badge_id}.webp", (badge_id, theme, size, rel)
            path = ROOT / rel
            assert path.is_file() and path.stat().st_size > 0, (badge_id, theme, size)
            payload = path.read_bytes()
            assert payload[:4] == b"RIFF" and payload[8:12] == b"WEBP", rel
            checked += 1
assert checked == 74 * 3 * 2, checked

report = json.loads(REPORT.read_text(encoding="utf-8"))
assert report["revision"] == "full-surface-v4-native-chip"
assert report["catalogBadges"] == 74
assert report["assetCount"] == 444
assert report["nativeChipChrome"] is True
assert report["webpLossless"] is True
assert report["idempotent"] is True
rows = report.get("rows") or []
assert len(rows) == 444
for row in rows:
    assert float(row.get("heightCoverage") or 0) > 0, row
    if not row.get("brand"):
        assert max(float(row.get("widthCoverage") or 0), float(row.get("heightCoverage") or 0)) >= 0.78, row

for theme in ("dark", "light", "fusion"):
    feed = json.loads((ROOT / f"assets/stream-badges-{theme}.json").read_text(encoding="utf-8"))
    filters = feed.get("filters") or []
    assert len(filters) == 74, (theme, len(filters))
    ids = {str(row.get("id") or "") for row in filters}
    assert ids == set(by_id), theme
    for row in filters:
        assert row.get("tagStyle") == "filled", (theme, row.get("id"), row.get("tagStyle"))
        assert str(row.get("tagColor") or "").startswith("#"), (theme, row.get("id"))
        assert str(row.get("borderColor") or "").startswith("#"), (theme, row.get("id"))
        assert str(row.get("textColor") or "").startswith("#"), (theme, row.get("id"))
        assert row.get("isEnabled") is True

print(f"badge asset contract passed: badges={len(badges)} assets={checked} themes=3 sizes=2 native_chip_style=true vf_generic=true")
