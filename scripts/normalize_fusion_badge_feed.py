#!/usr/bin/env python3
"""Build the single account-level Fusion Badge URL for Nuvio.

Nuvio account settings accept raw badge JSON URLs, but a rule has one imageURL and
cannot dynamically switch image assets when the app theme changes. NiakVIO therefore
uses the dark-chip 96x40 variants for the account-level Fusion feed: the contained
chip/border remains readable on both dark and light application backgrounds. The
separate dark/light feeds remain available for clients that can select by theme.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
OUTPUT = ROOT / "assets/stream-badges-fusion.json"
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"
ASSET_THEME = "dark"
ASSET_SIZE = "96x40"


def build() -> dict[str, Any]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    groups = [
        {
            "id": str(group.get("id") or ""),
            "name": str(group.get("name") or ""),
            "color": "",
            "isExpanded": True,
        }
        for group in (catalog.get("groups") or [])
        if isinstance(group, dict)
    ]
    filters: list[dict[str, Any]] = []
    for badge in catalog.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        badge_id = str(badge.get("id") or "")
        rel = str((((badge.get("assets") or {}).get(ASSET_THEME) or {}).get(ASSET_SIZE) or ""))
        pattern = str(badge.get("pattern") or "")
        name = str(badge.get("name") or badge.get("text") or badge_id)
        if not badge_id or not rel or not pattern or not name:
            raise ValueError(f"incomplete Fusion badge row: {badge_id or '<missing>'}")
        filters.append(
            {
                "id": badge_id,
                "groupId": str(badge.get("group") or ""),
                "name": name,
                "pattern": pattern,
                "imageURL": RAW_BASE + rel,
                "isEnabled": True,
                "tagColor": "",
                "tagStyle": "",
                "textColor": "",
                "borderColor": "",
            }
        )
    if len(filters) != len(catalog.get("badges") or []):
        raise ValueError("Fusion feed must cover the complete badge catalog")
    return {"filters": filters, "groups": groups}


def normalize(*, apply: bool) -> bool:
    wanted = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
    changed = current != wanted
    if changed and apply:
        OUTPUT.write_text(wanted, encoding="utf-8")
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
        raise SystemExit("Fusion badge feed normalization required")
    print(
        "FIELD_FUSION_BADGE_FEED "
        f"changed={int(changed)} theme={ASSET_THEME} size={ASSET_SIZE} "
        f"url={RAW_BASE}assets/stream-badges-fusion.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
