#!/usr/bin/env python3
"""Clean provider-local Sekai sitemap/script runtime."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.SEKAI.RUNTIME.V1"
MARKER = "NIAKVIO_SEKAI_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_SEKAI_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function request(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"anime").toLowerCase();if(semantic==="series")semantic="tv";if(semantic!=="anime"&&semantic!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(!row)try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"});row=projected(r)}}catch(_e){}if(!row)return null;var counts={};if(Array.isArray(row.seasons))for(var i=0;i<row.seasons.length;i++){var z=row.seasons[i]||{},sn=Number(z.season_number),ec=Number(z.episode_count);if(sn>0&&ec>0)counts[sn]=ec}return{raw:row,seasonCounts:counts}}
function aliases(meta){var md=meta&&meta.raw;if(!md)return[];var out=[md.name,md.title,md.original_name,md.original_title],alt=md.alternative_titles&&(md.alternative_titles.results||md.alternative_titles.titles||md.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(out).slice(0,7)}
function episodeCandidates(q,meta){var out=[q.episode],offset=0,ok=true;for(var sn=1;sn<q.season;sn++){var count=Number(meta&&meta.seasonCounts&&meta.seasonCounts[sn]);if(!count){ok=false;break}offset+=count}if(ok&&offset+q.episode!==q.episode)out.push(offset+q.episode);return out}
function headers(){return{"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml,text/plain,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Referer":c.base+"/"}}
async function text(url){try{var r=await g.fetch(url,{headers:headers()});if(!r||!r.ok)return"";return await r.text()}catch(_e){return""}}
function sim(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 100;if(a.length>=5&&(a.indexOf(b)>=0||b.indexOf(a)>=0))return 70;var aa=a.split(/\s+/),bb=b.split(/\s+/),hit=0;for(var i=0;i<aa.length;i++)if(aa[i].length>=3&&bb.indexOf(aa[i])>=0)hit++;var ratio=hit/Math.max(aa.length,bb.length);return ratio>=.6?Math.round(45+ratio*30):0}
async function sitemap(){var xml=await text(c.base+"/sitemap.xml"),out=[],re=/<loc>([^<]+)<\/loc>/gi,m;while((m=re.exec(xml))!==null){var p=s(m[1]).replace(/^https?:\/\/[^/]+/i,"").split("?")[0].replace(/^\/+|\/+$/g,"");if(!p||p==="android"||p.indexOf(".")>=0||out.indexOf(p)>=0)continue;out.push(p)}return out}
function matches(slugs,als){var out=[];for(var i=0;i<slugs.length;i++){var label=slugs[i].replace(/-/g," "),best=0;for(var j=0;j<als.length;j++)best=Math.max(best,sim(als[j],label));if(best>=45)out.push({slug:slugs[i],score:best})}out.sort(function(a,b){return b.score-a.score});return out}
function scripts(html){var out=[],re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi,m;while((m=re.exec(html||""))!==null)out.push(m[1]);return out}
function stripComments(src){return s(src).replace(/\/\*[\s\S]*?\*\//g,"").replace(/(^|[^:])\/\/.*$/gm,"$1")}
function vars(src){src=stripComments(src);var out={},m,re=/(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*atob\(\s*["']([^"']+)["']\s*\)/g;while((m=re.exec(src))!==null){try{out[m[1]]=atob(m[2])}catch(_e){}}re=/(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*["'](https?:\/\/[^"']+)["']/g;while((m=re.exec(src))!==null)if(!out[m[1]])out[m[1]]=m[2];return out}
function exprValue(expr,v,indexVar,index){var parts=s(expr).split("+"),out="";for(var i=0;i<parts.length;i++){var p=s(parts[i]),q=p.match(/^["']([\s\S]*)["']$/);if(q){out+=q[1];continue}if(/^\d+$/.test(p)){out+=p;continue}if(p===indexVar||p==="num"){out+=String(index);continue}if(v[p]!=null){out+=v[p];continue}return""}return out}
function available(src,episodes){var clean=stripComments(src),m=clean.match(/AVAILABLE_EPISODES\s*=\s*Object\.freeze\(\s*(\[[\s\S]*?\])\s*\)/)||clean.match(/AVAILABLE_EPISODES\s*=\s*(\[[\s\S]*?\])\s*;/);if(!m)return[];var arr=[];try{arr=JSON.parse(m[1])}catch(_e){return[]}if(!Array.isArray(arr))return[];var v=vars(clean),base=v.STREAM_MAIN_BASE_URL||v.STREAM_ORIGIN||"",film=(v.FILM_STREAM_ORIGIN||"").replace(/\/$/,"");if(!base)return[];var root=s(base).replace(/\/$/,""),prefix=(clean.match(/([A-Za-z0-9_-]+)-\$\{episodeNumber\}\.mp4/)||[])[1]||"",out=[];for(var i=0;i<episodes.length;i++){var ep=episodes[i],row=arr.find(function(x){return Number(x&&x.number)===ep});if(!row)continue;var file=s(row.file)||(prefix?prefix+"-"+ep:"");if(!file)continue;if(row.kind==="film"&&film){out.push({url:film+"/"+file+".mp4",quality:"1080p"});continue}out.push({url:root+"/"+file+".mp4",quality:"1080p"});out.push({url:root+"/low/"+file+".mp4",quality:"480p"})}return out}
function lastCounters(src){var out={},m,re=/(?:var|let|const)\s+(last[A-Za-z0-9_$]*)\s*=\s*(\d+)/g;while((m=re.exec(src))!==null)out[m[1]]=Number(m[2]);re=/"lastEpisode"\s*:\s*(\d+)/g;while((m=re.exec(src))!==null){var before=src.slice(Math.max(0,m.index-450),m.index),v=before.match(/([A-Za-z_$][\w$]*)\s*=\s*\(?\s*\{[^{}]*$/);if(v)out[v[1]+".lastEpisode"]=Number(m[1])}var rr=/(?:var|let|const)\s+(last[A-Za-z0-9_$]*)\s*=\s*(?:Number\s*\(\s*)?([A-Za-z_$][\w$]*)\.lastEpisode\s*(?:\|\|\s*(\d+)\s*)?\)?/g;while((m=rr.exec(src))!==null)out[m[1]]=out[m[2]+".lastEpisode"]||Number(m[3]||0);return out}
function loopEpisodeRows(clean,v,keys,sib){var out=[],seen={},last=lastCounters(clean),re=/for\s*\(\s*(?:var\s+|let\s+)?([A-Za-z_$][\w$]*)\s*=\s*(\d+)\s*;\s*\1\s*<=\s*([A-Za-z_$][\w$]*|\d+)\s*;\s*\1(?:\+\+|\s*\+=\s*1)\s*\)\s*\{([\s\S]{0,9000}?)\}/g,m;while((m=re.exec(clean))!==null){var iv=m[1],from=Number(m[2]),to=/^\d+$/.test(m[3])?Number(m[3]):Number(last[m[3]]||0);if(!to)continue;for(var key in keys){var n=Number(key);if(!Number.isFinite(n)||n<from||n>to)continue;var ar=new RegExp("([A-Za-z_$][\\w$]*)\\s*\\[\\s*"+iv+"\\s*\\]\\s*=\\s*([^;]{1,700})\\s*;","g"),a;while((a=ar.exec(m[4]))!==null){if(!/^episode/i.test(a[1]))continue;var u=exprValue(a[2],v,iv,n);if(!u)continue;if(!/^https?:/i.test(u)&&/^\d+$/.test(u)&&sib)u=sib+u;if(!/^https?:/i.test(u)||seen[u])continue;seen[u]=1;out.push({url:u,quality:/hd/i.test(a[1])?"1080p":/low/i.test(a[1])?"480p":"720p"})}}}return out}
function assignments(src,episodes){var clean=stripComments(src),v=vars(clean),mapping={},m,re=/numOriginale\s*\[\s*["']?(\d+)["']?\s*\]\s*=\s*([^;]{1,120})\s*;/g;while((m=re.exec(clean))!==null){var val=Number(exprValue(m[2],v,"",0));if(Number.isFinite(val))mapping[m[1]]=val}var keys={};for(var i=0;i<episodes.length;i++){keys[String(episodes[i])]=1;for(var k in mapping)if(mapping[k]===episodes[i])keys[k]=1}var sib="";for(var name in v)if(/sibnet/i.test(v[name])&&/php/i.test(v[name])){sib=v[name];break}var out=[],seen={};re=/([A-Za-z_$][\w$]*)\s*\[\s*["']?(\d+)["']?\s*\]\s*=\s*([^;]{1,500})\s*;/g;while((m=re.exec(clean))!==null){if(!/^episode/i.test(m[1])||!keys[m[2]])continue;var u=exprValue(m[3],v,"",Number(m[2]));if(!u)continue;if(!/^https?:/i.test(u)&&/^\d+$/.test(u)&&sib)u=sib+u;if(!/^https?:/i.test(u)||seen[u])continue;seen[u]=1;out.push({url:u,quality:/hd/i.test(m[1])?"1080p":/low/i.test(m[1])?"480p":"720p"})}var loops=loopEpisodeRows(clean,v,keys,sib);for(var j=0;j<loops.length;j++)if(!seen[loops[j].url]){seen[loops[j].url]=1;out.push(loops[j])}return out}
function blocked(u){return /mugiwara\.xyz|upvid\.co|opvid\.org|jetload/i.test(u)}
function sources(html,episodes){var out=[],seen={},ss=scripts(html);for(var i=0;i<ss.length;i++){var rows=available(ss[i],episodes).concat(assignments(ss[i],episodes));for(var j=0;j<rows.length;j++)if(rows[j].url&&!blocked(rows[j].url)&&!seen[rows[j].url]){seen[rows[j].url]=1;out.push(rows[j])}}return out}
function subpages(html,slug){var out=[],seen={},re=/href=["']([^"']+)["']/gi,m;while((m=re.exec(html||""))!==null&&out.length<35){var raw=s(m[1]).split("?")[0];if(!raw||raw[0]==="#"||/^mailto:|^https?:/i.test(raw)||/\.(?:css|js|png|jpe?g|webp|gif|svg|ico|woff2?)$/i.test(raw))continue;var path=raw.replace(/^\/+|\/+$/g,""),first=path.split("/")[0];if(!(first===slug||first.indexOf(slug+"-")===0))continue;var u=c.base+"/"+path;if(!seen[u]){seen[u]=1;out.push(u)}}return out}
async function terminal(rows,q){var out=[],seen={};rows.sort(function(a,b){return Number((b.quality||"").replace(/\D/g,""))-Number((a.quality||"").replace(/\D/g,""))});for(var i=0;i<rows.length&&out.length<4;i++){var u=rows[i].url;if(!u||seen[u])continue;seen[u]=1;if(/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(u)){out.push({name:"Sekai",title:"Sekai "+rows[i].quality+" [VOSTFR]",url:u,quality:rows[i].quality,language:"VOSTFR",provider:"sekai",season:q.season,episode:q.episode,isDirect:true,headers:{Referer:c.base+"/","User-Agent":c.userAgent}});continue}var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([u],c.base+"/",2)}catch(_e){direct=[]}if(Array.isArray(direct))for(var j=0;j<direct.length&&out.length<4;j++){var x=direct[j];if(!x||!/^https?:/i.test(s(x.url)))continue;var z=Object.assign({},x);z.name="Sekai";z.title="Sekai "+(z.quality||rows[i].quality||"HD")+" [VOSTFR]";z.language="VOSTFR";z.provider="sekai";z.season=q.season;z.episode=q.episode;out.push(z)}}return out}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q),als=aliases(md);if(!als.length)return[];var slugs=await sitemap(),cands=matches(slugs,als);if(!cands.length)return[];var eps=episodeCandidates(q,md);for(var i=0;i<cands.length&&i<3;i++){var main=c.base+"/"+cands[i].slug,html=await text(main);if(html.length<200)continue;var pages=[main].concat(subpages(html,cands[i].slug));for(var j=0;j<pages.length&&j<25;j++){var body=j===0?html:await text(pages[j]);if(body.length<100)continue;var rows=sources(body,eps);if(rows.length){var streams=await terminal(rows,q);if(streams.length)return streams}}}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"sekai",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg={"base":"https://sekai.one","userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36"}
    cfg.update(dict(options or {}))
    cfg["base"]=str(cfg.get("base") or "").rstrip("/")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"sekai-sitemap-script-family-v1",
        "identity":"core-tmdb-aliases-plus-season-count-absolute-episode",
        "semanticLanes":["anime"],
        "runtimeResolverRegistration":True,
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
