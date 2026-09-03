#!/usr/bin/env python3
"""Provider-owned deterministic Stremio JSON route family."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

WRAPPER = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||{};var canonical=s((obj&&obj.canonicalMediaType)||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(canonical!=="movie"&&canonical!=="tv")return null;var tmdb=s((obj&&(obj.tmdbId||obj.tmdb_id))||ctx.tmdbId||(typeof first==="string"?first:"")),imdb=s((obj&&(obj.imdbId||obj.imdb_id))||ctx.imdbId||(md.external_ids&&md.external_ids.imdb_id)),season=Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode=Number((obj&&obj.episode)!=null?obj.episode:args[3])||1;return{type:canonical,tmdbId:tmdb,imdbId:imdb,season:season,episode:episode}}
function endpoint(q,id){if(q.type==="movie")return c.base+"/stream/movie/"+encodeURIComponent(id)+".json";return c.base+"/stream/series/"+encodeURIComponent(id)+":"+encodeURIComponent(q.season)+":"+encodeURIComponent(q.episode)+".json"}
async function fetchJson(url){try{var r=await g.fetch(url,{headers:{"User-Agent":c.userAgent,"Accept":"application/json,*/*","Referer":c.base+"/"}});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function rows(v){return v&&Array.isArray(v.streams)?v.streams:Array.isArray(v)?v:[]}
function quality(row,url){var x=(s(row&&row.title)+" "+s(row&&row.name)+" "+s(url)).toLowerCase();if(x.indexOf("2160")>=0||x.indexOf("4k")>=0)return"2160p";if(x.indexOf("1080")>=0)return"1080p";if(x.indexOf("720")>=0)return"720p";if(x.indexOf("480")>=0)return"480p";return"Auto"}
function streams(value){var out=[],seen={};var list=rows(value);for(var i=0;i<list.length&&out.length<40;i++){var row=list[i]||{},url=s(row.url||row.externalUrl||row.external_url);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;out.push({name:c.name,title:s(row.title||row.name)||c.name,url:url,quality:quality(row,url),provider:c.provider,headers:{"Referer":c.base+"/","User-Agent":c.userAgent}})}return out}
async function resolve(args){var q=req(args);if(!q||!/^\d+$/.test(q.tmdbId))return[];var ids=[];if(/^tt\d+$/i.test(q.imdbId))ids.push(q.imdbId);ids.push(q.tmdbId);for(var i=0;i<ids.length;i++){var value=await fetchJson(endpoint(q,ids[i])),out=streams(value);if(out.length)return out}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioStremioJsonRuntimeV1)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioStremioJsonRuntimeV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply_runtime(text: str, *, managed_fix_id: str, marker: str, defaults: dict[str, Any], options: dict[str, Any] | None = None) -> str:
    cfg = dict(defaults)
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["provider"] = str(cfg.get("provider") or "").strip()
    cfg["name"] = str(cfg.get("name") or cfg["provider"]).strip()
    cfg["userAgent"] = str(cfg.get("userAgent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{managed_fix_id}: base must be http(s)")
    js = WRAPPER.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        managed_fix_id,
        js.lstrip(),
        data={
            "runtime": cfg,
            "identity": "core-tmdb-or-imdb-to-stremio-json-route",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )
