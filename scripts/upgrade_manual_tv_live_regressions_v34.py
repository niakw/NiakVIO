#!/usr/bin/env python3
"""V34: generic fixes proven by the exact 2026-09-12 manual-TV live matrix.

This migration owns no provider-specific fixture rule. It tightens three shared
contracts:
1. presentation uses the strongest explicit quality and detailed language fact;
2. learned API routes with a literal movie/tv discriminator must match the
   requested transport namespace;
3. the terminal stream sanitizer selects V8, where only positive media proof is
   publishable (unknown/network probe outcomes fail closed).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
PROVIDER_BASE = ROOT / "scripts/provider_base_store.py"
COMPOSITOR = ROOT / "scripts/apply_provider_overrides.py"


def function_span(text: str, name: str) -> tuple[int, int]:
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        raise AssertionError(f"missing JS function {name}")
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote = ""
    escaped = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch in "\r\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
        else:
            if ch in "'\"`":
                quote = ch
            elif ch == "/" and nxt == "/":
                line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                block_comment = True
                i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise AssertionError(f"unterminated JS function {name}")


def replace_function(text: str, name: str, replacement: str) -> str:
    start, end = function_span(text, name)
    return text[:start] + replacement.strip() + text[end:]


def patch_presentation() -> bool:
    text = PRESENTATION.read_text(encoding="utf-8")
    before = text
    text = text.replace(
        'REVISION = "all-providers-client-projection-language-detail-v21"',
        'REVISION = "all-providers-client-projection-strongest-evidence-v22"',
    )
    quality = r'''
function quality(r){
  var u=blob(r).toUpperCase(),best=0,m,re=/\b(2160|1440|1080|720|576|540|480|360)P?\b/g;
  if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))best=2160;
  while((m=re.exec(u))!==null)best=Math.max(best,Number(m[1]||0));
  if(/\b(?:FULL[ ._-]?HD|FHD)\b/.test(u))best=Math.max(best,1080);
  if(/\bHD\b/.test(u))best=Math.max(best,720);
  if(/\bSD\b/.test(u))best=Math.max(best,480);
  var h=Number(r&&r.height||0);if(h>=2000)best=Math.max(best,2160);else if(h>=1350)best=Math.max(best,1440);else if(h>=900)best=Math.max(best,1080);else if(h>=650)best=Math.max(best,720);else if(h>=450)best=Math.max(best,480);
  return best?String(best)+"p":"";
}
'''
    detailed = r'''
function detailedLanguage(r,fallback){
  var raw=s(r&&r.language),all=[raw,r&&r.name,r&&r.title,r&&r.label,r&&r.sourceLabel,r&&r.audio].map(s).join(" ").toLowerCase().replace(/[_-]+/g," ").replace(/\s+/g," ").trim();
  var aliases=[["malayalam","Malayalam"],["kannada","Kannada"],["bengali","Bengali"],["punjabi","Punjabi"],["gujarati","Gujarati"],["japanese","Japanese"],["english","English"],["telugu","Telugu"],["marathi","Marathi"],["korean","Korean"],["hindi","Hindi"],["tamil","Tamil"],["urdu","Urdu"],["ml","Malayalam"],["kn","Kannada"],["bn","Bengali"],["pa","Punjabi"],["gu","Gujarati"],["ja","Japanese"],["jpn","Japanese"],["en","English"],["eng","English"],["te","Telugu"],["mr","Marathi"],["ko","Korean"],["kor","Korean"],["hi","Hindi"],["ta","Tamil"],["ur","Urdu"]];
  for(var i=0;i<aliases.length;i++){var token=aliases[i][0].replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),rx=new RegExp("(?:^|[^a-z])"+token+"(?:[^a-z]|$)","i");if(rx.test(all))return aliases[i][1]}
  var u=raw.toLowerCase().replace(/[_-]+/g," ").replace(/\s+/g," ").trim();
  if(/^(?:vf|vff|vfq|vostfr|vo|multi|multi audio|dual audio)$/i.test(u))return fallback||raw.toUpperCase();
  if(meaningful(raw)&&raw.length<=32&&/^[A-Za-zÀ-ÿ .()/-]+$/.test(raw))return raw;
  return fallback||"";
}
'''
    text = replace_function(text, "quality", quality)
    text = replace_function(text, "detailedLanguage", detailed)
    if text != before:
        PRESENTATION.write_text(text, encoding="utf-8")
        return True
    return False


def patch_provider_base() -> bool:
    text = PROVIDER_BASE.read_text(encoding="utf-8")
    before = text
    learned = r'''
function _spv34RouteMediaCompatible(route, mediaType) {
  const desired = _mediaNamespace(mediaType);
  const source = _text(route);
  const match = source.match(/(?:[?&](?:type|media|m)=)(movie|tv|series|anime)(?=&|#|$)/i);
  if (!match) return true;
  let actual = _text(match[1]).toLowerCase();
  if (actual === "series" || actual === "anime") actual = "tv";
  return actual === desired;
}
function _learnedUrls(kind, meta, mediaType, season, episode) {
  const out = [];
  const bases = kind === "api" ? _apiBases() : _searchBases();
  for (const route of NIAKVIO_PROVIDER_MODEL.routes || []) {
    if (_routeKind(route) !== kind) continue;
    /* NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34 */
    if (kind === "api" && !_spv34RouteMediaCompatible(route, mediaType)) continue;
    out.push(..._expandLearnedRoute(route, meta, mediaType, season, episode, bases));
  }
  return _uniq(out);
}
'''
    text = replace_function(text, "_learnedUrls", learned)
    if text != before:
        PROVIDER_BASE.write_text(text, encoding="utf-8")
        return True
    return False


def patch_compositor() -> bool:
    text = COMPOSITOR.read_text(encoding="utf-8")
    before = text
    text = text.replace(
        '# NUVIO_STREAM_SANITIZER_V7_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v7.py"',
        '# NUVIO_STREAM_SANITIZER_V8_SELECTION\nGLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"',
    )
    v7_line = '    "scripts/provider_patches/stream_output_sanitizer_v7.py",\n'
    v8_line = '    "scripts/provider_patches/stream_output_sanitizer_v8.py",\n'
    if v8_line not in text:
        if v7_line not in text:
            raise AssertionError("sanitizer V7 managed-script anchor missing")
        text = text.replace(v7_line, v7_line + v8_line, 1)
    marker = '    "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7",\n'
    marker8 = '    "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8",\n'
    if marker8 not in text:
        if marker not in text:
            raise AssertionError("sanitizer V7 generated-tail marker anchor missing")
        text = text.replace(marker, marker + marker8, 1)
    if text != before:
        COMPOSITOR.write_text(text, encoding="utf-8")
        return True
    return False


def validate() -> None:
    presentation = PRESENTATION.read_text(encoding="utf-8")
    base = PROVIDER_BASE.read_text(encoding="utf-8")
    compositor = COMPOSITOR.read_text(encoding="utf-8")
    required = (
        (presentation, "strongest-evidence-v22"),
        (presentation, 'best=Math.max(best,Number(m[1]||0))'),
        (presentation, '["hindi","Hindi"]'),
        (base, "NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34"),
        (base, '_spv34RouteMediaCompatible(route, mediaType)'),
        (compositor, "NUVIO_STREAM_SANITIZER_V8_SELECTION"),
        (compositor, "stream_output_sanitizer_v8.py"),
        (compositor, "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8"),
    )
    for source, needle in required:
        if needle not in source:
            raise AssertionError(f"V34 missing {needle}")
    generic_window = base[base.index("NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34") - 800:base.index("NIAKVIO_PROVIDER_ROUTE_MEDIA_COMPAT_V34") + 800].casefold()
    for forbidden in ("moviebox", "hindmoviez", "castle", "interstellar", "ragna", "hell mode"):
        if forbidden in generic_window:
            raise AssertionError(f"fixture/provider-specific route rule leaked: {forbidden}")


def main() -> int:
    changed = {
        "presentation": patch_presentation(),
        "providerBase": patch_provider_base(),
        "compositor": patch_compositor(),
    }
    validate()
    print("MANUAL_TV_LIVE_REGRESSIONS_V34_OK " + " ".join(f"{k}={str(v).lower()}" for k, v in changed.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
