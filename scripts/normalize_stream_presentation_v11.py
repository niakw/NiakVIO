#!/usr/bin/env python3
"""Durably enforce NiakVIO's unified stream presentation V11.

This is a Core-wide normalizer, never a provider-specific repair. It makes provider
stream descriptions input-only: technical facts may be extracted from them, but the
visible description is always rebuilt by Core from stream facts plus safe TMDB media
context. The technical line remains visible so official Nuvio StreamBadge matchers can
render image badges; without StreamBadge the same line is the emoji fallback.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
CATALOG = ROOT / "assets/badge_catalog_v2_complete.json"
MAPPING = ROOT / "assets/mapping_core_brain_ui_v2_complete.json"
ASSET_README = ROOT / "assets/README.txt"
MOCKUP = ROOT / "assets/docs/MAQUETTE_EXEMPLE_FLUX_UNIQUE.txt"
DARK_FEED = ROOT / "assets/stream-badges-dark.json"
LIGHT_FEED = ROOT / "assets/stream-badges-light.json"

OLD_REV = "all-providers-facts-badge-dedupe-tmdb-fallback-v10"
REVISION = "all-providers-forced-description-badge-emoji-tmdb-v11"


def _region(src: str, start: str, end: str, replacement: str) -> str:
    a = src.find(start)
    if a < 0:
        raise ValueError(f"missing stream-presentation start anchor: {start}")
    b = src.find(end, a)
    if b < 0:
        raise ValueError(f"missing stream-presentation end anchor: {end}")
    return src[:a] + replacement + src[b:]


def _normalize_core(text: str) -> str:
    if REVISION in text:
        return text
    if OLD_REV not in text:
        raise ValueError("stream-presentation revision anchor is neither V10 nor V11")

    text = text.replace(
        "Important presentation rule: a technical fact represented by a badge is NOT repeated\n"
        "in user-facing title/description/size. Structured facts remain available to runtimes\n"
        "and badge renderers. Unknown quality/language/codec/source data is never invented.",
        "Presentation rule: provider descriptions are never authoritative UI. The Core always\n"
        "rebuilds them from provider/stream technical facts plus safe TMDB media context. The\n"
        "technical text stays visible so native StreamBadge matchers can render image badges;\n"
        "when native badges are disabled the same facts remain styled with emoji group markers.\n"
        "Unknown quality/language/codec/source data is never invented or displayed.",
    ).replace(OLD_REV, REVISION)

    text = _region(
        text,
        "function audio(r){",
        "function duration(r){",
        r'''function audioFacts(r){var u=(s(r&&r.audio)+" "+blob(r)).toUpperCase(),tech=[],codec="",ch="",cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(cm)ch=cm[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))tech.push("Dolby Atmos");if(/\bDTS[: ._-]?X\b/.test(u))tech.push("DTS:X");if(/\bTRUE[ ._-]?HD\b/.test(u))codec="TrueHD";else if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))codec="E-AC3";else if(/\bAC-?3\b/.test(u))codec="AC3";else if(/\bDTS[- ]?HD\b/.test(u))codec="DTS-HD";else if(/\bDTS\b/.test(u))codec="DTS";else if(/\bAAC\b/.test(u))codec="AAC";else if(meaningful(r&&r.audio)&&!tech.length)codec=s(r.audio);return{tech:uniq(tech),codec:codec,channels:ch}}
''',
    )
    text = _region(
        text,
        "function source(r){",
        "function formatType(r){",
        r'''function source(r){var raw=(s(r&&r.sourceType)+" "+s(r&&r.releaseType)+" "+blob(r)),u=raw.toUpperCase(),sourceType="",releaseType="";if(/\b(?:ULTRA[ ._-]?HD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BD)\b/.test(u))sourceType="ULTRA HD BLU-RAY";else if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))sourceType="BLU-RAY";else if(/\bWEB[- .]?DL\b/.test(u))sourceType="WEB-DL";else if(/\bWEB[- .]?RIP\b/.test(u))sourceType="WEBRIP";else if(/\bHDTV\b/.test(u))sourceType="HDTV";else if(/\bDVD[- .]?RIP\b/.test(u))sourceType="DVD RIP";if(/\bREMUX\b/.test(u))releaseType="REMUX";return{sourceType:sourceType||(meaningful(r&&r.sourceType)?s(r.sourceType):""),releaseType:releaseType||(meaningful(r&&r.releaseType)?s(r.releaseType):"")}}
''',
    )
    text = _region(
        text,
        "function badgeIds(f){",
        "function nativeFetchBridge(){",
        r'''function badgeIds(f){var ids=[];var q={"2160p":"4k-ultra-hd","1080p":"1080p-full-hd","720p":"720p-hd","480p":"480p-sd"}[f.quality];if(q)ids.push(q);var src={"ULTRA HD BLU-RAY":"uhd-blu-ray","BLU-RAY":"blu-ray-disc","WEB-DL":"webdl","WEBRIP":"webrip","HDTV":"hdtv","DVD RIP":"dvd-rip"}[f.sourceType];if(src)ids.push(src);if(f.releaseType==="REMUX")ids.push("remux");f.videoTech.forEach(function(v){var id={"Dolby Vision":"dolby-vision","HDR10+":"hdr10-plus","HDR10":"hdr10","IMAX Enhanced":"imax-enhanced","IMAX":"imax"}[v];if(id)ids.push(id)});var co={"HEVC":"hevc","AVC":"avc"}[f.codec];if(co)ids.push(co);if(f.bitDepth)ids.push(f.bitDepth);(f.audioTech||[]).forEach(function(v){var id={"Dolby Atmos":"dolby-atmos","DTS:X":"dts-x"}[v];if(id)ids.push(id)});var ac={"TrueHD":"truehd","E-AC3":"dolby-digital-plus","AC3":"dolby-digital","DTS-HD":"dts-hd-master-audio"}[f.audioCodec];if(ac)ids.push(ac);if(f.audioChannels==="7.1")ids.push("7.1");else if(f.audioChannels==="5.1")ids.push("5.1");var lg={"Multi":"multi","VFF":"vff","VFQ":"vfq","VO":"vo","VOSTFR":"vostfr"}[f.language];if(lg)ids.push(lg);f.subtitles.forEach(function(v){var id={"VOSTFR":"vostfr","SUB FR":"sub-fr","SUB EN":"sub-en","FORCED":"forced","SDH":"sdh-cc"}[v];if(id)ids.push(id)});return uniq(ids)}
function badgeLabels(f){var out=[];if(f.quality)out.push(f.quality==="2160p"?"4K":f.quality);if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);out=out.concat(f.audioTech||[]);if(f.audioCodec)out.push(f.audioCodec);if(f.audioChannels)out.push(f.audioChannels);if(f.language)out.push(f.language);out=out.concat(f.subtitles);if(f.duration)out.push(humanDuration(f.duration));if(f.ageRating)out.push(f.ageRating);return uniq(out)}
function humanDuration(v){v=Number(v)||0;if(v<=0)return"";var h=Math.floor(v/60),m=v%60;return h?h+"h"+String(m).padStart(2,"0"):v+"min"}
function brief(v){var x=s(v).replace(/\s+/g," ");return x.length>180?x.slice(0,177).replace(/\s+\S*$/,"")+"…":x}
function technicalLine(f,fs){var groups=[],video=[],audio=[],lang=[],misc=[];if(f.quality)video.push(f.quality);var src=f.sourceType+(f.releaseType?" "+f.releaseType:"");if(src)video.push(src);if(f.codec)video.push(f.codec+(f.bitDepth?" "+f.bitDepth:""));else if(f.bitDepth)video.push(f.bitDepth);video=video.concat(f.videoTech||[]);if(f.format)video.push(f.format);if(video.length)groups.push("🎞️ "+uniq(video).join(" • "));audio=audio.concat(f.audioTech||[]);if(f.audioCodec)audio.push(f.audioCodec);if(f.audioChannels)audio.push(f.audioChannels);if(audio.length)groups.push("🔊 "+uniq(audio).join(" • "));if(f.language)lang.push(f.language);(f.subtitles||[]).forEach(function(v){if(v&&lang.indexOf(v)<0)lang.push(v)});if(lang.length)groups.push("🌐 "+lang.join(" • "));if(f.duration)misc.push("⏱ "+humanDuration(f.duration));if(fs)misc.push("💾 "+fs);if(f.ageRating)misc.push("🔞 "+f.ageRating);if(misc.length)groups.push(misc.join(" • "));return groups.join("  |  ")}
''',
    )
    text = _region(
        text,
        "function present(r,meta,q){",
        "function install(o,k){",
        r'''function present(r,meta,q){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),au=audioFacts(r),so=source(r),vf=videoFacts(r),f={quality:quality(r),language:language(r),codec:codec(r),audioTech:au.tech,audioCodec:au.codec,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||""};f.subtitles=f.subtitles.filter(function(v){return v!==f.language});if(f.quality)out.quality=f.quality;if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;var audioCombined=uniq((f.audioTech||[]).concat([f.audioCodec,f.audioChannels].filter(Boolean))).join(" ");if(audioCombined)out.audio=audioCombined;if(f.duration)out.duration=f.duration;if(f.sourceType)out.sourceType=f.sourceType;if(f.releaseType)out.releaseType=f.releaseType;if(f.format)out.format=f.format;if(f.ageRating)out.ageRating=f.ageRating;out.badgeIds=badgeIds(f);out.displayBadges=badgeLabels(f);out.presentationFacts=f;var provider=providerName(r),media=mediaLine(meta,q),small=compact(meta,q),genres=meta&&Array.isArray(meta.genres)&&meta.genres.length?meta.genres.slice(0,3).join(", "):"",fs=fileSize(r),technical=technicalLine(f,fs),lines=[];if(media)lines.push(((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"📺 ":"🎬 ")+media+(genres?" • "+genres:""));if(technical)lines.push(technical);else if(meta&&meta.overview)lines.push("ℹ️ "+brief(meta.overview));if(!lines.length)lines.push("🎬 "+provider);out.title=small?provider+" • "+small:provider;out.name=provider;out.description=lines.join("\n");if(fs)out.size=fs;else if("size" in out)delete out.size;return out}
''',
    )
    return text


def _feed_payload(catalog: dict[str, Any], theme: str) -> dict[str, Any]:
    groups = [
        {"id": str(g.get("id") or ""), "name": str(g.get("name") or ""), "color": "", "isExpanded": True}
        for g in catalog.get("groups") or []
        if isinstance(g, dict)
    ]
    base = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"
    filters: list[dict[str, Any]] = []
    for badge in catalog.get("badges") or []:
        if not isinstance(badge, dict):
            continue
        rel = str((((badge.get("assets") or {}).get(theme) or {}).get("96x40") or ""))
        pattern = str(badge.get("pattern") or "")
        name = str(badge.get("name") or badge.get("text") or badge.get("id") or "")
        if not rel or not pattern or not name:
            raise ValueError(f"incomplete badge feed row: {badge.get('id')} {theme}")
        filters.append(
            {
                "id": str(badge.get("id") or ""),
                "groupId": str(badge.get("group") or ""),
                "name": name,
                "pattern": pattern,
                "imageURL": base + rel,
                "isEnabled": True,
                "tagColor": "",
                "tagStyle": "",
                "textColor": "",
                "borderColor": "",
            }
        )
    return {"filters": filters, "groups": groups}


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def normalize(*, apply: bool) -> list[str]:
    changed: list[str] = []

    current_core = CORE.read_text(encoding="utf-8")
    normalized_core = _normalize_core(current_core)
    if normalized_core != current_core:
        changed.append("global_stream_presentation_v11")
        if apply:
            CORE.write_text(normalized_core, encoding="utf-8")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    for theme, path in (("dark", DARK_FEED), ("light", LIGHT_FEED)):
        wanted = _json_text(_feed_payload(catalog, theme))
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        if current != wanted:
            changed.append(f"stream_badge_feed:{theme}")
            if apply:
                path.write_text(wanted, encoding="utf-8")

    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    wanted_mapping = json.loads(json.dumps(mapping))
    display = wanted_mapping.setdefault("display", {})
    display["alwaysReplaceProviderDescription"] = True
    display["nativeBadgeFeeds"] = {
        "dark_app_background": "assets/stream-badges-dark.json",
        "light_app_background": "assets/stream-badges-light.json",
    }
    display["fallbackWhenNativeBadgesDisabled"] = "emojiTechnicalLine"
    display["presentationSources"] = {
        "technicalTruth": "provider/stream facts",
        "mediaContextFallback": "TMDB",
    }
    rules = wanted_mapping.setdefault("rules", [])
    for rule in (
        "Always replace every provider-owned stream description with the shared Core presentation.",
        "When native StreamBadge rules are active, technical text provides matcher tokens for image badges.",
        "When native StreamBadge rules are inactive, emoji-grouped technical text remains the universal visual fallback.",
        "TMDB may fill media context, runtime and age rating, but never invent stream resolution/source/codec/audio/language facts.",
    ):
        if rule not in rules:
            rules.append(rule)
    if wanted_mapping != mapping:
        changed.append("mapping_core_brain_ui_v11")
        if apply:
            MAPPING.write_text(_json_text(wanted_mapping), encoding="utf-8")

    section = """
