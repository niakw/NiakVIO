#!/usr/bin/env python3
"""Compatibility entry point for the canonical version-aware StreamBadge generator.

This helper must never implement an independent Fusion writer. Public feed versioning
is owned by normalize_badge_feeds.py, which updates latest aliases, creates the four
version-aligned immutable snapshots, and refuses to mutate an already-published vN.
"""
from __future__ import annotations

import argparse

from normalize_badge_feeds import PUBLIC_FEED_VERSION, build, normalize


def validate_fusion() -> None:
    payload = build("fusion")
    filters = payload.get("filters") or []
    groups = payload.get("groups") or []
    if not filters or not groups:
        raise ValueError("Fusion feed must contain filters and groups")
    for row in filters:
        if row.get("tagStyle") != "bordered":
            raise ValueError(f"Fusion badge style drift: {row.get('id')}")
        if "/assets/transparent/96x40/" not in str(row.get("imageURL") or ""):
            raise ValueError(f"Fusion badge must use transparent 96x40 artwork: {row.get('id')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")

    changed = normalize(apply=args.apply)
    validate_fusion()
    if args.check and changed:
        raise SystemExit("canonical StreamBadge normalization required: " + ",".join(changed))

    print(
        "FIELD_FUSION_BADGE_FEED "
        f"changed={len(changed)} public_v={PUBLIC_FEED_VERSION} "
        "canonical_generator=normalize_badge_feeds "
        f"stable=assets/stream-badges-fusion-v{PUBLIC_FEED_VERSION}.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
