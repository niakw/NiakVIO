#!/usr/bin/env python3
"""Clean provider-local Anime-Ultime search/player runtime."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIME-ULTIME.RUNTIME.V1"
MARKER = "NIAKVIO_ANIME_ULTIME_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIME_ULTIME_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function slug(v){var x=norm(v);return x.replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return""}}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function request(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"anime").toLowerCase();if(semantic==="series")semantic="tv";if(semantic!=="anime"&&semantic!=="tv")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
  return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"});return projected(r)}}catch(_e){}return null}
function aliases(md){if(!md)return[];var out=[md.name,md.title,md.original_name,md.original_title],alt=md.alternative_titles&&(md.alternative_titles.results||md.alternative_titles.titles||md.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(out).slice(0,6)}
function headers(){return{"User-Agent":c.userAgent,"Accept":"application/json,text/html,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Referer":c.base+"/","Origin":c.base,"X-Requested-With":"XMLHttpRequest"}}
async function text(url){try{var r=await g.fetch(url,{headers:headers()});if(!r||!r.ok)return"";return await r.text()}catch(_e){return""}}
async function postJson(path,body){try{var h=headers();h["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8";var r=await g.fetch(c.base+path,{method:"POST",headers:h,body:body});if(!r||!r.ok)return null;var raw=await r.text();try{return JSON.parse(raw)}catch(_e){return null}}catch(_e){return null}}
function score(row,q,season){var a=norm(row&&row.title),b=norm(q);if(!a||!b)return 0;var sc=a===b?100:(a.indexOf(b)>=0||b.indexOf(a)>=0?75:0);if(!sc){var aw=a.split(/\s+/),bw=b.split(/\s+/),hit=0;for(var i=0;i<bw.length;i++)if(bw[i].length>1&&aw.indexOf(bw[i])>=0)hit++;sc=bw.length?Math.round(hit/bw.length*70):0}var fmt=s(row&&row.format).toUpperCase();if(fmt==="OAV"||fmt==="OST"||fmt==="FILM")sc-=25;var m=s(row&&row.title).match(/saison\s*(\d+)/i);if(m&&season)sc+=Number(m[1])===season?40:-20;return sc}
async function search(als,season){for(var i=0;i<als.length&&i<6;i++){var rows=await postJson("/MenuSearch.html","search="+encodeURIComponent(als[i]));if(!Array.isArray(rows))continue;var mapped=rows.map(function(r){return{title:s(r&&r.title).replace(/&amp;/g,"&"),url:s(r&&r.url),format:s(r&&r.format),type:s(r&&r.type),score:score(r,als[i],season)}}).filter(function(r){return r.url&&r.title&&r.score>=40&&["OAV","OST","FILM"].indexOf(r.format.toUpperCase())<0});mapped.sort(function(a,b){return b.score-a.score});if(mapped.length)return mapped[0]}return null}
function pageInfo(html){var sm=String(html||"").match(/data-serie=["'](\d+)["']/i),fm=String(html||"").match(/data-focus=["'](\d+)["']/i),eps=[],re=/<a[^>]+href=["']([^"']*Episode-(\d+)-(vostfr|vf)-par-[^"'.]+\.html)["'][^>]*>/gi,m;while((m=re.exec(html||""))!==null)eps.push({href:m[1],num:Number(m[2]),lang:m[3].toLowerCase()});return{serieId:sm?sm[1]:"",directFocus:fm?fm[1]:"",episodes:eps}}
async function focus(href){var h=await text(abs(href,c.base));var m=h.match(/data-focus=["'](\d+)["']/i);return m?m[1]:""}
function media(player){if(!player||typeof player!=="object")return null;var q=s(player.quality),keys=Object.keys(player),quality=q||keys.find(function(k){return /^\d+p$/i.test(k)})||"";var bucket=quality&&player[quality],mp4=bucket&&bucket.mp4,url=mp4&&mp4.url;if(!url)return null;return{url:s(url),quality:quality||"HD",title:s(player.title)}}
async function player(serie,focusId){return await postJson("/VideoPlayer.html","idserie="+encodeURIComponent(serie)+"&focusFile="+encodeURIComponent(focusId))}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q),als=aliases(md);if(!als.length)return[];var hit=await search(als,q.season);if(!hit)return[];var pageUrl=abs(hit.url,c.base),html=await text(pageUrl);if(!html)return[];var info=pageInfo(html);if(!info.serieId)return[];var ep=info.episodes.find(function(e){return e.num===q.episode&&e.lang==="vostfr"})||info.episodes.find(function(e){return e.num===q.episode})||null;if(!ep)return[];var focusId=await focus(ep.href);if(!focusId)return[];var p=await player(info.serieId,focusId);if(p&&p.error)return[];var m=media(p);if(!m||!/^https?:/i.test(m.url))return[];var url=m.url+(m.url.indexOf("?")>=0?"&":"?")+"v=.mp4";return[{name:"Anime-Ultime",title:(m.title||"Anime-Ultime")+" ["+ep.lang.toUpperCase()+"]",url:url,quality:m.quality,language:ep.lang==="vf"?"VF":"VOSTFR",provider:"anime-ultime",season:q.season,episode:q.episode,isDirect:true,headers:{Referer:c.base+"/"}}]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"anime-ultime",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://v5.anime-ultime.net",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text, MANAGED_FIX_ID, js.lstrip(),
        data={
            "runtimeFamily": "anime-ultime-menu-search-series-focus-player-v1",
            "identity": "core-tmdb-aliases-anime-season-episode",
            "semanticLanes": ["anime"],
            "runtimeResolverRegistration": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
