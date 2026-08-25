#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
MAPPING = ROOT / "assets/mapping_core_brain_ui_v2_complete.json"
README = ROOT / "assets/README.txt"
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
LIGHT_QA = ROOT / "assets/docs/LIGHT_BADGE_QA.json"
FUSION = ROOT / "assets/stream-badges-fusion.json"
RAW_PREFIX = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
readme = README.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")
light_qa = json.loads(LIGHT_QA.read_text(encoding="utf-8"))

badges = catalog.get("badges") or []
assert len(badges) == 73, f"expected complete 73-badge image catalog, got {len(badges)}"
by_id = {str(row.get("id") or ""): row for row in badges if isinstance(row, dict)}
assert len(by_id) == len(badges), "badge ids must be unique"

for badge_id, row in by_id.items():
    pattern = str(row.get("pattern") or "")
    assert pattern, (badge_id, "missing regex")
    # Parsed regexes must contain one escaping layer. Two backslashes here mean the
    # Kotlin/Java regex engine receives a literal backslash instead of \b/\s/etc.
    assert "\\\\" not in pattern, (badge_id, "over-escaped regex", repr(pattern))
    try:
        re.compile(pattern)
    except re.error as exc:
        raise AssertionError((badge_id, pattern, exc)) from exc

    assets = row.get("assets") or {}
    for theme in ("transparent", "dark", "light"):
        themed = assets.get(theme) or {}
        for size in ("72x32", "96x40"):
            rel = str(themed.get(size) or "")
            assert rel, (badge_id, theme, size, "missing asset path")
            path = ROOT / rel
            assert path.is_file(), (badge_id, theme, size, rel, "missing image")
            assert path.suffix.lower() == ".webp", (badge_id, rel)
            assert path.stat().st_size > 0, (badge_id, rel, "empty image")

assert light_qa.get("revision") == "light-contrast-v3-native-size", light_qa.get("revision")
assert light_qa.get("catalogBadges") == len(badges)
assert light_qa.get("assetCount") == len(badges) * 2
assert light_qa.get("changedCount") == len(badges) * 2
assert light_qa.get("rerenderedTextCount", 0) > 0
assert light_qa.get("preservedArtworkCount", 0) > 0
assert light_qa.get("minimumGenericFontSize", 0) >= 9
assert light_qa.get("whiteBackgroundMinimumSeparationRatio", 0) >= 4.5
assert light_qa.get("sourceOfTruth") == "assets/transparent"
assert light_qa.get("idempotent") is True
qa_rows = light_qa.get("rows") or []
assert len(qa_rows) == len(badges) * 2
qa_by_key = {
    (str(row.get("badge") or ""), str(row.get("size") or "")): row
    for row in qa_rows if isinstance(row, dict)
}
assert len(qa_by_key) == len(qa_rows)
for badge_id in by_id:
    for size in ("72x32", "96x40"):
        qa = qa_by_key.get((badge_id, size))
        assert qa, (badge_id, size, "missing light QA row")
        assert qa.get("output") == by_id[badge_id]["assets"]["light"][size]
        separation = max(
            float(qa.get("backgroundVsWhiteContrast") or 0),
            float(qa.get("outlineVsWhiteContrast") or 0),
        )
        assert separation >= 4.5, (badge_id, size, separation)

assert mapping["display"]["preferredThemeFolders"] == {
    "dark_app_background": "assets/dark",
    "light_app_background": "assets/light",
}
assert mapping["display"]["transparentAssets"] == "assets/transparent"
assert mapping["display"]["hideUnknownBadges"] is True
assert mapping["display"]["alwaysReplaceProviderDescription"] is True
assert mapping["display"]["presentationRevision"] == "global_core_v12"
assert mapping["display"]["clientProjection"]["compatibilityEnvelopeField"] == "size"
assert mapping["display"]["clientProjection"]["suppressedLegacyRecompositionFields"] == ["quality", "language"]
assert mapping["display"]["fallbackWhenNativeBadgesDisabled"] == "emojiTechnicalLine"
assert mapping["display"]["nativeBadgeFeeds"] == {
    "recommended": "assets/stream-badges-fusion.json",
    "dark_app_background": "assets/stream-badges-dark.json",
    "light_app_background": "assets/stream-badges-light.json",
    "requiresNuvioImport": True,
}
assert "Use assets/dark when the Nuvio application background is gray/dark." in readme
assert "Use assets/light when the Nuvio application background is white/light." in readme

core_badge_ids = {
    "uhd-blu-ray", "4k-ultra-hd", "1080p-full-hd", "720p-hd", "480p-sd",
    "blu-ray-disc", "webdl", "webrip", "hdtv", "dvd-rip", "remux",
    "dolby-vision", "hdr10-plus", "hdr10", "imax-enhanced", "imax",
    "hevc", "avc", "10bit", "dolby-atmos", "truehd", "dolby-digital-plus",
    "dolby-digital", "dts-x", "dts-hd-master-audio", "7.1", "5.1", "multi",
    "vff", "vfq", "vo", "vostfr", "sub-fr", "sub-en", "forced", "sdh-cc",
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
assert "TMDB may fill media context" in rules
assert "V12 mirrors the canonical presentation into size" in rules

# Exact payloads consumed by official Nuvio StreamBadgeRules.
for theme in ("dark", "light"):
    feed_path = ROOT / f"assets/stream-badges-{theme}.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    assert len(feed.get("filters") or []) == len(badges)
    assert len(feed.get("groups") or []) == len(catalog.get("groups") or [])
    feed_by_id = {str(row.get("id") or ""): row for row in feed.get("filters") or []}
    assert set(feed_by_id) == set(by_id)
    for badge_id, row in feed_by_id.items():
        expected_rel = by_id[badge_id]["assets"][theme]["96x40"]
        assert row["imageURL"].endswith(expected_rel)
        assert row["pattern"] == by_id[badge_id]["pattern"]
        assert "\\\\" not in str(row["pattern"])
        assert row["isEnabled"] is True

fusion = json.loads(FUSION.read_text(encoding="utf-8"))
fusion_by_id = {str(row.get("id") or ""): row for row in fusion.get("filters") or []}
assert set(fusion_by_id) == set(by_id)
for badge_id, row in fusion_by_id.items():
    assert row["pattern"] == by_id[badge_id]["pattern"]
    assert "\\\\" not in str(row["pattern"])
    image_url = str(row["imageURL"])
    assert image_url.startswith(RAW_PREFIX)
    image = ROOT / image_url.removeprefix(RAW_PREFIX)
    assert image.is_file() and image.stat().st_size > 0

# Smoke the regexes against the canonical V12 matcher vocabulary.
examples = {
    "4k-ultra-hd": "🎞️ 2160p • BLU-RAY • HEVC • HLS",
    "blu-ray-disc": "🎞️ 2160p • BLU-RAY • HEVC • HLS",
    "hevc": "🎞️ 2160p • BLU-RAY • HEVC • HLS",
    "dolby-digital-plus": "🔊 E-AC3 • 5.1",
    "5.1": "🔊 E-AC3 • 5.1",
}
for badge_id, text in examples.items():
    assert re.search(str(fusion_by_id[badge_id]["pattern"]), text), (badge_id, text)

print(
    "badge asset contract passed: "
    f"catalog={len(badges)} feeds=dark+light+fusion regexes=executable "
    f"light_qa_rows={len(qa_rows)} presentation=global_core_v12"
)
