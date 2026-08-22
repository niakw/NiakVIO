#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
MAPPING = ROOT / "assets/mapping_core_brain_ui_v2_complete.json"
README = ROOT / "assets/README.txt"
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
readme = README.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")

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
    "dark_light_contrast=true image_fallbacks=true"
)
