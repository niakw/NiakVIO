#!/usr/bin/env python3
"""Harden stream presentation metadata fallbacks without changing its UI contract.

Keeps the existing provider-title/quality convention, icon lines, badge ordering,
and stream/provider technical precedence. Only placeholder cleanup is changed:
- strip trailing Unknown/Inconnue markers from provider labels;
- never render Unknown/Inconnue as the TMDB/request media title.

The TMDB Core capability remains responsible for filling media identity, duration
and age when provider/stream metadata is missing.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    old_provider = '''function providerName(r){var raw=meaningful(r&&r.name)?s(r.name):"",n=raw.split(/[|\\n]/)[0].trim(),u=n.toUpperCase(),looksTechnical=/(?:\\b4K\\b|\\b(?:2160|1440|1080|720|576|480)P?\\b|\\b(?:VF|VFF|VFQ|VOSTFR|VO|MULTI|DUAL[ -]?AUDIO)\\b|\\b(?:HEVC|AVC|H[ ._-]?26[45]|X26[45]|AV1|VP9)\\b|\\b(?:WEB[ ._-]?DL|WEB[ ._-]?RIP|BLU[ ._-]?RAY|REMUX|HDR|DOLBY|DTS)\\b)/.test(u);if(n&&n.length<=40&&!looksTechnical)return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\\b\\w/g,function(x){return x.toUpperCase()}):"Source"}'''
    new_provider = '''function cleanProviderLabel(v){var x=s(v).replace(/\\s*(?:[-|•:])\\s*(?:unknown|inconnue?|n\\/?a|null|undefined|none|-+)\\s*$/i,"").trim();return meaningful(x)?x:""}\nfunction providerName(r){var raw=cleanProviderLabel(r&&r.name),n=raw.split(/[|\\n]/)[0].trim(),u=n.toUpperCase(),looksTechnical=/(?:\\b4K\\b|\\b(?:2160|1440|1080|720|576|480)P?\\b|\\b(?:VF|VFF|VFQ|VOSTFR|VO|MULTI|DUAL[ -]?AUDIO)\\b|\\b(?:HEVC|AVC|H[ ._-]?26[45]|X26[45]|AV1|VP9)\\b|\\b(?:WEB[ ._-]?DL|WEB[ ._-]?RIP|BLU[ ._-]?RAY|REMUX|HDR|DOLBY|DTS)\\b)/.test(u);if(n&&n.length<=40&&!looksTechnical)return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\\b\\w/g,function(x){return x.toUpperCase()}):"Source"}'''
    if new_provider not in text:
        if text.count(old_provider) != 1:
            raise AssertionError("providerName presentation anchor drifted")
        text = text.replace(old_provider, new_provider, 1)
        changed = True

    old_media = '''function mediaLine(meta,q){var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0))parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));return parts.join(" • ")}'''
    new_media = '''function mediaLine(meta,q){var mt=meta&&meaningful(meta.title)?s(meta.title):"",qt=meaningful(q&&q.title)?s(q.title):"",title=mt||qt,year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0))parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));return parts.join(" • ")}'''
    if new_media not in text:
        if text.count(old_media) != 1:
            raise AssertionError("mediaLine presentation anchor drifted")
        text = text.replace(old_media, new_media, 1)
        changed = True

    # The established visual contract is intentionally untouched.
    required = (
        '"🎬 "+media',
        '"📺 "+media',
        '"⏱ "+humanDuration',
        '"🔞 "+f.ageRating',
        '"🇫🇷 "',
        '"🌐 "',
        'out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"")',
        'out.description=lines.join("\\n")',
        'out.badgeIds=badgeIds(f)',
        'out.displayBadges=badgeLabels(f)',
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise AssertionError(f"stream presentation UI contract drifted: {missing}")

    forbidden_render = (
        'parts.push("Unknown")',
        'parts.push("Inconnue")',
    )
    if any(needle in text for needle in forbidden_render):
        raise AssertionError("placeholder media text is hardcoded into presentation")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
    print(f"STREAM_PRESENTATION_METADATA_FALLBACKS_OK changed={str(changed).lower()} ui_contract=preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
