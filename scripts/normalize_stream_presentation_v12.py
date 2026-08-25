#!/usr/bin/env python3
"""Enforce NiakVIO's cross-client unified stream presentation V12.

Provider output is factual input only. V12 builds one Core presentation, preserves the
normalized quality field required by official Nuvio labels/sorting, and projects the
remaining canonical details through ``size`` because Mobile/Desktop and TV all retain
that field. Provider-owned descriptions never survive as visible UI.

The badge catalog is also normalized at its source: historical patterns carried one
extra escaping layer, so JSON consumers received ``\\b`` instead of regex ``\b``.
Feeds are regenerated from the corrected catalog and validated after JSON parsing.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
MAPPING = ROOT / "assets/mapping_core_brain_ui_v2_complete.json"
DARK_FEED = ROOT / "assets/stream-badges-dark.json"
LIGHT_FEED = ROOT / "assets/stream-badges-light.json"
FUSION_FEED = ROOT / "assets/stream-badges-fusion.json"
OLD_CORE_REVISION = "all-providers-client-projected-badge-emoji-tmdb-v12"
REVISION = "all-providers-client-projected-quality-preserved-badge-emoji-tmdb-v12"
RAW_BASE = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _region(src: str, start: str, end: str, replacement: str) -> str:
    a = src.find(start)
    if a < 0:
        raise ValueError(f"missing V12 start anchor: {start}")
    b = src.find(end, a)
    if b < 0:
        raise ValueError(f"missing V12 end anchor: {end}")
    return src[:a] + replacement + src[b:]


def _normalize_core(text: str) -> str:
    if REVISION in text:
        return text
    if OLD_CORE_REVISION not in text:
        raise ValueError("stream presentation source is neither expected V12 revision")

    text = text.replace(OLD_CORE_REVISION, REVISION)
    text = text.replace(
        "mirrors the canonical presentation into ``size`` and clears the legacy quality/language\n"
        "transport fields after retaining their real values in ``presentationFacts``. This is a\n"
        "client-compatibility projection, not a provider-specific presentation fork.",
        "preserves normalized ``quality`` for official Nuvio labels/sorting and mirrors the\n"
        "remaining canonical multiline details into ``size``. ``language`` is transported inside\n"
        "that envelope to avoid duplicate client formatting. This is a client-compatibility\n"
        "projection, not a provider-specific presentation fork.",
    )
    text = text.replace(
        '"clientProjection": "description+size-envelope;quality-language-suppressed",',
        '"clientProjection": "quality-preserved;size-multiline-envelope;language-suppressed",',
    )

    text = _region(
        text,
        "function providerName(r){",
        "function fileSize(r){",
        r'''function providerName(r){var id=s(c.providerId).replace(/[-_]+/g," ");if(id)return id.replace(/\b\w/g,function(x){return x.toUpperCase()});var raw=first(r&&r.provider);return raw&&raw.length<=48?raw:"Source"}
''',
    )
    text = _region(
        text,
        "function fileSize(r){",
        "function badgeIds(f){",
        r'''function fileSize(r){var values=[r&&r.fileSize,r&&r.filesize,r&&r.size];for(var i=0;i<values.length;i++){var v=s(values[i]),m=v.match(/\b\d+(?:[.,]\d+)?\s*(?:KB|MB|GB|TB)\b/i);if(m)return m[0].replace(/\s+/g," ").trim()}return""}
''',
    )
    text = _region(
        text,
        "function technicalLine(f,fs){",
        "function nativeFetchBridge(){",
        r'''function technicalLines(f,fs,includeQuality){var lines=[],video=[],audio=[],lang=[],misc=[];if(includeQuality&&f.quality)video.push(f.quality);var src=f.sourceType+(f.releaseType?" "+f.releaseType:"");if(src)video.push(src);if(f.codec)video.push(f.codec+(f.bitDepth?" "+f.bitDepth:""));else if(f.bitDepth)video.push(f.bitDepth);video=video.concat(f.videoTech||[]);if(f.format)video.push(f.format);if(video.length)lines.push("🎞️ "+uniq(video).join(" • "));audio=audio.concat(f.audioTech||[]);if(f.audioCodec)audio.push(f.audioCodec);if(f.audioChannels)audio.push(f.audioChannels);if(audio.length)lines.push("🔊 "+uniq(audio).join(" • "));if(f.language)lang.push(f.language);(f.subtitles||[]).forEach(function(v){if(v&&lang.indexOf(v)<0)lang.push(v)});if(lang.length)lines.push("🌐 "+lang.join(" • "));if(f.duration)misc.push("⏱ "+humanDuration(f.duration));if(fs)misc.push("💾 "+fs);if(f.ageRating)misc.push("🔞 "+f.ageRating);if(misc.length)lines.push(misc.join(" • "));return lines}
''',
    )
    text = _region(
        text,
        "function present(r,meta,q){",
        "function install(o,k){",
        r'''function present(r,meta,q){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),au=audioFacts(r),so=source(r),vf=videoFacts(r),fs=fileSize(r),f={quality:quality(r),language:language(r),codec:codec(r),audioTech:au.tech,audioCodec:au.codec,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||"",fileSize:fs};f.subtitles=f.subtitles.filter(function(v){return v!==f.language});var audioCombined=uniq((f.audioTech||[]).concat([f.audioCodec,f.audioChannels].filter(Boolean))).join(" ");if(f.quality)out.quality=f.quality;else if("quality" in out)delete out.quality;if("language" in out)delete out.language;if(f.codec)out.codec=f.codec;var audioCombined=uniq((f.audioTech||[]).concat([f.audioCodec,f.audioChannels].filter(Boolean))).join(" ");if(audioCombined)out.audio=audioCombined;if(f.duration)out.duration=f.duration;if(f.sourceType)out.sourceType=f.sourceType;if(f.releaseType)out.releaseType=f.releaseType;if(f.format)out.format=f.format;if(f.ageRating)out.ageRating=f.ageRating;if(fs)out.fileSize=fs;out.badgeIds=badgeIds(f);out.displayBadges=badgeLabels(f);out.presentationFacts=f;var provider=providerName(r),media=mediaLine(meta,q),small=compact(meta,q),genres=meta&&Array.isArray(meta.genres)&&meta.genres.length?meta.genres.slice(0,3).join(", "):"",mediaText=media?(((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"📺 ":"🎬 ")+media+(genres?" • "+genres:"")):"",canonical=[],compat=[];if(mediaText){canonical.push(mediaText);compat.push(mediaText)}canonical=canonical.concat(technicalLines(f,fs,true));compat=compat.concat(technicalLines(f,fs,false));if(!canonical.length&&meta&&meta.overview)canonical.push("ℹ️ "+brief(meta.overview));if(!compat.length&&meta&&meta.overview)compat.push("ℹ️ "+brief(meta.overview));if(!canonical.length)canonical.push("🎬 "+provider);if(!compat.length)compat.push("🎬 "+provider);var visible=canonical.join("\n"),envelope=compat.join("\n");out.title=small?provider+" • "+small:provider;out.name=provider;out.description=visible;out.size=envelope;out.nuvioPresentation=visible;out.nuvioCompatibilityEnvelope=envelope;return out}
''',
    )
    return text


def _normalize_catalog_patterns(catalog: dict[str, Any]) -> tuple[dict[str, Any], int]:
    normalized = json.loads(json.dumps(catalog))
    changed = 0
    for badge in normalized.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        pattern = str(badge.get("pattern") or "")
        # Historical catalog JSON encoded every regex backslash twice. After JSON
        # parsing that leaves two backslashes where regex engines require one.
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
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"invalid badge regex: {badge_id}: {exc}") from exc
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

    current_core = CORE.read_text(encoding="utf-8")
    normalized_core = _normalize_core(current_core)
    if normalized_core != current_core:
        changed.append("global_stream_presentation_v12")
        if apply:
            CORE.write_text(normalized_core, encoding="utf-8")

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
        "preservedLegacyFields": ["quality"],
        "suppressedLegacyRecompositionFields": ["language"],
        "structuredFactsField": "presentationFacts",
        "mobileDesktopSubtitle": "quality + multiline size envelope",
        "tvTitle": "provider + quality",
        "tvDescription": "multiline size envelope",
    }
    display["nativeBadgeFeeds"] = {
        "recommended": "assets/stream-badges-fusion.json",
        "dark_app_background": "assets/stream-badges-dark.json",
        "light_app_background": "assets/stream-badges-light.json",
        "requiresNuvioImport": True,
    }
    display["fallbackWhenNativeBadgesDisabled"] = "multilineEmojiTechnicalGroups"
    display["presentationSources"] = {
        "technicalTruth": "provider/stream facts",
        "mediaContextFallback": "TMDB",
    }
    rules = wanted_mapping.setdefault("rules", [])
    for rule in (
        "Provider-owned presentation text is input-only; Core rebuilds the visible stream presentation.",
        "V12 preserves normalized quality because official Nuvio clients use it for stream labels/sorting.",
        "V12 mirrors complementary multiline presentation into size because official Nuvio plugin readers preserve size on Mobile, Desktop and TV.",
        "V12 suppresses transport language after preserving it in presentationFacts and the multiline envelope to prevent duplicate client formatting.",
        "Native StreamBadge image rules require import in Nuvio settings; canonical text remains the matcher and multiline emoji fallback.",
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
        "function technicalLines(f,fs,includeQuality)",
        'if(f.quality)out.quality=f.quality;else if("quality" in out)delete out.quality',
        'if("language" in out)delete out.language',
        "out.description=visible;out.size=envelope",
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
        raise ValueError("badge catalog still contains an extra regex escaping layer")
    expected = len(catalog.get("badges") or [])
    for badge in catalog.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        pattern = str(badge.get("pattern") or "")
        if "\\\\" in pattern:
            raise ValueError(f"badge catalog regex still contains doubled backslash: {badge.get('id')}")
        re.compile(pattern)

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
            re.compile(pattern)


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
