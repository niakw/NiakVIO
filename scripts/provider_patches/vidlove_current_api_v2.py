#!/usr/bin/env python3
"""VidLove current multi-source JSON API runtime v2."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDLOVE.CURRENT.API.V2"
MARKER = "NIAKVIO_VIDLOVE_CURRENT_API_V2"

WRAPPER = r'''
/* NIAKVIO_VIDLOVE_CURRENT_API_V2 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function lane(v){v=s(v).toLowerCase();if(v==="series"||v==="anime")v="tv";return v==="movie"?"movie":v==="tv"?"tv":""}
function headers(){return {"User-Agent":c.ua,"Accept":"application/json,text/plain,*/*","Accept-Language":"en-US,en;q=0.8","Referer":c.referer,"Origin":c.origin}}
function urlFor(source,id,type,season,episode){var q="id="+encodeURIComponent(id)+"&mode=json&sources="+encodeURIComponent(source)+"&hevc=1";if(type==="tv")q+="&season="+encodeURIComponent(season)+"&episode="+encodeURIComponent(episode);return c.base+"/"+type+"?"+q}
function add(out,seen,url,label,quality,title){url=s(url);if(!/^https?:\/\//i.test(url)||seen[url])return;seen[url]=1;out.push({name:"VidLove"+(label?" ["+label+"]":""),title:s(title)||"VidLove",url:url,quality:s(quality),provider:"vidlove",isDirect:true,type:"direct",headers:{Referer:c.referer,Origin:c.origin,"User-Agent":c.ua}})}
async function one(source,id,type,season,episode){try{var r=await g.fetch(urlFor(source,id,type,season,episode),{headers:headers(),redirect:"follow"});if(!r||!r.ok)return[];var data=await r.json(),src=data&&data.source;if(!src||typeof src!=="object")return[];var meta=data.meta||{},title=s(meta.name||meta.title||meta.original_title||meta.original_name),label=s(src.label||source),out=[],seen={};if(Array.isArray(src.qualities)){for(var i=0;i<src.qualities.length;i++){var q=src.qualities[i]||{};add(out,seen,q.url,label,q.quality,title)}}add(out,seen,src.url,label,src.quality,title);return out}catch(_e){return[]}}
async function current(id,mediaType,season,episode){id=s(id);var type=lane(mediaType);if(!id||!type)return[];season=Math.floor(Number(season)||0);episode=Math.floor(Number(episode)||0);if(type==="tv"&&(season<=0||episode<=0))return[];var out=[],seen={};for(var i=0;i<c.sources.length&&out.length<c.maxRows;i++){var rows=await one(c.sources[i],id,type,season,episode);for(var j=0;j<rows.length&&out.length<c.maxRows;j++){if(!seen[rows[j].url]){seen[rows[j].url]=1;out.push(rows[j])}}}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioVidLoveCurrentApiV2)return false;var original=o[k],wrapped=async function(tmdbId,mediaType,season,episode){try{var out=await current(tmdbId,mediaType,season,episode);if(out.length)return out}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return[]}};wrapped.__niakvioVidLoveCurrentApiV2=true;wrapped.__niakvioOriginal=original;o[k]=wrapped;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(typeof _spv4GetStreams==="function"&&!_spv4GetStreams.__niakvioVidLoveCurrentApiV2){var orig=_spv4GetStreams;_spv4GetStreams=async function(tmdbId,mediaType,season,episode){try{var out=await current(tmdbId,mediaType,season,episode);if(out.length)return out}catch(_e){}try{return await orig(tmdbId,mediaType,season,episode)}catch(_e){return[]}};_spv4GetStreams.__niakvioVidLoveCurrentApiV2=true}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://ballerinacappuccinalovestungtungtungsahur.com",
        "referer": "https://player.vidlove.cc/",
        "origin": "https://player.vidlove.cc",
        "sources": ["moviebox", "ipcloud", "tcloud", "vidapi", "vixsrc", "1embed", "xpass", "vidrift", "lookmovie", "vidnest"],
        "maxRows": 12,
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(text, MANAGED_FIX_ID, js.lstrip(), data={
        "scope": "provider-local-current-multisource-json-api-v2",
        "providerBaseModified": False,
        "fixtureIdsHardcoded": False,
        "directApi": cfg["base"],
        "sourceCount": len(cfg["sources"]),
        "supportsQualityArrays": True,
    })


if __name__ == "__main__":
    raise SystemExit("patch module only")
