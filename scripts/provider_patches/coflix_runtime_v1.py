#!/usr/bin/env python3
"""Clean provider-local Coflix catalogue/episode/player runtime."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.COFLIX.RUNTIME.V1"
MARKER = "NIAKVIO_COFLIX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_COFLIX_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function request(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(semantic==="series")semantic="tv";if(semantic!=="movie"&&semantic!=="tv"&&semantic!=="anime")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
  return{semantic:semantic,transport:semantic==="movie"?"movie":"tv",tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:q.transport,tmdbNamespace:q.transport});return projected(r)}}catch(_e){}return null}
function aliases(md){if(!md)return[];var out=[md.title,md.name,md.original_title,md.original_name],alt=md.alternative_titles&&(md.alternative_titles.titles||md.alternative_titles.results||md.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(out).slice(0,6)}
function headers(json){return{"User-Agent":c.userAgent,"Accept":json?"application/json, text/javascript, */*; q=0.01":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Referer":c.base+"/","X-Requested-With":"XMLHttpRequest"}}
async function getText(url){try{var r=await g.fetch(url,{headers:headers(false)});if(!r||!r.ok)return"";var t=await r.text();if(/BotBlocker|Just a moment|cf-browser-verification|Attention Required/i.test(t))return"";return t}catch(_e){return""}}
async function getJson(path){try{var r=await g.fetch(c.base+path,{headers:headers(true)});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function postJson(path,body){try{var h=headers(true);h["Content-Type"]="application/x-www-form-urlencoded";var r=await g.fetch(c.base+path,{method:"POST",headers:h,body:body});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function score(slug,query){var a=norm(s(slug).replace(/-(?:vostfr|vf|truefrench|french)$/i,"").replace(/-/g," ")),b=norm(query);if(!a||!b)return 0;if(a===b)return 100;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 75;var aw=a.split(/\s+/),bw=b.split(/\s+/),hit=0;for(var i=0;i<bw.length;i++)if(bw[i].length>=3&&aw.indexOf(bw[i])>=0)hit++;return bw.length?Math.round(hit/bw.length*70):0}
function language(slug,version){var x=(s(version)+" "+s(slug)).toLowerCase();if(/vostfr/.test(x))return"VOSTFR";if(/truefrench|french|(?:^|[-_ ])vf(?:[-_ ]|$)/.test(x))return"VF";return""}
function searchRows(html){var out=[],seen={},re=/href=["']https?:\/\/[^/"']+\/film\/([^/"']+)\/ep-(\d+)["']/gi,m;while((m=re.exec(html||""))!==null&&out.length<24){var slug=m[1],epId=m[2],key=slug+"|"+epId;if(seen[key])continue;seen[key]=1;out.push({slug:slug,epId:epId,language:language(slug,"")})}return out}
async function search(als){var out=[],seen={};for(var i=0;i<als.length&&i<5;i++){var data=await getJson("/ajax/search/suggest?keyword="+encodeURIComponent(als[i]));var rows=searchRows(data&&data.html);for(var j=0;j<rows.length;j++){rows[j].score=score(rows[j].slug,als[i]);var k=rows[j].slug+"|"+rows[j].epId;if(rows[j].score>=34&&!seen[k]){seen[k]=1;out.push(rows[j])}}if(out.length>=4)break}out.sort(function(a,b){return b.score-a.score});return out}
async function movieId(slug){var html=await getText(c.base+"/film/"+slug+"/");var m=html.match(/id=["']watch-page["'][^>]*data-id=["'](\d+)["']/i)||html.match(/data-id=["'](\d+)["']/i);return m?m[1]:""}
function episodes(html){var out=[],seen={},re=/data-num=["'](\d+)["'][^>]*data-id=["'](\d+)["']|data-id=["'](\d+)["'][^>]*data-num=["'](\d+)["']/gi,m;while((m=re.exec(html||""))!==null){var num=Number(m[1]||m[4]),id=s(m[2]||m[3]);if(num&&id&&!seen[num]){seen[num]=1;out.push({num:num,id:id})}}return out}
async function episodeId(slug,episode){var mid=await movieId(slug);if(!mid)return"";var data=await getJson("/ajax/episode/list-episode?movieId="+encodeURIComponent(mid));var row=episodes(data&&data.html).find(function(x){return x.num===episode});return row?row.id:""}
async function playerRows(epId,fallbackLang){var data=await postJson("/ajax/episode/player?episode_id="+encodeURIComponent(epId),"episode_id="+encodeURIComponent(epId));if(!data||data.status===false||!Array.isArray(data.message))return[];var out=[];for(var i=0;i<data.message.length;i++){var r=data.message[i]||{},u=r.server_link;if(u&&typeof u==="object")u=u.url;u=s(u);if(!/^https?:/i.test(u)||/kakaflix/i.test(u))continue;out.push({url:u,language:language("",r.version)||fallbackLang||""})}return out}
async function terminal(rows,referer,q){var out=[],seen={};for(var i=0;i<rows.length&&i<8;i++){var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([rows[i].url],referer,2)}catch(_e){direct=[]}if(!Array.isArray(direct))continue;for(var j=0;j<direct.length&&out.length<8;j++){var row=direct[j];if(!row||!/^https?:/i.test(s(row.url))||seen[row.url])continue;seen[row.url]=1;var x=Object.assign({},row);x.name="Coflix";x.title="Coflix"+(rows[i].language?" ["+rows[i].language+"]":"");x.language=rows[i].language||x.language||"";x.provider="coflix";if(q.transport==="tv"){x.season=q.season;x.episode=q.episode}out.push(x)}}return out}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q),als=aliases(md);if(!als.length)return[];var candidates=await search(als);if(!candidates.length)return[];for(var i=0;i<candidates.length&&i<5;i++){var cand=candidates[i],epId=q.transport==="movie"?cand.epId:await episodeId(cand.slug,q.episode);if(!epId)continue;var rows=await playerRows(epId,cand.language);if(!rows.length)continue;var streams=await terminal(rows,c.base+"/film/"+cand.slug+"/",q);if(streams.length)return streams}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"coflix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg={"base":"https://coflix.wiki","userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}
    cfg.update(dict(options or {}))
    cfg["base"]=str(cfg.get("base") or "").rstrip("/")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"coflix-search-film-episode-player-v1",
        "identity":"core-tmdb-aliases-provider-local-catalogue",
        "semanticLanes":["movie","tv","anime"],
        "animeTransport":"tv",
        "runtimeResolverRegistration":True,
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
