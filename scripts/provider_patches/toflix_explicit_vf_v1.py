"""Expose ToFlix's explicit VF stream semantics as normalized language metadata.

ToFlix already carries source language/variant information in its returned row
title (for example ``VF``) but does not populate the ``language`` field consumed
by Nuvio/our health checks.  This terminal wrapper is intentionally conservative:
it only marks a row French when the row itself says VF/TRUEFRENCH/FRENCH and the
resolved media host is explicitly on ToFlix's ``french.*`` delivery branch.
VOSTFR is not promoted to French audio because that would overstate the proof.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_TOFLIX_EXPLICIT_VF_V1"


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
function frenchHost(row){try{var h=new URL(s(row&&row.url)).hostname.toLowerCase();return h==="french"||h.indexOf("french.")===0||h.indexOf(".french.")>=0}catch(_e){return false}}
function explicitVf(row){var language=s(row&&row.language);if(/^(?:fr|fra|fre|french|francais|français)$/i.test(language))return true;var text=s((row&&row.title)||"")+" "+s((row&&row.name)||"");if(/\bVOSTFR\b/i.test(text))return false;return /\b(?:VF|TRUEFRENCH|FRENCH)\b/i.test(text)}
function annotate(row){if(!row||typeof row!=="object")return row;if(!explicitVf(row))return row;if(c.requireFrenchHost&&!frenchHost(row))return row;if(/^(?:fr|fra|fre|french|francais|français)$/i.test(s(row.language)))return row;var out=Object.assign({},row);out.language="fr";return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioToflixExplicitVfV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x)return v;return rebuild(v,x,x.list.map(annotate))};wrap.__nuvioToflixExplicitVfV1=true;wrap.__nuvioToflixExplicitVfOriginal=native;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return source.rstrip() + "\n" + shim.lstrip()
