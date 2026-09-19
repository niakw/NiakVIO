#!/usr/bin/env python3
"""Provider-owned deterministic JSON stream-route adapter for Nuvio."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

WRAPPER = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||{};var canonical=s((obj&&obj.canonicalMediaType)||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(canonical!=="movie"&&canonical!=="tv")return null;var tmdb=s((obj&&(obj.tmdbId||obj.tmdb_id))||ctx.tmdbId||(typeof first==="string"?first:"")),imdb=s((obj&&(obj.imdbId||obj.imdb_id))||ctx.imdbId||(md.external_ids&&md.external_ids.imdb_id)),season=Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode=Number((obj&&obj.episode)!=null?obj.episode:args[3])||1;return{type:canonical,tmdbId:tmdb,imdbId:imdb,season:season,episode:episode}}
function bases(){var out=[],seen={};function add(v){v=s(v).replace(/\/+$/,"");if(!/^https?:\/\//i.test(v)||seen[v])return;seen[v]=1;out.push(v)}add(c.base);var f=Array.isArray(c.fallbackBases)?c.fallbackBases:[];for(var i=0;i<f.length;i++)add(f[i]);return out}
function endpoint(q,id,base){if(q.type==="movie")return base+"/stream/movie/"+encodeURIComponent(id)+".json";return base+"/stream/series/"+encodeURIComponent(id)+":"+encodeURIComponent(q.season)+":"+encodeURIComponent(q.episode)+".json"}
async function fetchJson(url,base){try{var r=await g.fetch(url,{headers:{"User-Agent":c.userAgent,"Accept":"application/json,*/*","Referer":base+"/"}});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function rows(v){return v&&Array.isArray(v.streams)?v.streams:Array.isArray(v)?v:[]}
function quality(row,url){var x=(s(row&&row.title)+" "+s(row&&row.name)+" "+s(url)).toLowerCase();if(x.indexOf("2160")>=0||x.indexOf("4k")>=0)return"2160p";if(x.indexOf("1080")>=0)return"1080p";if(x.indexOf("720")>=0)return"720p";if(x.indexOf("480")>=0)return"480p";return"Auto"}
function streams(value,base){var out=[],seen={};var list=rows(value);for(var i=0;i<list.length&&out.length<40;i++){var row=list[i]||{},url=s(row.url||row.externalUrl||row.external_url);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;out.push({name:c.name,title:s(row.title||row.name)||c.name,url:url,quality:quality(row,url),provider:c.provider,headers:{"Referer":base+"/","User-Agent":c.userAgent}})}return out}
function imdbFrom(value){var row=value&&value.metadata&&typeof value.metadata==="object"?value.metadata:value;if(!row||typeof row!=="object")return"";return s((row.external_ids&&row.external_ids.imdb_id)||row.imdb_id||row.imdbId)}
async function hydrateImdb(q){if(!q||/^tt\d+$/i.test(q.imdbId))return q;try{var ctx=g&&g.__nuvioMediaContext||{},id=imdbFrom(ctx.tmdbMetadata);if(/^tt\d+$/i.test(id)){q.imdbId=id;return q}}catch(_e){}try{var cache=g&&g.__nuvioTmdbMetadataCacheV1,key=q.type+":"+q.tmdbId,cached=cache&&cache[key];if(cached){var settled=typeof cached.then==="function"?await cached:cached,id2=imdbFrom(settled);if(/^tt\d+$/i.test(id2)){q.imdbId=id2;return q}}}catch(_e){}try{var getTmdbData=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof getTmdbData==="function"){var result=await getTmdbData({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type}),id3=imdbFrom(result);if(/^tt\d+$/i.test(id3))q.imdbId=id3}}catch(_e){}return q}
async function resolve(args){var q=req(args);if(!q||!/^\d+$/.test(q.tmdbId))return[];q=await hydrateImdb(q);var ids=[];if(/^tt\d+$/i.test(q.imdbId))ids.push(q.imdbId);ids.push(q.tmdbId);var bs=bases();for(var b=0;b<bs.length;b++){var base=bs[b];for(var i=0;i<ids.length;i++){var value=await fetchJson(endpoint(q,ids[i],base),base),out=streams(value,base);if(out.length)return out}}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioJsonStreamRuntimeV2)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioJsonStreamRuntimeV2=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply_runtime(text: str, *, managed_fix_id: str, marker: str, defaults: dict[str, Any], options: dict[str, Any] | None = None) -> str:
    cfg = dict(defaults)
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    fallback_bases: list[str] = []
    for raw in cfg.get("fallbackBases") or []:
        value = str(raw or "").strip().rstrip("/")
        if value.startswith(("http://", "https://")) and value != cfg["base"] and value not in fallback_bases:
            fallback_bases.append(value)
    cfg["fallbackBases"] = fallback_bases[:4]
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
            "identity": "core-tmdb-external-id-to-json-stream-route",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )
