#!/usr/bin/env python3
"""Enforce NiakVIO's cross-client unified stream presentation V12.

V12 keeps one provider-agnostic Core presentation while projecting it through the
legacy fields actually preserved by official Nuvio plugin readers. It also maintains
badge feeds whose regexes match the same canonical visible text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
MAPPING = ROOT / "assets/mapping_core_brain_ui_v2_complete.json"
DARK_FEED = ROOT / "assets/stream-badges-dark.json"
LIGHT_FEED = ROOT / "assets/stream-badges-light.json"
FUSION_FEED = ROOT / "assets/stream-badges-fusion.json"
REVISION = "all-providers-client-projected-badge-emoji-tmdb-v12"
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _normalize_catalog_patterns(catalog: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Collapse the historical double escaping that made Nuvio regexes literal.

    The source catalog accidentally stored two backslash characters for regex escapes
    such as ``\\b``. JSON then serialized both, and the official Kotlin/Java regex
    engines received ``\\\\b`` (a literal backslash plus ``b``) instead of a word
    boundary. A single collapse is enough and leaves already-correct patterns intact.
    """
    normalized = json.loads(json.dumps(catalog))
    changed = 0
    for badge in normalized.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        pattern = str(badge.get("pattern") or "")
        fixed = pattern.replace("\\\\", "\\")
        if fixed != pattern:
            badge["pattern"] = fixed
            changed += 1
    return normalized, changed


def _feed_payload(catalog: dict[str, Any], theme: str) -> dict[str, Any]:
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
        name = str(badge.get("name") or badge.get("text") or badge_id)
        pattern = str(badge.get("pattern") or "")
        rel = str((((badge.get("assets") or {}).get(theme) or {}).get("96x40") or ""))
        if not badge_id or not name or not pattern or not rel:
            raise ValueError(f"incomplete badge feed row: {badge_id or '<missing>'} theme={theme}")
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
        raise ValueError("badge feed must cover the complete catalog")
    return {"filters": filters, "groups": groups}


def normalize(*, apply: bool) -> list[str]:
    changed: list[str] = []
    core = CORE.read_text(encoding="utf-8")
    if REVISION not in core:
        raise ValueError(
            "V12 Core source is not materialized; presentation normalizer refuses to "
            "silently reconstruct security-sensitive provider wrappers"
        )

    raw_catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog, pattern_changes = _normalize_catalog_patterns(raw_catalog)
    if pattern_changes:
        changed.append(f"badge_catalog_regex_escaping:{pattern_changes}")
        if apply:
            CATALOG.write_text(_json_text(catalog), encoding="utf-8")

    for theme, path in (("dark", DARK_FEED), ("light", LIGHT_FEED), ("dark", FUSION_FEED)):
        wanted = _json_text(_feed_payload(catalog, theme))
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current != wanted:
            changed.append(f"stream_badge_feed:{path.name}")
            if apply:
                path.write_text(wanted, encoding="utf-8")

    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    wanted_mapping = json.loads(json.dumps(mapping))
    display = wanted_mapping.setdefault("display", {})
    display["alwaysReplaceProviderDescription"] = True
    display["presentationRevision"] = "global_core_v12"
    display["clientProjection"] = {
        "canonicalVisibleField": "description",
        "compatibilityEnvelopeField": "size",
        "suppressedLegacyRecompositionFields": ["quality", "language"],
        "structuredFactsField": "presentationFacts",
        "mobileDesktopSubtitle": "quality + size + language => size only after V12 suppression",
        "tvDescription": "size",
    }
    display["nativeBadgeFeeds"] = {
        "recommended": "assets/stream-badges-fusion.json",
        "dark_app_background": "assets/stream-badges-dark.json",
        "light_app_background": "assets/stream-badges-light.json",
        "requiresNuvioImport": True,
    }
    display["fallbackWhenNativeBadgesDisabled"] = "emojiTechnicalLine"
    display["presentationSources"] = {
        "technicalTruth": "provider/stream facts",
        "mediaContextFallback": "TMDB",
    }
    rules = wanted_mapping.setdefault("rules", [])
    for rule in (
        "Provider-owned presentation text is input-only; Core rebuilds the visible stream presentation.",
        "V12 mirrors the canonical presentation into size because official Nuvio plugin readers preserve size on Mobile, Desktop and TV.",
        "V12 clears transport quality/language after preserving their truth in presentationFacts to prevent client-side duplicate formatting.",
        "Native StreamBadge image rules require import in Nuvio settings; canonical text remains the matcher and emoji fallback.",
        "TMDB may fill media context, runtime and age rating, but never invent stream resolution/source/codec/audio/language facts.",
    ):
        if rule not in rules:
            rules.append(rule)
    if wanted_mapping != mapping:
        changed.append("mapping_core_brain_ui_v12")
        if apply:
            MAPPING.write_text(_json_text(wanted_mapping), encoding="utf-8")
    return changed


def assert_contract() -> None:
    text = CORE.read_text(encoding="utf-8")
    required = (
        REVISION,
        "function technicalLine(f,fs)",
        'out.description=visible;out.size=visible;out.quality="";out.language=""',
        "presentationFacts=f",
        "sourceLabel",
        "behaviorHints",
        "tmdbJson(url)",
    )
    for token in required:
        if token not in text:
            raise ValueError(f"stream presentation V12 contract missing: {token}")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    normalized_catalog, pattern_changes = _normalize_catalog_patterns(catalog)
    if pattern_changes or normalized_catalog != catalog:
        raise ValueError("badge catalog still contains over-escaped regex patterns")
    expected = len(catalog.get("badges") or [])
    for path in (FUSION_FEED, DARK_FEED, LIGHT_FEED):
        if not path.is_file():
            raise ValueError(f"native StreamBadge feed missing: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        filters = payload.get("filters") or []
        groups = payload.get("groups") or []
        if len(filters) != expected or not groups:
            raise ValueError(f"native StreamBadge feed incomplete: {path.name}")
        for row in filters:
            pattern = str(row.get("pattern") or "")
            if not pattern or "\\\\" in pattern or not row.get("imageURL"):
                raise ValueError(f"native StreamBadge feed row invalid: {path.name} {row.get('id')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")
    changes = normalize(apply=args.apply)
    if args.check and changes:
        raise SystemExit("stream presentation V12 normalization required: " + ", ".join(changes))
    if args.apply or not changes:
        assert_contract()
    print(f"FIELD_STREAM_PRESENTATION_V12 changed={len(changes)} revision={REVISION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