DUAL-MODE RUNTIME RULE
----------------------
NiakVIO always replaces provider-owned stream descriptions with the shared Core presentation.
Technical truth comes from provider/stream facts; TMDB fills only safe media context such as title/year/episode/genres/runtime/age when useful.

If native StreamBadge is active, import one of these feeds according to the Nuvio theme:
- assets/stream-badges-dark.json
- assets/stream-badges-light.json
The technical line deliberately keeps the matcher tokens so the official Nuvio StreamBadge renderer can show the real image assets.

If StreamBadge is inactive, the exact same description remains styled with emoji groups (🎞️ video, 🔊 audio, 🌐 language/subtitles, ⏱ duration, 💾 size, 🔞 age). No provider Unknown/private layout is allowed through.
"""
    readme = ASSET_README.read_text(encoding="utf-8")
    if "DUAL-MODE RUNTIME RULE" not in readme:
        changed.append("assets_readme_dual_mode")
        if apply:
            ASSET_README.write_text(readme.rstrip() + "\n" + section, encoding="utf-8")

    dual = """
RUNTIME DUAL-MODE
-----------------
- StreamBadge actif : les tokens de la ligne technique déclenchent les vrais badges image du feed dark/light.
- StreamBadge inactif : la ligne technique reste visible avec groupes emoji, par exemple :
  🎞️ 2160p • Ultra HD Blu-ray REMUX • HEVC 10-bit • Dolby Vision • IMAX Enhanced  |  🔊 Dolby Atmos • TrueHD • 7.1  |  🌐 VFF • VOSTFR
