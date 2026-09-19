#!/usr/bin/env python3
"""NiakVIO-owned Animetsu current API runtime.

Current upstream contract decoded from the active Animetsu provider bytes:
Core TMDB semantic gate -> /v2/api/anime/search/?query=... ->
/v2/api/anime/oppai/{id}/{episode}?server={kite|dio}&source_type={sub|dub} ->
swiftstream proxy URL -> Core HLS validation.

No upstream JavaScript is embedded or executed. Core owns TMDB identity,
semantic classification and final stream validation.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMETSU.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMETSU_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMETSU_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[’']/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function uniq(values){var out=[],seen={};for(var i=0;i<(values||[]).length;i++){var x=s(values[i]),k=norm(x);if(x&&k&&!seen[k]){seen[k]=1;out.push(x)}}return out}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var raw=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||x.semanticType||x.canonicalMediaType||x.mediaType||a[1]||"").toLowerCase();
  if(raw==="movie")return null;if(raw!=="anime"&&raw!=="tv"&&raw!=="series")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
  if(!/^\d+$/.test(id))return null;
  return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||x.tmdbMetadata||x.fixtureMetadata||null}
}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var m=projected(q.metadata);if(!m)try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv",season:q.season,episode:q.episode});m=projected(z)}}catch(_e){}return m}
function animeMeta(m){if(!m)return false;var genres=Array.isArray(m.genres)?m.genres:[],animation=false;for(var i=0;i<genres.length;i++){var r=genres[i]||{};if(Number(r.id)===16||/animation/i.test(s(r.name))){animation=true;break}}var lang=s(m.original_language||m.originalLanguage).toLowerCase();return animation&&["ja","zh","ko"].indexOf(lang)>=0}
function aliases(m){if(!m)return[];var values=[m.name,m.title,m.original_name,m.original_title],alt=m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)values.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(values).slice(0,8)}
function metaYear(m){var d=s(m&&(m.first_air_date||m.release_date));var hit=d.match(/(?:19|20)\d{2}/);return hit?Number(hit[0]):0}
function seasonCounts(m){var out={};if(Array.isArray(m&&m.seasons))for(var i=0;i<m.seasons.length;i++){var r=m.seasons[i]||{},sn=Number(r.season_number),ec=Number(r.episode_count);if(sn>0&&ec>0)out[sn]=ec}return out}
function absoluteEpisode(q,m){var n=q.episode,counts=seasonCounts(m);for(var sn=1;sn<q.season;sn++){var ec=Number(counts[sn]);if(!ec)return q.episode;n+=ec}return n}
function similarity(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 100;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 82;var aa=a.split(" ").filter(function(x){return x.length>=3}),bb=b.split(" ").filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<aa.length;i++)if(bb.indexOf(aa[i])>=0)hit++;return Math.round(100*hit/Math.max(aa.length,bb.length,1))}
function rowTitles(row){var t=row&&row.title,out=[row&&row.name,row&&row.englishName];if(t&&typeof t==="object")out.push(t.english,t.romaji,t.native);else out.push(t);return uniq(out)}
function score(row,wanted,year){var tt=rowTitles(row),best=0;for(var i=0;i<tt.length;i++)best=Math.max(best,similarity(tt[i],wanted));var ry=Number(row&&row.year)||Number((s(row&&row.release_date).match(/(?:19|20)\d{2}/)||[])[0]||0);if(year&&ry)best+=year===ry?24:-30;return best}
function headers(){return{"User-Agent":c.ua,"Referer":c.site+"/","Origin":c.site,"Accept-Language":"en-US,en;q=0.9","Accept":"application/json,text/plain,*/*"}}
async function jsonGet(url){try{var r=await g.fetch(url,{method:"GET",headers:headers(),redirect:"follow"});if(!r||!r.ok)return null;var raw=await r.text();try{return JSON.parse(raw)}catch(_e){return null}}catch(_e){return null}}
async function searchOne(query,year){var j=await jsonGet(c.api+"/anime/search/?query="+encodeURIComponent(query)),rows=j&&Array.isArray(j.results)?j.results:[],best=null,bestScore=0;for(var i=0;i<rows.length;i++){var sc=score(rows[i],query,year);if(sc>bestScore){bestScore=sc;best=rows[i]}}return best&&s(best.id||best._id)&&bestScore>=62?best:null}
async function findShow(m,q){var names=aliases(m),year=metaYear(m);if(q.season>1){for(var i=0;i<Math.min(names.length,4);i++){var hit=await searchOne(names[i]+" Season "+q.season,year);if(hit)return hit}}for(var j=0;j<Math.min(names.length,6);j++){var hit2=await searchOne(names[j],year);if(hit2)return hit2}return null}
function proxied(raw){var u=s(raw);if(!u)return"";if(u.indexOf(c.proxy)===0)return u;if(/^https?:\/\//i.test(u))return u;return c.proxy+u}
function quality(v){var hit=s(v).match(/\b(2160|1440|1080|720|480|360)p?\b/i);return hit?hit[1]+"p":"Auto"}
async function sourceRows(id,ep,server,sourceType){var url=c.api+"/anime/oppai/"+encodeURIComponent(id)+"/"+encodeURIComponent(ep)+"?server="+encodeURIComponent(server)+"&source_type="+encodeURIComponent(sourceType),j=await jsonGet(url),rows=j&&Array.isArray(j.sources)?j.sources:[],out=[];for(var i=0;i<rows.length;i++){var r=rows[i]||{},u=proxied(r.url);if(!/^https?:\/\//i.test(u))continue;out.push({url:u,quality:quality(r.quality||r.resolution),language:sourceType==="dub"?"English Dub":"VOSTA",server:server})}return out}
async function resolve(a){var q=req(a);if(q===null)return[];var m=await metadata(q);if(!animeMeta(m))return[];var show=await findShow(m,q);if(!show)return[];var id=s(show.id||show._id),ep=absoluteEpisode(q,m),out=[],seen={};for(var si=0;si<c.servers.length&&out.length<c.maxStreams;si++){for(var ti=0;ti<c.sourceTypes.length&&out.length<c.maxStreams;ti++){var st=c.sourceTypes[ti],rows=await sourceRows(id,ep,c.servers[si],st);for(var ri=0;ri<rows.length&&out.length<c.maxStreams;ri++){var row=rows[ri],u=s(row.url);if(!u||seen[u])continue;seen[u]=1;out.push({name:"Animetsu | "+row.server+" | "+row.language,title:"Animetsu | S"+q.season+"E"+q.episode+" | "+row.language,url:u,quality:row.quality,language:row.language,provider:"animetsu",season:q.season,episode:q.episode,headers:headers()})}}}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"animetsu",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg={
        "api":"https://animetsu.live/v2/api",
        "site":"https://animetsu.live",
        "proxy":"https://swiftstream.top/proxy",
        "servers":["kite","dio"],
        "sourceTypes":["sub","dub"],
        "maxStreams":8,
        "ua":"Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["api"]=str(cfg.get("api") or "").rstrip("/")
    cfg["site"]=str(cfg.get("site") or "").rstrip("/")
    cfg["proxy"]=str(cfg.get("proxy") or "").rstrip("/")
    cfg["servers"]=[str(x) for x in (cfg.get("servers") or []) if str(x)][:4]
    cfg["sourceTypes"]=[str(x) for x in (cfg.get("sourceTypes") or []) if str(x) in {"sub","dub"}][:2]
    cfg["maxStreams"]=max(1,min(int(cfg.get("maxStreams") or 8),12))
    if not cfg["api"].startswith(("http://","https://")) or not cfg["proxy"].startswith(("http://","https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: api/proxy must be http(s)")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"animetsu-gojo-search-oppai-v1",
        "identity":"core-tmdb-anime-gated-title-year",
        "semanticLanes":["anime"],
        "runtimeResolverRegistration":True,
        "upstreamContract":{"servers":["kite","dio"],"sourceTypes":["sub","dub"],"proxy":"swiftstream"},
        "coreFinalOutputOwnership":True,
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
