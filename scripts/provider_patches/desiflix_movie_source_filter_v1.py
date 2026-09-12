#!/usr/bin/env python3
"""DesiFlix provider-local pre-Core movie source selector.

This Lego is neutral unless configured with movieAllowContains. It wraps the
provider-owned JSON runtime before shared Core composition, so diagnostics and
future evidence-backed source selection can exclude unstable terminals before
Core spends its bounded probe budget. TV is never filtered here.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.DESIFLIX.MOVIE_SOURCE_FILTER.V1"
MARKER = "NIAKVIO_DESIFLIX_MOVIE_SOURCE_FILTER_V1"

WRAPPER = r'''
/* NIAKVIO_DESIFLIX_MOVIE_SOURCE_FILTER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function mediaType(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var t=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();if(t==="series")t="tv";return t}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioDesiMovieSourceFilterV1)return false;var native=o[k];var fn=async function(){var rows=await native.apply(this,arguments);if(!Array.isArray(rows)||mediaType(arguments)!=="movie")return rows;var allow=Array.isArray(c.movieAllowContains)?c.movieAllowContains:[];if(!allow.length)return rows;return rows.filter(function(row){var u=s(row&&row.url).toLowerCase();for(var i=0;i<allow.length;i++)if(u.indexOf(String(allow[i]).toLowerCase())>=0)return true;return false})};fn.__niakvioDesiMovieSourceFilterV1=true;fn.__niakvioOriginal=native;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    allow = []
    for raw in cfg.get("movieAllowContains") or []:
        value = str(raw or "").strip().lower()
        if value and value not in allow:
            allow.append(value)
    payload = {"movieAllowContains": allow[:12]}
    js = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtime": payload,
            "scope": "desiflix-movie-only-pre-core",
            "tvUnchanged": True,
            "sharedCoreUnchanged": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