- Dans les deux modes, la description originale du provider est entièrement remplacée par le Core.
- TMDB enrichit uniquement le contexte média absent ; les faits techniques restent issus du flux/provider.
"""
    mock = MOCKUP.read_text(encoding="utf-8")
    if "RUNTIME DUAL-MODE" not in mock:
        changed.append("mockup_dual_mode")
        if apply:
            MOCKUP.write_text(mock.rstrip() + "\n" + dual, encoding="utf-8")

    return changed


def assert_contract() -> None:
    text = CORE.read_text(encoding="utf-8")
    if REVISION not in text:
        raise ValueError("stream presentation V11 is not materialized")
    for token in ("technicalLine(f,fs)", "out.description=lines.join", "audioFacts(r)", "ULTRA HD BLU-RAY"):
        if token not in text:
            raise ValueError(f"stream presentation V11 contract missing: {token}")
    for path in (DARK_FEED, LIGHT_FEED):
        if not path.is_file():
            raise ValueError(f"native StreamBadge feed missing: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not payload.get("filters") or not payload.get("groups"):
            raise ValueError(f"native StreamBadge feed incomplete: {path.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply and args.check:
        raise SystemExit("choose --apply or --check")
    changes = normalize(apply=args.apply)
    if args.check and changes:
        raise SystemExit("stream presentation V11 normalization required: " + ", ".join(changes))
    if args.apply:
        assert_contract()
    print(f"FIELD_STREAM_PRESENTATION_V11 changed={len(changes)} revision={REVISION}")
