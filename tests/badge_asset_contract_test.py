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

badges = catalog.get("badges") or []
assert len(badges) == 73, f"expected complete 73-badge image catalog, got {len(badges)}"
by_id = {str(row.get("id") or ""): row for row in badges if isinstance(row, dict)}
assert len(by_id) == len(badges), "badge ids must be unique"

# Every badge in the catalog must have both render sizes for all three contrast
# variants. The UI chooses dark for gray/dark Nuvio themes, light for white/light
# themes, while transparent remains available for contexts that provide contrast.
for badge_id, row in by_id.items():
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

# Structural existence is not enough for light-theme assets: lock the deterministic
# contrast QA report produced from transparent artwork so a future asset refresh
# cannot silently reintroduce white-on-white/tiny-label regressions.
assert light_qa.get("revision") == "light-contrast-v3-native-size", light_qa.get("revision")
assert light_qa.get("catalogBadges") == len(badges), light_qa.get("catalogBadges")
assert light_qa.get("assetCount") == len(badges) * 2, light_qa.get("assetCount")
assert light_qa.get("changedCount") == len(badges) * 2, light_qa.get("changedCount")
assert light_qa.get("rerenderedTextCount", 0) > 0, light_qa.get("rerenderedTextCount")
assert light_qa.get("preservedArtworkCount", 0) > 0, light_qa.get("preservedArtworkCount")
assert light_qa.get("minimumGenericFontSize", 0) >= 9, light_qa.get("minimumGenericFontSize")
assert light_qa.get("whiteBackgroundMinimumSeparationRatio", 0) >= 4.5, light_qa.get("whiteBackgroundMinimumSeparationRatio")
assert light_qa.get("sourceOfTruth") == "assets/transparent", light_qa.get("sourceOfTruth")
assert light_qa.get("idempotent") is True
qa_rows = light_qa.get("rows") or []
assert len(qa_rows) == len(badges) * 2, len(qa_rows)
qa_by_key = {(str(row.get("badge") or ""), str(row.get("size") or "")): row for row in qa_rows if isinstance(row, dict)}
assert len(qa_by_key) == len(qa_rows), "light QA badge/size rows must be unique"
for badge_id in by_id:
    for size in ("72x32", "96x40"):
        qa = qa_by_key.get((badge_id, size))
        assert qa, (badge_id, size, "missing light QA row")
        assert qa.get("output") == by_id[badge_id]["assets"]["light"][size], (badge_id, size, qa.get("output"))
        separation = max(float(qa.get("backgroundVsWhiteContrast") or 0), float(qa.get("outlineVsWhiteContrast") or 0))
        assert separation >= 4.5, (badge_id, size, separation)

assert mapping["display"]["preferredThemeFolders"] == {
    "dark_app_background": "assets/dark",
    "light_app_background": "assets/light",
}
assert mapping["display"]["transparentAssets"] == "assets/transparent"
assert mapping["display"]["hideUnknownBadges"] is True
assert "Use assets/dark when the Nuvio application background is gray/dark." in readme
assert "Use assets/light when the Nuvio application background is white/light." in readme

# These are the exact image IDs emitted by the shared Core presentation wrapper.
# Keep them aligned with the existing complete asset catalog rather than inventing
# near-duplicate aliases such as 5-1-audio/7-1-audio/dts-hd-ma/sdh.
core_badge_ids = {
    "4k-ultra-hd",
    "1080p-full-hd",
    "720p-hd",
    "480p-sd",
    "blu-ray-disc",
    "webdl",
    "webrip",
    "hdtv",
    "dvd-rip",
    "remux",
    "dolby-vision",
    "hdr10-plus",
    "hdr10",
    "imax-enhanced",
    "imax",
    "hevc",
    "avc",
    "10bit",
    "dolby-atmos",
    "truehd",
    "dolby-digital-plus",
    "dolby-digital",
    "dts-x",
    "dts-hd-master-audio",
    "7.1",
    "5.1",
    "multi",
    "vff",
    "vfq",
    "vo",
    "vostfr",
    "sub-fr",
    "sub-en",
    "forced",
    "sdh-cc",
}
missing = sorted(core_badge_ids - set(by_id))
assert not missing, f"Core emits badge IDs with no catalog image: {missing}"
for badge_id in core_badge_ids:
    assert f'"{badge_id}"' in core, f"expected shared Core to reference locked badge id {badge_id}"
for stale_id in ("dts-hd-ma", "7-1-audio", "5-1-audio", "sdh"):
    assert f'"{stale_id}"' not in core, f"stale non-catalog badge alias leaked from Core: {stale_id}"

# The most important branded/technical image cases must retain a declared asset
# provenance rather than silently being regenerated from unrelated facts.
for badge_id in ("4k-ultra-hd", "blu-ray-disc", "dolby-vision", "dolby-atmos"):
    assert by_id[badge_id].get("assetBasis"), (badge_id, "missing asset provenance")

# No resolution-only presentation is allowed to imply physical-media provenance.
rules = "\n".join(mapping.get("rules") or [])
assert "Never infer Blu-ray or Ultra HD Blu-ray from 1080p/2160p alone." in rules
assert "REMUX must be confirmed" in rules

print(
    "badge asset contract passed: "
    f"catalog={len(badges)} themes=3 sizes=2 core_ids={len(core_badge_ids)} "
    f"light_qa_rows={len(qa_rows)} min_white_separation={light_qa['whiteBackgroundMinimumSeparationRatio']} "
    "dark_light_contrast=true image_fallbacks=true"
)
