#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.badge_versioning import latest_catalog, latest_mapping

CATALOG_VERSION, CATALOG = latest_catalog(ROOT)
MAPPING_VERSION, MAPPING = latest_mapping(ROOT)
assert MAPPING_VERSION == CATALOG_VERSION
README = ROOT / "assets/README.txt"
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
LIGHT_QA = ROOT / "assets/docs/LIGHT_BADGE_QA.json"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
readme = README.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")
light_qa = json.loads(LIGHT_QA.read_text(encoding="utf-8"))

badges = [row for row in (catalog.get("badges") or []) if isinstance(row, dict)]
assert len(badges) >= 150, f"expected universal v3 badge surface, got {len(badges)}"
by_id = {str(row.get("id") or ""): row for row in badges}
assert len(by_id) == len(badges), "badge ids must be unique"
legacy_public_ids = {"vf", "vff", "vfq", "vo", "multi", "vostfr", "pg-13", "tv-ma"}
assert not (legacy_public_ids & set(by_id)), sorted(legacy_public_ids & set(by_id))

for badge_id, row in by_id.items():
    for theme in ("transparent", "dark", "light"):
        for size in ("72x32", "96x40"):
            rel = str((((row.get("assets") or {}).get(theme) or {}).get(size) or ""))
            assert rel == f"assets/{theme}/{size}/{badge_id}.webp", (badge_id, theme, size, rel)
            payload = (ROOT / rel).read_bytes()
            assert payload[:4] == b"RIFF" and payload[8:12] == b"WEBP", rel

assert light_qa.get("schemaVersion") == 2
assert light_qa.get("revision") == f"full-surface-v{CATALOG_VERSION}-stream-score-v{CATALOG_VERSION}"
assert light_qa.get("catalogBadges") == len(badges)
assert light_qa.get("assetCount") == len(badges) * 2
assert light_qa.get("idempotent") is True
qa_rows = light_qa.get("rows") or []
assert len(qa_rows) == len(badges) * 2
qa_by_key = {(str(row.get("badge") or ""), str(row.get("size") or "")): row for row in qa_rows if isinstance(row, dict)}
for badge_id in by_id:
    for size in ("72x32", "96x40"):
        row = qa_by_key[(badge_id, size)]
        assert row.get("theme") == "light"
        assert int(row.get("bytes") or 0) > 0
        assert len(str(row.get("sha256") or "")) == 64
        if not row.get("brand"):
            assert max(float(row.get("widthCoverage") or 0), float(row.get("heightCoverage") or 0)) >= 0.78

assert mapping["display"]["preferredThemeFolders"] == {
    "dark_app_background": "assets/dark",
    "light_app_background": "assets/light",
}
assert mapping["display"]["transparentAssets"] == "assets/transparent"
assert mapping["display"]["hideUnknownBadges"] is True
assert mapping["display"]["alwaysReplaceProviderDescription"] is True
assert mapping["display"]["fallbackWhenNativeBadgesDisabled"] == "emojiTechnicalLine"
assert mapping["display"]["nativeBadgeFeeds"] == {
    "dark_app_background": f"assets/stream-badges-dark-v{CATALOG_VERSION}.json",
    "light_app_background": f"assets/stream-badges-light-v{CATALOG_VERSION}.json",
    "transparent": f"assets/stream-badges-transparent-v{CATALOG_VERSION}.json",
    "fusion": f"assets/stream-badges-fusion-v{CATALOG_VERSION}.json",
}
assert "Use assets/dark when the Nuvio application background is gray/dark." in readme
assert "Use assets/light when the Nuvio application background is white/light." in readme
assert "DUAL-MODE RUNTIME RULE" in readme

required_universal_ids = {
    "lang-fr", "lang-fr-ca", "lang-en", "lang-ko", "lang-ja", "lang-de",
    "sub-fr", "sub-en", "sub-ko", "age-19", "age-kr19", "age-us-pg13", "hls", "dash",
}
assert required_universal_ids <= set(by_id), sorted(required_universal_ids - set(by_id))
for legacy_id in ("vf", "vff", "vfq", "vo", "multi", "vostfr"):
    assert legacy_id not in by_id, f"legacy locale-specific badge leaked into v3 catalog: {legacy_id}"

for theme in ("dark", "light", "transparent", "fusion"):
    versioned = ROOT / f"assets/stream-badges-{theme}-v{CATALOG_VERSION}.json"
    latest = ROOT / f"assets/stream-badges-{theme}.json"
    assert versioned.is_file(), versioned
    assert versioned.read_bytes() == latest.read_bytes(), f"{theme} v4 must equal latest at v4 publication"

for theme in ("dark", "light", "transparent", "fusion"):
    assert (ROOT / f"assets/stream-badges-{theme}-v3.json").is_file(), f"historical {theme} v3 must be preserved"
assert (ROOT / "assets/stream-badges-fusion-v2.json").is_file(), "historical fusion-v2 must be preserved"
assert '"lang-"+' in core and '"sub-"+' in core, "provider presentation generator must emit universal language/subtitle badge IDs"
for stale_mapping in ('"VF":"vf"', '"VFQ":"vfq"', '"VO":"vo"', '"VOSTFR":"vostfr"'):
    assert stale_mapping not in core, f"legacy public badge mapping leaked from provider presentation generator: {stale_mapping}"

rules = "\n".join(mapping.get("rules") or [])
assert "Never infer Blu-ray or Ultra HD Blu-ray from 1080p/2160p alone." in rules
assert "REMUX must be confirmed" in rules
assert "Always replace every provider-owned stream description" in rules
assert "TMDB may fill media context" in rules

catalog_groups = {str(row.get("id") or "") for row in (catalog.get("groups") or []) if isinstance(row, dict)}
for theme in ("dark", "light", "transparent", "fusion"):
    feed = json.loads((ROOT / f"assets/stream-badges-{theme}.json").read_text(encoding="utf-8"))
    filters = feed.get("filters") or []
    groups = feed.get("groups") or []
    assert len(filters) == len(badges), (theme, len(filters))
    assert len(groups) == len(catalog_groups), theme
    assert {str(row.get("id") or "") for row in groups} == catalog_groups
    for group in groups:
        assert str(group.get("color") or "").startswith("#")
        assert str(group.get("borderColor") or "").startswith("#")
    feed_by_id = {str(row.get("id") or "") for row in filters}
    assert feed_by_id == set(by_id), theme
    rows_by_id = {str(row.get("id") or ""): row for row in filters}
    for badge_id, row in rows_by_id.items():
        asset_theme = "transparent" if theme == "fusion" else theme
        expected_rel = by_id[badge_id]["assets"][asset_theme]["96x40"]
        assert row["imageURL"].endswith(expected_rel), (theme, badge_id, row["imageURL"])
        assert row["pattern"] == by_id[badge_id]["pattern"]
        assert row["isEnabled"] is True
        assert row.get("tagStyle") == "bordered", (theme, badge_id, row.get("tagStyle"))
        for color_key in ("tagColor", "borderColor", "textColor"):
            assert str(row.get(color_key) or "").startswith("#"), (theme, badge_id, color_key)

print(
    "badge asset contract passed: "
    f"catalog={len(badges)} themes=4 sizes=2 universal_language_ids=true "
    f"light_qa_rows={len(qa_rows)} native_streambadge_feeds=bordered emoji_fallback=true"
)

assert len(badges) >= 309
assert any(group.get("id") == "stream-score" for group in catalog.get("groups") or [])
