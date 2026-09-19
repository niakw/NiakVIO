#!/usr/bin/env python3
"""Clean provider-local Flemmix catalogue/player runtime."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.FLEMMIX.RUNTIME.V1"
MARKER = "NIAKVIO_FLEMMIX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_FLEMMIX_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function runtimeBase(){try{var m=typeof NIAKVIO_PROVIDER_MODEL!=="undefined"&&NIAKVIO_PROVIDER_MODEL,b=s(m&&(m.officialSite||m.knownSite)||c.base);return b.replace(/\/$/,"")}catch(_e){return s(c.base).replace(/\/$/,"")}}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return""}}
function textOnly(v){return s(v).replace(/<[^>]+>/g," ").replace(/&amp;/gi,"&").replace(/&#(?:39|x27);/gi,"'").replace(/\s+/g," ").trim()}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function request(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"movie").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
  return {type:raw,tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type});return projected(r)}}catch(_e){}return null}
function aliases(md){if(!md)return[];var out=[md.title,md.name,md.original_title,md.original_name],alt=md.alternative_titles&&(md.alternative_titles.titles||md.alternative_titles.results||md.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(out).slice(0,6)}
function headers(json){return {"User-Agent":c.userAgent,"Accept":json?"application/json,text/html,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Referer":runtimeBase()+"/","X-Requested-With":"XMLHttpRequest"}}
async function getText(url){try{var r=await g.fetch(url,{headers:headers(false)});if(!r||!r.ok)return"";return await r.text()}catch(_e){return""}}
async function getJson(url){try{var r=await g.fetch(url,{headers:headers(true)});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function score(label,query){var a=norm(label),b=norm(query);if(!a||!b)return 0;if(a===b)return 150;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 100;var aw=a.split(/\s+/),bw=b.split(/\s+/),n=0;for(var i=0;i<bw.length;i++)if(bw[i].length>2&&aw.indexOf(bw[i])>=0)n++;return bw.length?Math.round(n/bw.length*80):0}
function catalogRows(html,page){var out=[],seen={},re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<160){var u=abs(m[1],page),low=u.toLowerCase();if(!/\/(?:serie-en-streaming|film-en-streaming)\//i.test(low)||seen[u])continue;seen[u]=1;var sm=low.match(/(?:saison|season)-(\d+)/),label=textOnly(m[2])||decodeURIComponent(low.split("/").pop()||"").replace(/[-_]+/g," ");out.push({url:u,title:label,series:/\/serie-en-streaming\//i.test(low),season:sm?Number(sm[1]):0})}return out}
async function find(als,isSeries,wantedSeason){for(var i=0;i<als.length&&i<4;i++){var url=runtimeBase()+"/index.php?do=search&subaction=search&search_start=0&full_search=0&story="+encodeURIComponent(als[i]),html=await getText(url);if(!html)continue;var pool=catalogRows(html,url),typed=pool.filter(function(r){return r.series===isSeries});if(typed.length)pool=typed;pool.sort(function(a,b){var sa=score(a.title,als[i]),sb=score(b.title,als[i]);if(isSeries&&wantedSeason){if(a.season===wantedSeason)sa+=80;else if(a.season)sa-=30;if(b.season===wantedSeason)sb+=80;else if(b.season)sb-=30}return sb-sa});if(pool.length&&score(pool[0].title,als[i])>=20)return pool[0]}return null}
function attr(tag,name){var re=new RegExp(name+"\\s*=\\s*[\"']([^\"']+)[\"']","i"),m=re.exec(tag);return m?m[1]:""}
function serverTabs(html,kind,page){var cls=kind==="movie"?"video-server-tab":"episode-server-tab",re=new RegExp("<button[^>]*class=[\"'][^\"']*"+cls+"[^\"']*[\"'][^>]*>[\\s\\S]*?<\\/button>","gi"),out=[],m;while((m=re.exec(html||""))!==null&&out.length<16){var tag=m[0],u=abs(attr(tag,"data-url"),page);if(!u)continue;var langm=tag.match(/class=[\"'][^\"']*lang-pill[^\"']*[\"'][^>]*>([\\s\\S]*?)<\\//i),qm=tag.match(/class=[\"'][^\"']*quality-pill[^\"']*[\"'][^>]*>([\\s\\S]*?)<\\//i),blob=textOnly(tag).toUpperCase(),lang=langm?textOnly(langm[1]).toUpperCase():(blob.indexOf("VOSTFR")>=0?"VOSTFR":blob.match(/(?:^|\s)VF(?:\s|$)/)?"VF":"VO"),quality=qm?textOnly(qm[1]).toUpperCase():"HD";out.push({url:u,language:lang,quality:quality})}return out}
async function resolveTabs(tabs,page,q){var out=[],seen={};for(var i=0;i<tabs.length&&i<8;i++){var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([tabs[i].url],page,2)}catch(_e){direct=[]}if(!Array.isArray(direct))continue;for(var j=0;j<direct.length&&out.length<8;j++){var row=direct[j];if(!row||!/^https?:/i.test(s(row.url))||seen[row.url])continue;seen[row.url]=1;var x=Object.assign({},row);x.name="Flemmix";x.title="Flemmix ["+tabs[i].language+"]";x.language=tabs[i].language;x.quality=x.quality||tabs[i].quality||"HD";x.provider="flemmix";if(q.type!=="movie"){x.season=q.season;x.episode=q.episode}out.push(x)}}return out}
function seasonLinks(html,page){var out=[],re=/<a[^>]+href=[\"']([^\"']*\/saison-(\d+)(?:-vf|-vostfr)?)[\"'][^>]*>/gi,m;while((m=re.exec(html||""))!==null)out.push({url:abs(m[1],page),season:Number(m[2])});return out}
function episodeLinks(html,page){var out=[],re=/<a[^>]+href=[\"']([^\"']*\/([a-z0-9-]+)\/(\d+)x(\d+))[^\"']*[\"'][^>]*>/gi,m;while((m=re.exec(html||""))!==null)out.push({url:abs(m[1],page),season:Number(m[3]),episode:Number(m[4])});return out}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q),als=aliases(md);if(!als.length)return[];var hit=await find(als,q.type==="tv",q.season);if(!hit)return[];
  if(q.type==="movie"){var html=await getText(hit.url);if(!html)return[];return await resolveTabs(serverTabs(html,"movie",hit.url),hit.url,q)}
  var root=await getText(hit.url);if(!root)return[];var season=hit.season===q.season?{url:hit.url,season:q.season}:seasonLinks(root,hit.url).find(function(x){return x.season===q.season});if(!season)return[];var sh=season.url===hit.url?root:await getText(season.url);if(!sh)return[];var eps=episodeLinks(sh,season.url),ep=eps.find(function(x){return x.season===q.season&&x.episode===q.episode});if(!ep)return[];var eh=await getText(ep.url);if(!eh)return[];return await resolveTabs(serverTabs(eh,"episode",ep.url),ep.url,q)}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"flemmix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://flemmix.me",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text, MANAGED_FIX_ID, js.lstrip(),
        data={
            "runtimeFamily": "flemmix-search-detail-season-episode-player-v1",
            "identity": "core-tmdb-aliases-plus-site-catalogue",
            "semanticLanes": ["movie", "tv"],
            "runtimeResolverRegistration": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
