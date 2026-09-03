#!/usr/bin/env python3
"""Validate the permanently materialized NiakVIO stream presentation V18.

Presentation code is canonical in global_stream_presentation_v1.py. This compatibility
entry point is read-only: it never rewrites Provider/Core bytes. Badge artwork and native
StreamBadge feeds remain owned exclusively by the badge-system materializer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
DARK_FEED = ROOT / "assets/stream-badges-dark.json"
LIGHT_FEED = ROOT / "assets/stream-badges-light.json"
FUSION_FEED = ROOT / "assets/stream-badges-fusion.json"
REVISION = "all-providers-standard-fields-url-facts-v18"


def normalize(*, apply: bool) -> list[str]:
    # ``apply`` is retained for compatibility only. V18 is a committed fixed point:
    # no hidden staging, formatting or one-shot rewrite is permitted during a build/test run.
    _ = apply
    text = CORE.read_text(encoding="utf-8")
    if REVISION not in text:
        raise ValueError(
            "stream presentation V18 source is not materialized; "
            "global_stream_presentation_v1.py must contain the canonical V18 source"
        )
    return []


def assert_contract() -> None:
    text = CORE.read_text(encoding="utf-8")
    for token in (
        REVISION,
        '"providerLanguageMode"',
        '"languageFallback"',
        '"MULTI (VF/VO)"',
        '"🇫🇷 "',
        '"🌐🇫🇷 "',
        '"🌐 "',
        '"VF":"vf"',
        'function urlFacts(r){',
        'r&&r.height',
        'FULL[ ._-]?HD|FHD',
        'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")',
        'out.description=lines.join("\\n")',
        'function tvDescriptionTunnel(){',
        'function streamPayload(v){',
        'function asciiJson(v){',
        'function installJvmSafeStreamStringify(){',
        'streamPayload(value)?asciiJson(raw):raw',
        'if(tvDescriptionTunnel()&&out.description)out.size=out.description',
    ):
        if token not in text:
            raise ValueError(f"stream presentation V18 contract missing: {token}")
    technical_start = text.find("function technicalLine(f,fs){")
    technical_end = text.find("function durationAgeLine(f){", technical_start)
    if technical_start < 0 or technical_end < 0:
        raise ValueError("stream presentation V18 technical line missing")
    if "f.quality" in text[technical_start:technical_end]:
        raise ValueError("quality must remain title-only")

    for path in (DARK_FEED, LIGHT_FEED, FUSION_FEED):
        if not path.is_file():
            raise ValueError(f"native StreamBadge feed missing: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("filters") or []
        if not rows or not payload.get("groups"):
            raise ValueError(f"native StreamBadge feed incomplete: {path.name}")
        for row in rows:
            if row.get("tagStyle") != "bordered":
                raise ValueError(f"native StreamBadge style drift: {path.name} {row.get('id')}")
            for key in ("tagColor", "borderColor", "textColor"):
                if not str(row.get(key) or "").startswith("#"):
                    raise ValueError(f"native StreamBadge {key} missing: {path.name} {row.get('id')}")
        ids = {str(row.get("id") or "") for row in rows}
        if not {"vf", "vff", "vfq", "vo", "vostfr", "multi"}.issubset(ids):
            raise ValueError(f"language badge set incomplete: {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")
    changed = normalize(apply=args.apply)
    if args.check and changed:
        raise SystemExit("stream presentation V18 validation drift: " + ", ".join(changed))
    if args.apply or args.check:
        assert_contract()
    print(f"FIELD_STREAM_PRESENTATION_V18 changed={len(changed)} revision={REVISION} badge_feeds=external_owner read_only=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
