#!/usr/bin/env python3
"""NiakVIO-owned AnimeVOSTFR WordPress/ToroPlay runtime.

Clean-room adapter from the observable current contract:
TMDB/Core metadata -> WordPress search -> /animes/ result -> /episode/ page ->
`trembed` resolver -> external player. Upstream JavaScript is never embedded or
executed. Core retains timeout, identity and terminal stream ownership.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMEVOSTFR.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMEVOSTFR_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMEVOSTFR_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function txt(v){return String(v==null?"":v).trim()}
function uniq(v){return Array.from(new Set((v||[]).filter(Boolean)))}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=txt((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"anime").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv"&&raw!=="anime")return null;var id=txt((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return null;return{type:raw,transport:raw==="movie"?"movie":"tv",tmdbId:id,season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1}}
function norm(v){return txt(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[’']/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,base){try{return new URL(v,base).toString()}catch(_e){return""}}
function htmlDecode(v){return txt(v).replace(/&amp;/g,"&").replace(/&quot;|&#34;/g,'"').replace(/&#39;/g,"'")}
async function fetchText(url,opt){try{var options=opt||{};options.headers=Object.assign({"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"},options.headers||{});var r=typeof _fetch==="function"?await _fetch(url,options):await g.fetch(url,options);if(!r||r.ok===false)return"";return await r.text()}catch(_e){return""}}
async function metadata(q){var meta=null;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:String(q.tmdbId),mediaType:q.transport,tmdbNamespace:q.transport});meta=z&&z.metadata||null}}catch(_e){}if(!meta){try{if(typeof _tmdb==="function")meta=await _tmdb(q.tmdbId,q.transport)}catch(_e){}}if(!meta){try{var ctx=g&&g.__nuvioMediaContext||{};meta=ctx.tmdbMetadata||ctx.fixtureMetadata||null}catch(_e){}}return meta}
function titles(meta){var out=[];if(meta){out.push(meta.title,meta.name,meta.original_title,meta.original_name);if(Array.isArray(meta.aliases))out=out.concat(meta.aliases);if(meta.alternative_titles&&Array.isArray(meta.alternative_titles.titles))for(var i=0;i<meta.alternative_titles.titles.length;i++)out.push(meta.alternative_titles.titles[i]&&meta.alternative_titles.titles[i].title)}return uniq(out.map(txt).filter(Boolean)).slice(0,6)}
function hrefs(body,base,needle){var out=[],re=/href\s*=\s*["']([^"']+)["']/gi,m;while((m=re.exec(body||""))!==null){var u=abs(htmlDecode(m[1]),base);if(u&&(!needle||u.indexOf(needle)>=0)&&!out.includes(u))out.push(u);if(out.length>=80)break}return out}
function resultScore(url,title){var path="";try{path=decodeURIComponent(new URL(url).pathname)}catch(_e){path=url}var n=norm(path.replace(/\/animes\//i," ").replace(/\//g," ")),t=norm(title);if(!n||!t)return 0;if(n===t)return 300;if(n.indexOf(t)>=0)return 220-Math.min(80,Math.max(0,n.length-t.length));var words=t.split(" ").filter(function(w){return w.length>2}),hit=0;for(var i=0;i<words.length;i++)if(n.indexOf(words[i])>=0)hit++;return words.length?Math.round(120*hit/words.length):0}
async function search(base,title){var body=await fetchText(base+"/?s="+encodeURIComponent(title),{headers:{Referer:base+"/"}});if(!body)return[];var urls=hrefs(body,base,"/animes/");urls.sort(function(a,b){return resultScore(b,title)-resultScore(a,title)});return urls.filter(function(u){return resultScore(u,title)>=35}).slice(0,6)}
function episodeScore(url,q){var s=String(q.season),e=String(q.episode),p=String(q.episode).padStart(2,"0"),u=txt(url).toLowerCase();if(new RegExp("-(?:saison-)?"+s+"-episode-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 300;if(new RegExp("-episode-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 180;if(new RegExp("-ep-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 120;return 0}
async function episodePage(series,q){var body=await fetchText(series,{headers:{Referer:c.base+"/"}});if(!body)return"";var eps=hrefs(body,series,"/episode/");if(q.type==="movie")return eps[0]||series;eps.sort(function(a,b){return episodeScore(b,q)-episodeScore(a,q)});return eps.length&&episodeScore(eps[0],q)>0?eps[0]:""}
function trembeds(body,base){var out=[],patterns=[/(?:src|data-src)\s*=\s*["']([^"']*(?:trembed|trid=)[^"']*)["']/gi,/iframe[^>]+src\s*=\s*["']([^"']+)["']/gi],m;for(var p=0;p<patterns.length;p++){while((m=patterns[p].exec(body||""))!==null){var u=abs(htmlDecode(m[1]),base);if(u&&/^https?:/i.test(u)&&!out.includes(u))out.push(u);if(out.length>=12)break}}return out}
function externalPlayer(body,base){var patterns=[/iframe[^>]+src\s*=\s*["']([^"']+)["']/i,/(?:data-src|src|href)\s*=\s*["'](https?:\/\/[^"']+)["']/i];for(var i=0;i<patterns.length;i++){var m=(body||"").match(patterns[i]);if(m){var u=abs(htmlDecode(m[1]),base);try{if(new URL(u).hostname!==new URL(c.base).hostname)return u}catch(_e){}}}return""}
async function playerRows(player,referer,language){if(!/^https?:/i.test(player))return[];var rows=[];try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([player],referer,2)}catch(_e){}if(!Array.isArray(rows)||!rows.length){try{if(typeof _directMedia==="function"&&_directMedia(player)&&typeof _streams==="function")rows=_streams([player],referer)}catch(_e){}}if(!Array.isArray(rows)||!rows.length)rows=[{name:"AnimeVOSTFR",title:"AnimeVOSTFR player",url:player,quality:"HD",language:language,headers:{Referer:referer},provider:"animevostfr"}];for(var i=0;i<rows.length;i++){var r=rows[i];if(r&&typeof r==="object"){r.name=r.name||"AnimeVOSTFR";r.title=r.title||"AnimeVOSTFR";r.language=r.language||language;r.provider=r.provider||"animevostfr";r.headers=Object.assign({Referer:referer},r.headers||{})}}return rows.slice(0,3)}
function langFrom(url){var u=txt(url).toLowerCase();if(/vostfr/.test(u))return"VOSTFR";if(/(?:^|[-_/])vf(?:[-_/]|$)/.test(u))return"VF";return"VOSTFR"}
async function resolveSeries(series,q){var ep=await episodePage(series,q);if(!ep)return[];var body=await fetchText(ep,{headers:{Referer:series}});if(!body)return[];var entries=trembeds(body,ep),out=[];for(var i=0;i<entries.length&&out.length<c.targetStreams;i++){var embed=await fetchText(entries[i],{headers:{Referer:ep}});if(!embed)continue;var player=externalPlayer(embed,entries[i]);if(!player)continue;var rows=await playerRows(player,ep,langFrom(series+" "+ep));for(var j=0;j<rows.length;j++)if(rows[j]&&rows[j].url)out.push(rows[j])}return out.slice(0,c.targetStreams)}
async function resolve(args,_ctx){var q=req(args);if(!q)return[];var meta=await metadata(q),tt=titles(meta);if(!tt.length)return[];for(var t=0;t<tt.length;t++){var found=await search(c.base,tt[t]);for(var i=0;i<found.length;i++){var rows=await resolveSeries(found[i],q);if(rows.length)return rows}}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"animevostfr",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://v2.animevostfr.org",
        "targetStreams": 3,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["targetStreams"] = max(1, min(6, int(cfg.get("targetStreams") or 3)))
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "wordpress-toroplay-trembed-v1",
            "identity": "core-tmdb-metadata-to-search-to-episode",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "anime"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
