#!/usr/bin/env python3
"""Validate the fully materialized NiakVIO badge system."""
from __future__ import annotations

import json
from pathlib import Path

from badge_versioning import latest_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG_VERSION, CATALOG = latest_catalog(ROOT)
REPORT = ROOT / "assets/docs/BADGE_QA.json"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
badges = [row for row in (catalog.get("badges") or []) if isinstance(row, dict)]
assert len(badges) >= 150, f"expected universal v3 catalog, got {len(badges)}"
by_id = {str(row.get("id") or ""): row for row in badges}
assert len(by_id) == len(badges)
legacy_public_ids = {"vf", "vff", "vfq", "vo", "multi", "vostfr", "pg-13", "tv-ma"}
assert not (legacy_public_ids & set(by_id)), sorted(legacy_public_ids & set(by_id))
assert {"hls", "dash"} <= set(by_id), sorted({"hls", "dash"} - set(by_id))
required_v3 = {"lang-fr", "lang-fr-ca", "lang-ko", "lang-ja", "lang-de", "lang-bg", "lang-bn", "lang-pt-br", "lang-fi", "lang-el", "lang-hu", "lang-id", "lang-fa", "lang-he", "lang-ku", "lang-uz", "lang-fil", "lang-pl", "lang-ro", "lang-sk", "lang-sv", "lang-cs", "lang-vi", "lang-zh-hk", "lang-zh-tw", "sub-fr", "sub-ko", "age-19", "age-kr19", "age-us-pg13"}
assert required_v3 <= set(by_id), sorted(required_v3 - set(by_id))

# Nuvio clients compile filter.pattern directly (Java Pattern on TV). After JSON
# decoding every regex escape must therefore be one backslash, never a literal
# double-backslash sequence such as "\\\\b".
for badge_id, row in by_id.items():
    pattern = str(row.get("pattern") or "")
    assert "\\\\" not in pattern, (badge_id, pattern, "double-escaped runtime regex")


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
assert checked == len(badges) * 3 * 2, checked

report = json.loads(REPORT.read_text(encoding="utf-8"))
assert report["revision"] == "full-surface-v7-delivery-v4"
assert report["catalogBadges"] == len(badges)
assert report["assetCount"] == len(badges) * 3 * 2
assert report["nativeChipChrome"] is True
assert report["webpLossless"] is True
assert report["idempotent"] is True
rows = report.get("rows") or []
assert len(rows) == len(badges) * 3 * 2
for row in rows:
    assert float(row.get("heightCoverage") or 0) > 0, row
    if not row.get("brand"):
        assert max(float(row.get("widthCoverage") or 0), float(row.get("heightCoverage") or 0)) >= 0.78, row

catalog_groups = {str(row.get("id") or "") for row in (catalog.get("groups") or []) if isinstance(row, dict)}
for theme in ("dark", "light", "transparent", "fusion"):
    feed = json.loads((ROOT / f"assets/stream-badges-{theme}.json").read_text(encoding="utf-8"))
    filters = feed.get("filters") or []
    groups = feed.get("groups") or []
    assert len(filters) == len(badges), (theme, len(filters))
    ids = {str(row.get("id") or "") for row in filters}
    assert ids == set(by_id), theme
    assert {str(row.get("id") or "") for row in groups} == catalog_groups, theme
    for group in groups:
        assert str(group.get("color") or "").startswith("#"), (theme, group.get("id"), "color")
        assert str(group.get("borderColor") or "").startswith("#"), (theme, group.get("id"), "borderColor")
    for row in filters:
        assert row.get("tagStyle") == "bordered", (theme, row.get("id"), row.get("tagStyle"))
        assert str(row.get("tagColor") or "").startswith("#"), (theme, row.get("id"))
        assert str(row.get("borderColor") or "").startswith("#"), (theme, row.get("id"))
        assert str(row.get("textColor") or "").startswith("#"), (theme, row.get("id"))
        assert row.get("isEnabled") is True
        pattern = str(row.get("pattern") or "")
        assert "\\\\" not in pattern, (theme, row.get("id"), pattern, "double-escaped runtime regex")

for theme in ("dark", "light", "transparent", "fusion"):
    latest = (ROOT / f"assets/stream-badges-{theme}.json").read_text(encoding="utf-8")
    versioned = (ROOT / f"assets/stream-badges-{theme}-v{CATALOG_VERSION}.json").read_text(encoding="utf-8")
    assert latest == versioned, f"{theme} latest feed drifted from immutable v4 snapshot"

for theme in ("dark", "light", "transparent", "fusion"):
    assert (ROOT / f"assets/stream-badges-{theme}-v3.json").is_file(), f"historical {theme} v3 must remain available"
assert (ROOT / "assets/stream-badges-fusion-v2.json").is_file(), "historical fusion v2 must remain available"

print(f"badge asset contract passed: badges={len(badges)} assets={checked} themes=3 sizes=2 feeds=4 public_v4=true legacy_v2_v3_preserved=true")
