#!/usr/bin/env python3
"""AllAnime current-site runtime: HTML catalogue -> exact episode -> verified HLS."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLANIME.SITE.RUNTIME.V1"
MARKER = "NIAKVIO_ALLANIME_SITE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ALLANIME_SITE_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function base(){try{var m=typeof NIAKVIO_PROVIDER_MODEL!=="undefined"&&NIAKVIO_PROVIDER_MODEL;return s(m&&(m.officialSite||m.knownSite)||c.base).replace(/\/$/,"")}catch(_e){return s(c.base).replace(/\/$/,"")}}
function norm(v){var x=s(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[’'`]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function text(v){return s(v).replace(/<script\b[\s\S]*?<\/script\s*>/gi," ").replace(/<style\b[\s\S]*?<\/style\s*>/gi," ").replace(/<[^>]*>/g," ").replace(/&[^;]+;/g," ").replace(/\s+/g," ").trim()}
function abs(v,b){try{return new URL(s(v).replace(/&amp;/gi,"&"),b).toString()}catch(_e){return""}}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||x.semanticType||x.canonicalMediaType||x.mediaType||a[1]||"").toLowerCase();if(semantic==="tv")semantic="anime";if(semantic!=="anime")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return[];return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||x.tmdbMetadata||x.fixtureMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var m=projected(q.metadata);if(!m)try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"});m=projected(z)}}catch(_e){}if(!m)return null;var title=s(m.name||m.title||m.original_name||m.original_title),alts=[],rows=m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(rows))for(var i=0;i<rows.length;i++){var t=s(rows[i]&&(rows[i].title||rows[i].name));if(t)alts.push(t)}var counts={};if(Array.isArray(m.seasons))for(var j=0;j<m.seasons.length;j++){var row=m.seasons[j]||{},sn=Number(row.season_number),ec=Number(row.episode_count);if(sn>0&&ec>0)counts[sn]=ec}return{title:title,aliases:[title].concat(alts).filter(Boolean).slice(0,8),seasonCounts:counts}}
function h(ref,accept){return{"User-Agent":c.ua,"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9","Referer":ref||base()+"/"}}
async function get(url,ref,accept){try{var r=await g.fetch(url,{headers:h(ref,accept),redirect:"follow"});if(!r||!r.ok)return null;return{body:await r.text(),url:r.url||url,headers:r.headers}}catch(_e){return null}}
function similarity(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 100;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 75;var aa=a.split(" ").filter(function(x){return x.length>=3}),bb=b.split(" ").filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<aa.length;i++)if(bb.indexOf(aa[i])>=0)hit++;return Math.round(100*hit/Math.max(aa.length,bb.length,1))}
function candidates(html,url,aliases){var out=[],seen={},re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<120){var u=abs(m[1],url);if(!u||seen[u])continue;var p="";try{p=new URL(u).pathname}catch(_e){continue}if(!/^\/[a-z0-9][a-z0-9-]*\/?$/i.test(p)||/-episode-\d+/i.test(p))continue;var label=text(m[2]),best=0;for(var i=0;i<aliases.length;i++)best=Math.max(best,similarity(label||p,aliases[i]));if(best<55)continue;seen[u]=1;out.push({url:u,score:best,label:label})}out.sort(function(a,b){return b.score-a.score});return out}
function absoluteEpisode(q,meta){var n=q.episode,ok=true;for(var sn=1;sn<q.season;sn++){var c=Number(meta&&meta.seasonCounts&&meta.seasonCounts[sn]);if(!c){ok=false;break}n+=c}return ok?n:q.episode}
function episodeLinks(html,url){var out=[],seen={},re=/<a\b[^>]*href=["']([^"']*-episode-(\d+)-[^"']+)["'][^>]*>/gi,m;while((m=re.exec(html||""))!==null&&out.length<500){var u=abs(m[1],url),n=Number(m[2]);if(u&&n>0&&!seen[u]){seen[u]=1;out.push({url:u,episode:n})}}return out}
function hlsUrls(body){var src=s(body).replace(/\\\//g,"/").replace(/&amp;/gi,"&"),out=[],seen={},re=/https?:\/\/[^"'<>\s]+\.m3u8(?:[?#][^"'<>\s]*)?/gi,m;while((m=re.exec(src))!==null&&out.length<20){var u=m[0].replace(/[),\];}]+$/g,"");if(!seen[u]){seen[u]=1;out.push(u)}}return out}
async function verifiedHls(url,referer){try{var r=await g.fetch(url,{headers:h(referer,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),redirect:"follow"});if(!r||!r.ok)return"";var body=await r.text();return /^#EXTM3U/m.test(body)?(r.url||url):""}catch(_e){return""}}
async function resolve(a){var q=req(a);if(q===null)return null;if(!q||!q.tmdbId)return[];var meta=await metadata(q);if(!meta||!meta.title)return[];var search=await get(base()+"/?s="+encodeURIComponent(meta.title).replace(/%20/g,"+"),base()+"/");if(!search)return[];var cs=candidates(search.body,search.url,meta.aliases);for(var i=0;i<cs.length&&i<4;i++){var series=await get(cs[i].url,search.url);if(!series)continue;var links=episodeLinks(series.body,series.url),wanted=absoluteEpisode(q,meta),row=links.find(function(x){return x.episode===wanted})||links.find(function(x){return x.episode===q.episode});if(!row)continue;var ep=await get(row.url,series.url);if(!ep)continue;var hs=hlsUrls(ep.body);for(var j=0;j<hs.length&&j<6;j++){var media=await verifiedHls(hs[j],ep.url);if(!media)continue;var lang=/dub|english-dubbed/i.test(ep.url+ep.body)?"English Dub":/sub|subbed/i.test(ep.url+ep.body)?"VOSTA":"Unknown";return[{name:"AllAnime",title:meta.title+" | E"+wanted,url:media,quality:"HD",language:lang,provider:"allanime",isDirect:true,headers:h(ep.url,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")}]}}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"allanime",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg={"base":"https://ww2.aniwatch.fit","ua":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36"}
    cfg.update(dict(options or {}))
    cfg["base"]=str(cfg.get("base") or "").rstrip("/")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"allanime-current-html-episode-hls-v1",
        "identity":"core-tmdb-aliases-exact-episode",
        "semanticLanes":["anime"],
        "runtimeResolverRegistration":True,
        "coreFinalOutputOwnership":True,
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
