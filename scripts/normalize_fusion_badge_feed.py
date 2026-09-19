#!/usr/bin/env python3
"""Build the account-level Fusion StreamBadge feed from the canonical badge generator.

Fusion is not a second styling implementation. It delegates to normalize_badge_feeds
so Dark, Light and Fusion always share the exact same group palette, native bordered
chrome and validation rules. Fusion uses transparent 96x40 artwork with a dark neutral
native chip, making the same account-level feed readable on light and dark app themes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from normalize_badge_feeds import build as build_theme

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/stream-badges-fusion.json"
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"
ASSET_THEME = "transparent"
ASSET_SIZE = "96x40"


def build() -> dict[str, Any]:
    payload = build_theme("fusion")
    filters = payload.get("filters") or []
    groups = payload.get("groups") or []
    if not filters or not groups:
        raise ValueError("Fusion feed must contain filters and groups")
    for row in filters:
        if row.get("tagStyle") != "bordered":
            raise ValueError(f"Fusion badge style drift: {row.get('id')}")
        if "/assets/transparent/96x40/" not in str(row.get("imageURL") or ""):
            raise ValueError(f"Fusion badge must use transparent 96x40 artwork: {row.get('id')}")
        for key in ("tagColor", "textColor", "borderColor"):
            if not str(row.get(key) or "").startswith("#"):
                raise ValueError(f"Fusion badge {key} missing: {row.get('id')}")
    return payload


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
        "native_style=bordered canonical_generator=normalize_badge_feeds "
        f"url={RAW_BASE}assets/stream-badges-fusion.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
