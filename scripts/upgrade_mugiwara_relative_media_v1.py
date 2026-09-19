#!/usr/bin/env python3
"""Upgrade Mugiwara packed media handling and semantic fallback authority."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "mugiwarastream_packed_runtime_v1.py"
MARKER = "NIAKVIO_MUGIWARA_RELATIVE_PACKED_MEDIA_V1"
FALLBACK_MARKER = "NIAKVIO_MUGIWARA_SPECIALIZED_FALLBACK_PRIORITY_V1"
SEMANTIC_MARKER = "NIAKVIO_MUGIWARA_TV_TRANSPORT_IS_ANIME_V1"

NEW_MEDIA = r'''  function media(src,base){var full=s(src),pos=0;for(var i=0;i<8;i++){var r=unpackOne(full,pos);if(!r)break;full+="\n"+r.decoded;pos=r.next}full=full.replace(/\\\//g,"/").replace(/&amp;/g,"&").replace(/&quot;/g,'"');var out=[],seen={};function add(raw){var u=s(raw).replace(/[),\];}]+$/g,"");if(!u)return;if(u.indexOf("//")===0)u="https:"+u;else if(u.charAt(0)==="/"&&base){try{u=new URL(u,base).toString()}catch(_e){return}}if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u)}var m,re=/https?:\/\/[^\s"'<>\\]+(?:\.m3u8|\/hls2\/|\/master\.m3u8)[^\s"'<>\\]*/gi;while((m=re.exec(full))!==null)add(m[0]);var rel=/["'](\/[^\s"'<>\\]+(?:\.m3u8|\/hls2\/|\/master\.m3u8)[^\s"'<>\\]*)["']/gi;while((m=rel.exec(full))!==null)add(m[1]);return out}'''

OLD_RESOLVE_TAIL = "if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;if(!pageUrl)return[];return await fallback(pageUrl,q)"
NEW_RESOLVE_TAIL = (
    "/* " + FALLBACK_MARKER + " */"
    "if(pageUrl){var specialized=await fallback(pageUrl,q);"
    "if(Array.isArray(specialized)&&specialized.length)return specialized}"
    "if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;return[]"
)
OLD_SEMANTIC = 'if(type==="series")type="tv";if(type!=="anime"&&type!=="movie")return null;'
NEW_SEMANTIC = (
    'if(type==="series")type="tv";'
    '/* ' + SEMANTIC_MARKER + ' */'
    'if(type==="tv")type="anime";'
    'if(type!=="anime"&&type!=="movie")return null;'
)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    if SEMANTIC_MARKER not in text:
        if OLD_SEMANTIC not in text:
            raise AssertionError("Mugiwara semantic transport boundary not found")
        text = text.replace(OLD_SEMANTIC, NEW_SEMANTIC, 1)
        changed = True

    if MARKER not in text:
        start = text.find("  function media(src){")
        end = text.find("\n  async function proveHls", start)
        if start < 0 or end < 0:
            raise AssertionError("Mugiwara media decoder boundary not found")
        text = text[:start] + "  /* " + MARKER + " */\n" + NEW_MEDIA + text[end:]
        old = "var urls=media(p.text);"
        new = "var urls=media(p.text,p.url);"
        if old not in text:
            raise AssertionError("Mugiwara Smoothpre media call not found")
        text = text.replace(old, new, 1)
        changed = True

    if FALLBACK_MARKER not in text:
        if OLD_RESOLVE_TAIL not in text:
            raise AssertionError("Mugiwara native/fallback resolver tail not found")
        text = text.replace(OLD_RESOLVE_TAIL, NEW_RESOLVE_TAIL, 1)
        changed = True

    if changed:
        TARGET.write_text(text, encoding="utf-8")
    return changed


def validate() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if SEMANTIC_MARKER not in text or 'if(type==="tv")type="anime";' not in text:
        raise AssertionError("anime semantic transport normalization missing")
    if MARKER not in text:
        raise AssertionError("relative media marker missing")
    if "function media(src,base)" not in text or "media(p.text,p.url)" not in text:
        raise AssertionError("relative media resolver not active")
    if "new URL(u,base).toString()" not in text:
        raise AssertionError("relative media URL resolution missing")
    if FALLBACK_MARKER not in text:
        raise AssertionError("specialized fallback priority marker missing")
    if "if(pageUrl){var specialized=await fallback(pageUrl,q);" not in text:
        raise AssertionError("specialized fallback does not precede native output")


def main() -> int:
    changed = patch()
    validate()
    print(
        "MUGIWARA_RELATIVE_PACKED_MEDIA_V1_OK "
        f"changed={str(changed).lower()} semantic_anime_over_tv=true specialized_fallback_first=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
