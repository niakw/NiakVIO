#!/usr/bin/env python3
"""NiakVIO-owned MovieBox resolver for the current vidsrcme TMDB contract.

Observed current chain: MovieBox -> vidsrcme TMDB resolver -> JSON `src` media URL.
No upstream JavaScript is embedded or executed. Core keeps final media validation,
HTTP fail-closed, timeout/cancellation, identity and output ownership.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIEBOX.VIDSRCME.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIEBOX_VIDSRCME_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MOVIEBOX_VIDSRCME_RUNTIME_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"movie").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return null;return{type:raw,id:id,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
async function jsonGet(url){try{var headers={"User-Agent":c.userAgent,"Accept":"application/json,text/plain,*/*","Referer":c.referer};var r=typeof _fetch==="function"?await _fetch(url,{headers:headers,redirect:"follow"}):await g.fetch(url,{headers:headers,redirect:"follow"});if(!r||r.ok===false)return null;return await r.json()}catch(_e){return null}}
function mediaUrl(v){var u=s(v);return /^https?:\/\//i.test(u)?u:""}
async function resolve(args){var q=req(args);if(!q)return[];var url=c.base+"/vs_src.php?type="+encodeURIComponent(q.type)+"&id="+encodeURIComponent(q.id);if(q.type==="tv")url+="&season="+encodeURIComponent(q.season)+"&episode="+encodeURIComponent(q.episode);var data=await jsonGet(url),src=mediaUrl(data&&data.src);if(!src)return[];return[{name:"MovieBox",title:"MovieBox",url:src,provider:"moviebox",headers:{"Referer":c.referer,"User-Agent":c.userAgent}}]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioMovieboxVidsrcmeV1)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioMovieboxVidsrcmeV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://vidsrcme.ru",
        "referer": "https://vidsrcme.ru/",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["referer"] = str(cfg.get("referer") or cfg["base"] + "/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "moviebox-vidsrcme-tmdb-direct-v1",
            "identity": "tmdb-direct",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "tv"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
