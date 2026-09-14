#!/usr/bin/env python3
"""Validate the permanently materialized NiakVIO stream presentation source.

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
REVISION_V22 = "all-providers-client-projection-strongest-evidence-v22"
REVISION_V23 = "all-providers-client-projection-language-roles-v23"
SUPPORTED_REVISIONS = (REVISION_V23, REVISION_V22)


def active_revision(text: str) -> str | None:
    return next((revision for revision in SUPPORTED_REVISIONS if revision in text), None)


def normalize(*, apply: bool) -> list[str]:
    # ``apply`` is retained for compatibility only. Presentation is a committed
    # fixed point: no hidden staging/formatting rewrite is permitted in builds.
    _ = apply
    text = CORE.read_text(encoding="utf-8")
    if not active_revision(text):
        raise ValueError(
            "supported stream presentation source is not materialized; "
            "global_stream_presentation_v1.py must contain canonical V22 or V23 source"
        )
    return []


def assert_contract() -> None:
    text = CORE.read_text(encoding="utf-8")
    revision = active_revision(text)
    if not revision:
        raise ValueError("stream presentation revision missing")
    common = (
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
        'var languageDetailValue=detailedLanguage(r,f.language);',
        'out.name=out.title',
        'out.description=lines.join("\\n")',
        'function streamPayload(v){',
        'function asciiJson(v){',
        'function installJvmSafeStreamStringify(){',
        'streamPayload(value)?asciiJson(raw):raw',
        'if(out.description)out.size=out.description',
    )
    for token in (revision, *common):
        if token not in text:
            raise ValueError(f"stream presentation contract missing for {revision}: {token}")

    if revision == REVISION_V23:
        for token in (
            'function languageTracks(r,meta){',
            'function compactTrack(t){',
            'function fullTrack(t){',
            'out.originalLanguage=f.originalLanguage||null',
            'out.languageTracks=f.languageTracks||[]',
            'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"");out.name=out.title',
        ):
            if token not in text:
                raise ValueError(f"stream presentation V23 contract missing: {token}")
        if '+(languageDetailValue?" - "+languageDetailValue:"")' in text:
            raise ValueError("stream presentation V23 title must not append language detail")
    else:
        token = 'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")+(languageDetailValue?" - "+languageDetailValue:"")'
        if token not in text:
            raise ValueError(f"stream presentation V22 contract missing: {token}")

    technical_start = text.find("function technicalLine(f,fs){")
    technical_end = text.find("function durationAgeLine(f){", technical_start)
    if technical_start < 0 or technical_end < 0:
        raise ValueError("stream presentation technical line missing")
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
        raise SystemExit("stream presentation validation drift: " + ", ".join(changed))
    if args.apply or args.check:
        assert_contract()
    text = CORE.read_text(encoding="utf-8")
    revision = active_revision(text) or "missing"
    print(f"FIELD_STREAM_PRESENTATION changed={len(changed)} revision={revision} badge_feeds=external_owner read_only=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
