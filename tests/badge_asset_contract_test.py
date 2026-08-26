#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
MAPPING = ROOT / "assets/mapping_core_brain_ui_v2_complete.json"
README = ROOT / "assets/README.txt"
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
LIGHT_QA = ROOT / "assets/docs/LIGHT_BADGE_QA.json"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
readme = README.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")
light_qa = json.loads(LIGHT_QA.read_text(encoding="utf-8"))

badges = [row for row in (catalog.get("badges") or []) if isinstance(row, dict)]
assert len(badges) >= 74, f"expected complete 74-badge baseline or newer, got {len(badges)}"
by_id = {str(row.get("id") or ""): row for row in badges}
assert len(by_id) == len(badges), "badge ids must be unique"
assert {"vf", "vff", "vfq", "vo", "multi", "vostfr"} <= set(by_id)
assert by_id["vf"]["pattern"] != by_id["vff"]["pattern"]

for badge_id, row in by_id.items():
    for theme in ("transparent", "dark", "light"):
        for size in ("72x32", "96x40"):
            rel = str((((row.get("assets") or {}).get(theme) or {}).get(size) or ""))
            assert rel == f"assets/{theme}/{size}/{badge_id}.webp", (badge_id, theme, size, rel)
            payload = (ROOT / rel).read_bytes()
            assert payload[:4] == b"RIFF" and payload[8:12] == b"WEBP", rel

assert light_qa.get("schemaVersion") == 2
assert light_qa.get("revision") == "full-surface-v4-native-chip"
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
    "dark_app_background": "assets/stream-badges-dark.json",
    "light_app_background": "assets/stream-badges-light.json",
}
assert "Use assets/dark when the Nuvio application background is gray/dark." in readme
assert "Use assets/light when the Nuvio application background is white/light." in readme
assert "DUAL-MODE RUNTIME RULE" in readme

core_badge_ids = {
    "uhd-blu-ray", "4k-ultra-hd", "1080p-full-hd", "720p-hd", "480p-sd",
    "blu-ray-disc", "webdl", "webrip", "hdtv", "dvd-rip", "remux",
    "dolby-vision", "hdr10-plus", "hdr10", "imax-enhanced", "imax", "hevc", "avc", "10bit",
    "dolby-atmos", "truehd", "dolby-digital-plus", "dolby-digital", "dts-x", "dts-hd-master-audio",
    "7.1", "5.1", "multi", "vf", "vff", "vfq", "vo", "vostfr", "sub-fr", "sub-en", "forced", "sdh-cc",
}
missing = sorted(core_badge_ids - set(by_id))
assert not missing, f"Core emits badge IDs with no catalog image: {missing}"
for badge_id in core_badge_ids:
    assert f'"{badge_id}"' in core, f"expected shared Core to reference locked badge id {badge_id}"
for stale_id in ("dts-hd-ma", "7-1-audio", "5-1-audio", "sdh"):
    assert f'"{stale_id}"' not in core, f"stale non-catalog badge alias leaked from Core: {stale_id}"

rules = "\n".join(mapping.get("rules") or [])
assert "Never infer Blu-ray or Ultra HD Blu-ray from 1080p/2160p alone." in rules
assert "REMUX must be confirmed" in rules
assert "Always replace every provider-owned stream description" in rules
assert "TMDB may fill media context" in rules

catalog_groups = {str(row.get("id") or "") for row in (catalog.get("groups") or []) if isinstance(row, dict)}
for theme in ("dark", "light", "fusion"):
    feed = json.loads((ROOT / f"assets/stream-badges-{theme}.json").read_text(encoding="utf-8"))
    filters = feed.get("filters") or []
    groups = feed.get("groups") or []
    assert len(filters) == len(badges), (theme, len(filters))
    assert len(groups) == len(catalog_groups), theme
    assert {str(row.get("id") or "") for row in groups} == catalog_groups
    for group in groups:
        assert str(group.get("color") or "").startswith("#")
        assert str(group.get("borderColor") or "").startswith("#")
    feed_by_id = {str(row.get("id") or ""): row for row in filters}
    assert set(feed_by_id) == set(by_id), theme
    for badge_id, row in feed_by_id.items():
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
    f"catalog={len(badges)} themes=3 sizes=2 core_ids={len(core_badge_ids)} "
    f"light_qa_rows={len(qa_rows)} native_streambadge_feeds=bordered emoji_fallback=true"
)
