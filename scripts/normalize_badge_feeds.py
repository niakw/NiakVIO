#!/usr/bin/env python3
"""Generate Dark, Light and Fusion Nuvio StreamBadge imports with native chip styling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"
OUTPUTS = {
    "dark": ROOT / "assets/stream-badges-dark.json",
    "light": ROOT / "assets/stream-badges-light.json",
    "fusion": ROOT / "assets/stream-badges-fusion.json",
}
ACCENTS = {
    "source": "#49B46D",
    "resolution": "#F3C43F",
    "video-tech": "#28B7E4",
    "video-codec": "#559EFF",
    "bit-depth": "#A87BE8",
    "audio-tech": "#E05DAC",
    "audio-codec": "#B873EA",
    "audio-channels": "#F09248",
    "language": "#4CBA70",
    "subtitles": "#32B7C5",
    "age-rating": "#E45F6D",
}


def style(theme: str, group: str) -> dict[str, str]:
    if theme == "light":
        return {"tagColor": "#F7F9FC", "tagStyle": "filled", "textColor": "#111827", "borderColor": ACCENTS.get(group, "#64748B")}
    return {"tagColor": "#151A22", "tagStyle": "filled", "textColor": "#FFFFFF", "borderColor": ACCENTS.get(group, "#94A3B8")}


def build(theme: str) -> dict[str, Any]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    asset_theme = "transparent" if theme == "fusion" else theme
    groups = []
    for group in catalog.get("groups") or []:
        if not isinstance(group, dict):
            continue
        gid = str(group.get("id") or "")
        groups.append({"id": gid, "name": str(group.get("name") or gid), "color": ACCENTS.get(gid, "#64748B"), "isExpanded": True})
    filters = []
    for badge in catalog.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        badge_id = str(badge.get("id") or "")
        group = str(badge.get("group") or "")
        rel = str((((badge.get("assets") or {}).get(asset_theme) or {}).get("96x40") or ""))
        pattern = str(badge.get("pattern") or "")
        name = str(badge.get("name") or badge.get("text") or badge_id)
        if not badge_id or not rel or not pattern or not name:
            raise RuntimeError(f"incomplete badge feed row: {badge_id or '<missing>'} {theme}")
        filters.append({
            "id": badge_id,
            "groupId": group,
            "name": name,
            "pattern": pattern,
            "imageURL": RAW_BASE + rel,
            "isEnabled": True,
            **style(theme, group),
        })
    return {"filters": filters, "groups": groups}


def normalize(*, apply: bool) -> list[str]:
    changed = []
    for theme, path in OUTPUTS.items():
        wanted = json.dumps(build(theme), ensure_ascii=False, indent=2) + "\n"
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if wanted != current:
            changed.append(theme)
            if apply:
                path.write_text(wanted, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")
    changed = normalize(apply=args.apply)
    if args.check and changed:
        raise SystemExit("badge feed normalization required: " + ",".join(changed))
    print("FIELD_BADGE_FEEDS changed=" + str(len(changed)) + " themes=dark,light,fusion native_style=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
