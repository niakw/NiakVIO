"""Expose only explicit ToFlix VF rows as normalized French streams.

The provider already embeds source language/variant information in the returned
row title but omits the normalized ``language`` field. V2 deliberately avoids
browser-only URL APIs so the wrapper behaves the same inside NuvioTV QuickJS.
A row is marked ``fr`` only when it carries VF/TRUEFRENCH/FRENCH (never VOSTFR)
and its resolved URL uses ToFlix's explicit ``french.*`` delivery branch.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_TOFLIX_EXPLICIT_VF_V2"


def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {"requireFrenchHost": bool(cfg.get("require_french_host", True))}
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in source:
        return source

    shim = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function slot(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function frenchHost(row){var u=s(row&&row.url).toLowerCase();return /^https?:\/\/french\./.test(u)||/^\/\/french\./.test(u)}
function explicitVf(row){var language=s(row&&row.language);if(/^(?:fr|fra|fre|french|francais|français)$/i.test(language))return true;var text=s((row&&row.title)||"")+" "+s((row&&row.name)||"");if(/\bVOSTFR\b/i.test(text))return false;return /\b(?:VF|TRUEFRENCH|FRENCH)\b/i.test(text)}
function annotate(row){if(!row||typeof row!=="object")return row;if(!explicitVf(row))return row;if(c.requireFrenchHost&&!frenchHost(row))return row;if(/^(?:fr|fra|fre|french|francais|français)$/i.test(s(row.language)))return row;var out=Object.assign({},row);out.language="fr";return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioToflixExplicitVfV2)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x)return v;return rebuild(v,x,x.list.map(annotate))};wrap.__nuvioToflixExplicitVfV2=true;wrap.__nuvioToflixExplicitVfOriginal=native;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return source.rstrip() + "\n" + shim.lstrip()
