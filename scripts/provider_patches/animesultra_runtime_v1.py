#!/usr/bin/env python3
"""Clean provider-local AnimesUltra DLE/full-story runtime."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID="PROVIDER.ANIMESULTRA.RUNTIME.V1"
MARKER="NIAKVIO_ANIMESULTRA_RUNTIME_V1"

WRAPPER=r'''
/* NIAKVIO_ANIMESULTRA_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function request(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"anime").toLowerCase();if(semantic==="series")semantic="tv";if(semantic!=="anime"&&semantic!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"});return projected(r)}}catch(_e){}return null}
function aliases(md){if(!md)return[];var out=[md.name,md.title,md.original_name,md.original_title],alt=md.alternative_titles&&(md.alternative_titles.results||md.alternative_titles.titles||md.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(out).slice(0,6)}
function headers(json){var h={"User-Agent":c.userAgent,"Accept":json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(json)h["X-Requested-With"]="XMLHttpRequest";return h}
async function getText(url){try{var r=await g.fetch(url,{headers:headers(false)});if(!r||!r.ok)return"";return await r.text()}catch(_e){return""}}
async function getJson(url){try{var r=await g.fetch(url,{headers:headers(true)});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function visible(v){return s(v).replace(/<[^>]+>/g," ").replace(/&amp;/gi,"&").replace(/\s+/g," ").trim()}
function score(label,query,season){var a=norm(s(label).replace(/\s+(?:VF|VOSTFR)$/i,"")),b=norm(query);if(!a||!b)return 0;var sc=a===b?150:(a.indexOf(b)>=0||b.indexOf(a)>=0?100:0);if(!sc){var aw=a.split(/\s+/),bw=b.split(/\s+/),hit=0;for(var i=0;i<bw.length;i++)if(bw[i].length>2&&aw.indexOf(bw[i])>=0)hit++;sc=bw.length?Math.round(hit/bw.length*60):0}var m=(s(label)).match(/(?:saison|season|\bS)(\d+)/i);if(m&&season)sc+=Number(m[1])===season?40:-25;return sc}
function resultRows(html,query,season){var out=[],seen={},re=/<a[^>]+class=["'][^"']*film-poster-ahref[^"']*item-qtip[^"']*["'][^>]*>/gi,m;while((m=re.exec(html||""))!==null){var tag=m[0],href=(tag.match(/href=["']([^"']+)["']/i)||[])[1]||"",title=(tag.match(/title=["']([^"']+)["']/i)||[])[1]||"",id=(tag.match(/data-id=["']([^"']+)["']/i)||[])[1]||"";if(!href||!title||/\+ item\.name \+/i.test(title))continue;var key=id||href;if(seen[key])continue;seen[key]=1;out.push({url:/^https?:/i.test(href)?href:c.base+href,title:title,newsId:id,score:score(title,query,season)})}if(!out.length){var r2=/<a[^>]+href=["']([^"']*-au\.html)["'][^>]*?(?:title=["']([^"']+)["'])?[^>]*>/gi,x;while((x=r2.exec(html||""))!==null){var label=x[2]||visible(x[0]),u=/^https?:/i.test(x[1])?x[1]:c.base+x[1];if(label&&u)out.push({url:u,title:label,newsId:"",score:score(label,query,season)})}}out.sort(function(a,b){return b.score-a.score});return out}
async function search(als,season){for(var i=0;i<als.length&&i<5;i++){var html=await getText(c.base+"/index.php?do=search&subaction=search&story="+encodeURIComponent(als[i]));var rows=resultRows(html,als[i],season).filter(function(r){return r.score>=30});if(rows.length)return rows[0]}return null}
function newsId(row){if(row.newsId)return row.newsId;var m=s(row.url).match(/\/(\d+)-/);return m?m[1]:""}
function fullStory(html){if(!html)return{episodes:[],players:[],links:[]};var episodes=[],re=/<[^>]*class=["'][^"']*ep-item[^"']*["'][^>]*>/gi,m;while((m=re.exec(html))!==null){var tag=m[0],num=Number((tag.match(/data-number=["'](\d+)["']/i)||[])[1]||0),id=(tag.match(/data-id=["']([^"']+)["']/i)||[])[1]||"",href=(tag.match(/href=["']([^"']+)["']/i)||[])[1]||"";if(num)episodes.push({num:num,id:id,href:href})}
  var players=[],pr=/<div\s+id=["']content_player_(\d+)([a-z]*)["'][^>]*>\s*([^<]+)\s*<\/div>/gi,p;while((p=pr.exec(html))!==null){players.push({id:p[1],suffix:p[2]||"",value:s(p[3])})}
  return{episodes:episodes,players:players}}
async function story(id){var data=await getJson(c.base+"/engine/ajax/full-story.php?newsId="+encodeURIComponent(id));return fullStory(data&&data.html)}
function candidateShells(parsed,episode){var out=[],epIndex=-1;for(var i=0;i<parsed.episodes.length;i++)if(parsed.episodes[i].num===episode){epIndex=i;break}
  if(epIndex>=0){var plain=parsed.players.filter(function(p){return !p.suffix&&/^\d+$/.test(p.value)});if(epIndex<plain.length)out.push({url:"https://video.sibnet.ru/shell.php?videoid="+plain[epIndex].value,language:"VOSTFR"})}
  return out}
async function episodeFallback(parsed,episode){var ep=parsed.episodes.find(function(e){return e.num===episode&&e.href});if(!ep)return[];var url=/^https?:/i.test(ep.href)?ep.href:c.base+ep.href,html=await getText(url),out=[],re=/<[^>]*class=["'][^"']*server-item[^"']*["'][^>]*>/gi,m;while((m=re.exec(html))!==null){var tag=m[0],u=(tag.match(/data-embed=["']([^"']+)["']/i)||[])[1]||"";if(/^https?:/i.test(u)&&!/sendvid\.com|vidstream\.pro/i.test(u))out.push({url:u,language:"VOSTFR"})}if(!out.length){var fr=/<iframe[^>]+src=["']([^"']+)["']/gi,x;while((x=fr.exec(html))!==null&&out.length<6){var u=x[1];if(/^https?:/i.test(u)&&!/google|disqus|sendvid\.com|vidstream\.pro/i.test(u))out.push({url:u,language:"VOSTFR"})}}return out}
async function terminal(rows,referer,q){var out=[],seen={};for(var i=0;i<rows.length&&i<6;i++){var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([rows[i].url],referer,2)}catch(_e){direct=[]}if(!Array.isArray(direct))continue;for(var j=0;j<direct.length&&out.length<4;j++){var row=direct[j];if(!row||!/^https?:/i.test(s(row.url))||seen[row.url])continue;seen[row.url]=1;var x=Object.assign({},row);x.name="AnimesUltra";x.title="AnimesUltra ["+rows[i].language+"]";x.language=rows[i].language;x.provider="animesultra";x.season=q.season;x.episode=q.episode;out.push(x)}}return out}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q),als=aliases(md);if(!als.length)return[];var hit=await search(als,q.season);if(!hit)return[];var id=newsId(hit);if(!id)return[];var parsed=await story(id);var shells=candidateShells(parsed,q.episode);if(!shells.length)shells=await episodeFallback(parsed,q.episode);if(!shells.length)return[];return await terminal(shells,hit.url,q)}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"animesultra",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text:str,options:dict[str,Any]|None=None,**_kwargs:Any)->str:
    cfg={"base":"https://animesultra.com","userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36"}
    cfg.update(dict(options or {}));cfg["base"]=str(cfg.get("base") or "").rstrip("/")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"animesultra-dle-full-story-sibnet-v1",
        "identity":"core-tmdb-aliases-anime-season-episode",
        "semanticLanes":["anime"],
        "runtimeResolverRegistration":True,
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
