#!/usr/bin/env python3
"""NiakVIO-owned StreamZo current-site runtime.

Clean-room contract from observable site behavior:
TMDB/Core metadata -> /api/web/suggest exact href -> movie/series page -> embed
page -> direct HLS/MP4 URL. No upstream JavaScript is embedded or executed.
Core remains owner of final media/identity validation.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.STREAMZO.RUNTIME.V1"
MARKER = "NIAKVIO_STREAMZO_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_STREAMZO_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function uniq(a){return Array.from(new Set((a||[]).filter(Boolean)))}
function norm(v){return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();if(raw==="series")raw="tv";if(!["movie","tv","anime"].includes(raw))return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return null;return{type:raw,transport:raw==="movie"?"movie":"tv",tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:ctx.episode))||1}}
function hdr(ref,accept){var h={"User-Agent":c.ua,"Accept":accept||"text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function response(url,opt){try{var o=Object.assign({redirect:"follow",credentials:"include"},opt||{});o.headers=Object.assign(hdr(o.referer||""),o.headers||{});delete o.referer;var r=typeof _fetch==="function"?await _fetch(url,o):await g.fetch(url,o);return r||null}catch(_e){return null}}
async function text(url,opt){var r=await response(url,opt);if(!r||r.ok===false)return null;try{return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
async function jsonReq(url,opt){var r=await response(url,Object.assign({headers:{Accept:"application/json,*/*"}},opt||{}));if(!r||r.ok===false)return null;try{return await r.json()}catch(_e){try{return JSON.parse(await r.text())}catch(_x){return null}}}
async function metadata(q){try{var fn=g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.transport,tmdbNamespace:q.transport}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var ctx=g.__nuvioMediaContext||{};return ctx.tmdbMetadata||ctx.fixtureMetadata||null}catch(_e){return null}}
function titles(m){var a=[];if(m){a.push(m.title,m.name,m.original_title,m.original_name);if(Array.isArray(m.aliases))a=a.concat(m.aliases);if(m.alternative_titles&&Array.isArray(m.alternative_titles.titles))for(var i=0;i<m.alternative_titles.titles.length;i++)a.push(m.alternative_titles.titles[i]&&m.alternative_titles.titles[i].title)}return uniq(a.map(s)).slice(0,5)}
function year(m){var raw=s(m&&(m.release_date||m.first_air_date||m.year));var z=/^(\d{4})/.exec(raw);return z?Number(z[1]):0}
function score(wanted,row,wantSeries,wantYear){var cand=s(row&&(row.titre||row.title||(row.slug||"").replace(/-/g," "))),a=norm(wanted),b=norm(cand);if(!a||!b)return-999;var n=0;if(a===b)n=100;else if(b===a+" vostfr")n=95;else if(a.length>=5&&(a.includes(b)||b.includes(a)))n=70;else{var ta=a.split(" ").filter(Boolean),tb=b.split(" ").filter(Boolean),hit=0;for(var i=0;i<ta.length;i++)if(tb.includes(ta[i]))hit++;var ratio=hit/Math.max(ta.length,tb.length,1);if(ratio>=.6)n=Math.round(40+ratio*30);else if(ratio>=.4)n=25}if(n<=0)return 0;var series=row&&(row.content_type==="series"||row.kind==="series");n+=series===wantSeries?25:-60;var y=Number(row&&row.year)||0;if(y&&wantYear){var d=Math.abs(y-wantYear);if(d===0)n+=30;else if(d===1)n+=15;else if(d>2)n-=25}return n}
async function suggest(tt,q,m){var want=q.type!=="movie",y=year(m),best=null,bestScore=-999;for(var i=0;i<Math.min(3,tt.length);i++){var list=await jsonReq(c.base+"/api/web/suggest?q="+encodeURIComponent(tt[i]),{referer:c.base+"/"});list=list&&Array.isArray(list.suggestions)?list.suggestions:[];for(var j=0;j<list.length;j++){var row=list[j];if(!row||typeof row.href!=="string"||row.href.charAt(0)!=="/")continue;var sc=score(tt[i],row,want,y);if(sc>bestScore){bestScore=sc;best=row}}if(bestScore>=110)break}if(!best||bestScore<45)return null;return{href:best.href,kind:(best.content_type==="series"||best.kind==="series")?"series":"movie",quality:s(best.resolution||best.quality||"HD")}}
function abs(v,base){try{return new URL(v,base).toString()}catch(_e){return""}}
function movieEmbeds(html){var ps=[/id=["']player-facade["'][^>]*data-embed=["']([^"']+)["']/gi,/data-embed=["']([^"']+)["'][^>]*id=["']player-facade["']/gi,/<iframe[^>]*id=["']video-frame["'][^>]*src=["']([^"']+)["']/gi,/<iframe[^>]*src=["']([^"']*\/(?:embed|player|watch)\/[^"']+)["']/gi],out=[],seen={};for(var i=0;i<ps.length&&out.length<8;i++){var m;while((m=ps[i].exec(html||""))!==null&&out.length<8){var u=s(m[1]);if(u&&!seen[u]){seen[u]=1;out.push({embed:u,player:"Lecteur "+(out.length+1)})}}}return out}
function attr(el,name){var q=new RegExp(name+"\\s*=\\s*([\\\"'])([\\s\\S]*?)\\1","i").exec(el);if(q)return q[2];var m=new RegExp(name+"\\s*=\\s*([^\\s>]+)","i").exec(el);return m?m[1]:""}
function episodes(html,q){var b=(html||"").match(/<button\b[^>]*class=["'][^"']*\bsd-ep\b[^"']*["'][^>]*>/gi)||[],out=[],seen={};for(var i=0;i<b.length&&out.length<8;i++){var st=Number(attr(b[i],"data-season")),ep=Number(attr(b[i],"data-ep")),src=attr(b[i],"data-src");if(st!==q.season||ep!==q.episode||!src)continue;var lr=s(attr(b[i],"data-lang")).toLowerCase(),lang=lr==="vostfr"?"VOSTFR":lr==="vf"?"VF":(lr?lr.toUpperCase():"VF"),key=lang+"|"+src;if(seen[key])continue;seen[key]=1;var label=s(attr(b[i],"data-player")||attr(b[i],"data-server")||attr(b[i],"data-name")||attr(b[i],"title")||attr(b[i],"aria-label"))||("Lecteur "+(out.length+1));out.push({embed:src,lang:lang,player:label})}out.sort(function(a,b){return(a.lang==="VF"?0:1)-(b.lang==="VF"?0:1)});return out.slice(0,8)}
function decode(body){return s(body).replace(/\\u0026/gi,"&").replace(/\\u([0-9a-fA-F]{4})/g,function(_m,h){return String.fromCharCode(parseInt(h,16))}).replace(/&amp;/g,"&").replace(/\\\//g,"/")}
function mediaUrls(body){body=decode(body);var out=[],seen={},ps=[/https?:\/\/[^"'<>\s\\]+\.m3u8[^"'<>\s\\]*/gi,/https?:\/\/[^"'<>\s\\]+\.mp4[^"'<>\s\\]*/gi];for(var p=0;p<ps.length;p++){var m;while((m=ps[p].exec(body))!==null){var u=m[0].replace(/[,;]+$/,'');if(u&&!seen[u]){seen[u]=1;out.push(u)}}}out.sort(function(a,b){function k(x){return/master\.m3u8/i.test(x)?0:/\.m3u8/i.test(x)?1:2}return k(a)-k(b)});return out}
function stream(u,lang,quality,q,player){var episodic=q&&q.type!=="movie",tag=episodic?(" | S"+String(q.season||1).padStart(2,"0")+"E"+String(q.episode||1).padStart(2,"0")):"",label=s(player);var row={name:"StreamZo | "+lang,title:"StreamZo | "+lang+tag,url:u,quality:quality||"HD",language:lang,provider:"streamzo",isDirect:true,headers:{Referer:c.base+"/","User-Agent":c.ua}};if(label){row.player=label;row.sourceLabel=label;row.sourceName="StreamZo · "+label}if(episodic){row.season=Number(q.season)||1;row.episode=Number(q.episode)||1}return row}
async function resolveEmbed(embed,lang,quality,ref,q,player){var full=abs(embed,c.base);if(!full)return[];var page=await text(full,{referer:ref||c.base+"/"});if(!page)return[];var urls=mediaUrls(page.text),out=[],seen={};for(var i=0;i<Math.min(6,urls.length)&&out.length<8;i++){var row=stream(urls[i],lang,quality,q,player),resolved=[];try{if(typeof _crawlDirectMedia==="function"){var z=await _crawlDirectMedia([urls[i]],full,1);if(Array.isArray(z)&&z.length)resolved=z}}catch(_e){}if(!resolved.length)resolved=[row];for(var j=0;j<resolved.length&&out.length<8;j++){var x=resolved[j];if(!x||!x.url||seen[x.url])continue;seen[x.url]=1;x.name=x.name||row.name;x.title=x.title||row.title;x.language=x.language||lang;x.provider="streamzo";x.headers=Object.assign({},row.headers,x.headers||{});if(player){x.player=x.player||player;x.sourceLabel=x.sourceLabel||player;x.sourceName=x.sourceName||("StreamZo · "+player)}if(q&&q.type!=="movie"){x.season=Number(q.season)||1;x.episode=Number(q.episode)||1;if(!/S\d+E\d+/i.test(String(x.title||"")))x.title=String(x.title||row.title)+" | S"+String(q.season||1).padStart(2,"0")+"E"+String(q.episode||1).padStart(2,"0")}out.push(x)}}return out}
async function resolve(a,_ctx){var q=req(a);if(!q)return[];var m=await metadata(q),tt=titles(m);if(!tt.length)return[];var hit=await suggest(tt,q,m);if(!hit)return[];var pageUrl=abs(hit.href,c.base),page=await text(pageUrl,{referer:c.base+"/"});if(!page)return[];if(hit.kind==="movie"){var embeds=movieEmbeds(page.text),movieOut=[],movieSeen={},movieLang=/-vostfr(?:\/|$|\?)/i.test(hit.href)?"VOSTFR":"VF";for(var mi=0;mi<embeds.length&&movieOut.length<8;mi++){var movieRows=await resolveEmbed(embeds[mi].embed,movieLang,hit.quality,page.url,q,embeds[mi].player);for(var mj=0;mj<movieRows.length&&movieOut.length<8;mj++){var movieRow=movieRows[mj];if(movieRow&&movieRow.url&&!movieSeen[movieRow.url]){movieSeen[movieRow.url]=1;movieOut.push(movieRow)}}}return movieOut}if(q.type==="movie")return[];var vars=episodes(page.text,q),out=[],seen={};for(var i=0;i<vars.length&&out.length<8;i++){var rows=await resolveEmbed(vars[i].embed,vars[i].lang,hit.quality,page.url,q,vars[i].player);for(var j=0;j<rows.length&&out.length<8;j++){if(rows[j]&&rows[j].url&&!seen[rows[j].url]){seen[rows[j].url]=1;out.push(rows[j])}}}return out.slice(0,8)}
try{g.__niakvioProviderRuntimeResolverV1={provider:"streamzo",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://streamzo.fr",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "streamzo-suggest-exact-href-v3-multiflux",
            "identity": "core-tmdb-metadata-to-suggest-title-year-type",
            "searchAuthority": "/api/web/suggest",
            "seriesEpisodeAuthority": "sd-ep-data-season-data-ep-data-src",
            "mediaExtraction": "all-distinct-embeds-and-direct-hls-mp4-up-to-8",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "tv", "anime"],
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
