#!/usr/bin/env python3
"""AnimeSalt clean-room runtime built from current provider-observable contracts."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMESALT.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMESALT_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMESALT_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function runtimeBase(){try{var m=typeof NIAKVIO_PROVIDER_MODEL!=="undefined"&&NIAKVIO_PROVIDER_MODEL,b=s(m&&(m.officialSite||m.knownSite)||c.base);return b.replace(/\/$/,"")}catch(_e){return s(c.base).replace(/\/$/,"")}}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[’'\x60]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function abs(v,b){try{return new URL(s(v).replace(/&amp;/gi,"&"),b).toString()}catch(_e){return""}}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||x.semanticType||x.canonicalMediaType||x.mediaType||a[1]||"").toLowerCase();
  if(semantic==="series")semantic="tv";
  if(semantic!=="anime"&&semantic!=="tv")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
  if(!/^\d+$/.test(id))return[];
  return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1}
}
function headers(ref,extra){var h={"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/json,*/*","Accept-Language":"en-US,en;q=0.8"};if(ref)h.Referer=ref;return Object.assign(h,extra||{})}
async function getText(url,ref){try{var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||!r.ok)return null;return{text:await r.text(),url:r.url||url}}catch(_e){return null}}
async function postJson(url,body,ref,origin){try{var r=await g.fetch(url,{method:"POST",headers:headers(ref,{"Content-Type":"application/x-www-form-urlencoded","Origin":origin||runtimeBase(),"X-Requested-With":"XMLHttpRequest"}),body:body,redirect:"follow"});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function meta(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"}),m=z&&z.metadata;if(m){var title=s(m.name||m.title||m.original_name||m.original_title),year=Number(s(m.first_air_date||m.release_date).slice(0,4))||0;if(title)return{title:title,year:year}}}}catch(_e){}
  try{var x=g&&g.__nuvioMediaContext||{},m2=x.tmdbMetadata||x.fixtureMetadata||{},t=s(m2.name||m2.title||m2.original_name||m2.original_title||x.title);if(t)return{title:t,year:Number(s(m2.first_air_date||m2.release_date||x.year).slice(0,4))||0}}catch(_e2){}return null}
function text(v){return s(v).replace(/<[^>]*>/g," ").replace(/&[^;]+;/g," ").replace(/\s+/g," ").trim()}
function candidateScore(label,title,year,type){var a=norm(label),b=norm(title),score=0;if(!a||!b)return-999;if(a===b)score+=250;else if(a.indexOf(b)>=0||b.indexOf(a)>=0)score+=150;var toks=b.split(" ").filter(function(x){return x.length>=3});for(var i=0;i<toks.length;i++)if(a.indexOf(toks[i])>=0)score+=12;if(year&&a.indexOf(String(year))>=0)score+=25;if(type==="series")score+=20;else score-=80;return score}
function searchRows(html,base,title,year){var out=[],seen={},re=/<article[^>]*>([\s\S]*?)<\/article>/gi,m;while((m=re.exec(html||""))!==null&&out.length<80){var block=m[1],hm=/href=["']([^"']+\/(series|movies)\/[^"']+)["']/i.exec(block),tm=/class=["'][^"']*entry-title[^"']*["'][^>]*>([\s\S]*?)<\//i.exec(block),ym=/class=["'][^"']*year[^"']*["'][^>]*>\s*(\d{4})/i.exec(block);if(!hm||!tm)continue;var u=abs(hm[1],base);if(!u||seen[u])continue;seen[u]=1;var label=text(tm[1]),y=ym?Number(ym[1]):0,score=candidateScore(label,title,year,hm[2].toLowerCase());if(year&&y&&Math.abs(y-year)>1)score-=100;if(score>=100)out.push({url:u,type:hm[2].toLowerCase(),score:score,label:label})}out.sort(function(a,b){return b.score-a.score});return out}
async function findSeries(m){var p=await getText(runtimeBase()+"/?s="+encodeURIComponent(m.title),runtimeBase()+"/");if(!p)return null;var rows=searchRows(p.text,p.url,m.title,m.year);for(var i=0;i<rows.length;i++)if(rows[i].type==="series")return rows[i];return null}
function episodeHref(html,season,episode,base){var target=String(season)+"x"+String(episode),re=/href=["']([^"']*\/episode\/[^"']+)["']/gi,m;while((m=re.exec(html||""))!==null){var u=abs(m[1],base);if(u&&u.toLowerCase().indexOf(target.toLowerCase())>=0)return u}return""}
async function episodePage(series,q){var root=await getText(series.url,runtimeBase()+"/");if(!root)return null;var direct=episodeHref(root.text,q.season,q.episode,root.url);if(direct)return await getText(direct,series.url);
  var seasons=[],re=/data-post=["'](\d+)["']\s+data-season=["'](\d+)["']/gi,m;while((m=re.exec(root.text))!==null)seasons.push({post:m[1],season:Number(m[2])});var chosen=null;for(var i=0;i<seasons.length;i++)if(seasons[i].season===q.season){chosen=seasons[i];break}if(!chosen)return null;
  var ajax=runtimeBase()+"/wp-admin/admin-ajax.php?action=action_select_season&season="+encodeURIComponent(String(q.season))+"&post="+encodeURIComponent(chosen.post),ap=await getText(ajax,series.url);if(!ap)return null;var href=episodeHref(ap.text,q.season,q.episode,ap.url);return href?await getText(href,series.url):null}
async function terminal(page,q,m){var hit=/src=["'](https:\/\/as-cdn\d+\.top\/video\/([a-f0-9]+))["']/i.exec(page.text||"");if(!hit)return[];var player=hit[1],hash=hit[2],origin="";try{origin=new URL(player).origin}catch(_e){return[]}
  var data=await postJson(origin+"/player/index.php?data="+encodeURIComponent(hash)+"&do=getVideo","hash="+encodeURIComponent(hash)+"&r="+encodeURIComponent(runtimeBase()+"/"),runtimeBase()+"/",origin);if(!data)return[];var url=s(data.videoSource||data.securedLink);if(!/^https?:/i.test(url))return[];var row={name:"AnimeSalt",title:m.title+" | S"+q.season+"E"+q.episode+" | Multi",url:url,quality:"1080p",language:"Multi",provider:"animesalt",headers:{Referer:origin+"/",Origin:origin,"User-Agent":c.userAgent}};return[row]}
async function resolve(a,_ctx){var q=req(a);if(q===null)return null;if(!q||!q.tmdbId)return[];var m=await meta(q);if(!m||!m.title)return[];var series=await findSeries(m);if(!series)return[];var page=await episodePage(series,q);if(!page)return[];return await terminal(page,q,m)}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"animesalt",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://animesalt.cx",
        "maxStreams": 2,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("AnimeSalt runtime base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "animesalt-search-season-ajax-cdn-v1",
            "identity": "core-tmdb-title-season-episode",
            "semanticLanes": ["anime"],
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
