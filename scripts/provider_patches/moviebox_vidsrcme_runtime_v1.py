#!/usr/bin/env python3
"""NiakVIO-owned MovieBox current Cinescrape runtime with legacy vidsrcme fallback."""
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
function req(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"movie").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{type:raw,id:id,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
function imdbFrom(v){if(v&&v.state==="ok"&&v.metadata)v=v.metadata;if(!v||typeof v!=="object")return"";var e=v.external_ids||v.externalIds||{},id=s(v.imdb_id||v.imdbId||v.imdb||e.imdb_id||e.imdbId||e.imdb);return /^tt\d+$/i.test(id)?id:""}
async function hydrateImdb(q){try{var ctx=g&&g.__nuvioMediaContext||{},id=imdbFrom(ctx.tmdbMetadata||ctx.metadata||ctx);if(id)return id}catch(_e){}try{var cache=g&&g.__nuvioTmdbMetadataCacheV1,key=q.type+":"+q.id,cached=cache&&cache[key];if(cached){var settled=typeof cached.then==="function"?await cached:cached,id2=imdbFrom(settled);if(id2)return id2}}catch(_e){}try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.id,mediaType:q.type,tmdbNamespace:q.type}),id3=imdbFrom(z);if(id3)return id3}}catch(_e){}return""}
function baseHeaders(ref){var h={"User-Agent":c.userAgent,"Accept":"application/json,text/plain,*/*"};if(ref)h.Referer=ref;return h}
async function jsonGet(url,ref){try{var r=typeof _fetch==="function"?await _fetch(url,{headers:baseHeaders(ref),redirect:"follow"}):await g.fetch(url,{headers:baseHeaders(ref),redirect:"follow"});if(!r||r.ok===false)return null;return await r.json()}catch(_e){return null}}
function mediaUrl(v){var u=s(v);return /^https?:\/\//i.test(u)?u:""}
function directMedia(u){return /\.(?:m3u8|mpd|mp4|m4v|mkv|webm)(?:[?#]|$)/i.test(s(u))||/\/hls\//i.test(s(u))}
function quality(row){var x=(s(row&&row.title)+" "+s(row&&row.description)+" "+s(row&&row.url)).toLowerCase();if(/2160|\b4k\b/.test(x))return"2160p";if(/1080/.test(x))return"1080p";if(/720/.test(x))return"720p";if(/480/.test(x))return"480p";return"Auto"}
function language(row){var x=(s(row&&row.title)+" "+s(row&&row.description)).toLowerCase();if(/hindi|\bhin\b/.test(x))return"hi";if(/multi|dual/.test(x))return"multi";if(/french|\bvf\b/.test(x))return"fr";return"en"}
function currentRows(value,q){var list=value&&Array.isArray(value.streams)?value.streams:Array.isArray(value)?value:[],out=[],seen={};for(var i=0;i<list.length&&out.length<c.maxStreams;i++){var row=list[i]||{},u=mediaUrl(row.url||row.externalUrl||row.external_url);if(!u||seen[u]||/bcdnxw\.hakunaymatata\.com/i.test(u))continue;seen[u]=1;var ql=quality(row),title="MovieBox"+(q.type==="tv"?" | S"+q.season+"E"+q.episode:"")+(ql!=="Auto"?" | "+ql:"");out.push({name:"MovieBox",title:title,url:u,quality:ql,language:language(row),provider:"moviebox",headers:{"Referer":c.streamReferer,"User-Agent":c.userAgent},isDirect:directMedia(u)})}return out}
async function current(q){var imdb=await hydrateImdb(q);if(!imdb)return[];var suffix=q.type==="tv"?"/stream/series/"+imdb+":"+q.season+":"+q.episode+".json":"/stream/movie/"+imdb+".json";var value=await jsonGet(c.cinescrapeBase.replace(/\/$/,"")+suffix,c.streamReferer);return currentRows(value,q)}
async function legacy(q){var url=c.legacyBase.replace(/\/$/,"")+"/vs_src.php?type="+encodeURIComponent(q.type)+"&id="+encodeURIComponent(q.id);if(q.type==="tv")url+="&season="+encodeURIComponent(q.season)+"&episode="+encodeURIComponent(q.episode);var data=await jsonGet(url,c.legacyReferer),src=mediaUrl(data&&data.src);if(!src)return[];var title="MovieBox"+(q.type==="tv"?" | S"+q.season+"E"+q.episode:"");if(directMedia(src))return[{name:"MovieBox",title:title,url:src,provider:"moviebox",headers:{"Referer":c.legacyReferer,"User-Agent":c.userAgent},isDirect:true}];var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([src],c.legacyReferer,3)}catch(_e){direct=[]}if(!Array.isArray(direct)||!direct.length)return[];var out=[],seen={};for(var i=0;i<direct.length&&out.length<c.maxStreams;i++){var row=direct[i]||{},u=mediaUrl(row.url);if(!u||seen[u])continue;seen[u]=1;var x=Object.assign({},row);x.url=u;x.provider="moviebox";x.name="MovieBox";x.title=title;if(!x.headers)x.headers={"Referer":src,"User-Agent":c.userAgent};out.push(x)}return out}
async function resolve(args){var q=req(args);if(!q)return[];var now=await current(q);if(now.length)return now;return await legacy(q)}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioMovieboxVidsrcmeV1)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioMovieboxVidsrcmeV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"moviebox",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "cinescrapeBase": "https://pengu.uk/",
        "streamReferer": "https://stremio-moviebox-1.onrender.com/",
        "legacyBase": "https://vidsrcme.ru",
        "legacyReferer": "https://vidsrcme.ru/",
        "maxStreams": 12,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["cinescrapeBase"] = str(cfg.get("cinescrapeBase") or "").rstrip("/")
    cfg["streamReferer"] = str(cfg.get("streamReferer") or "")
    cfg["legacyBase"] = str(cfg.get("legacyBase") or "").rstrip("/")
    cfg["legacyReferer"] = str(cfg.get("legacyReferer") or cfg["legacyBase"] + "/")
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 12), 24))
    if not cfg["cinescrapeBase"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: cinescrapeBase must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "moviebox-cinescrape-imdb-v3-with-legacy-vidsrcme",
            "identity": "tmdb-direct-core-imdb",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
            "terminalResolution": "current-cinescrape-json-first-legacy-vidsrcme-fallback",
            "semanticLanes": ["movie", "tv"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
