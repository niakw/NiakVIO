#!/usr/bin/env python3
"""NiakVIO-owned WookaFR current-site runtime.

Observable contract only:
TMDB metadata -> current Wooka search/detail -> optional episode page -> all
player/embed seeds -> bounded shared media crawl. A failing player host does not
prevent later discovered seeds from being tried. No upstream JavaScript is
embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WOOKAFR.CURRENT.RUNTIME.V2"
MARKER = "NIAKVIO_WOOKAFR_CURRENT_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_WOOKAFR_CURRENT_RUNTIME_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[’'\x60]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}
 var type=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.semanticType||x.mediaType||"movie").toLowerCase();if(type==="series")type="tv";if(type!=="movie"&&type!=="tv")return null;
 var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
 return{id:id,type:type,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||x.tmdbMetadata||x.fixtureMetadata||null}}
function projected(v){if(v&&v.state==="ok"&&v.metadata)v=v.metadata;return v&&typeof v==="object"?v:null}
async function meta(q){var m=projected(q.metadata);if(!m)try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function")m=projected(await fn({tmdbId:q.id,mediaType:q.type,tmdbNamespace:q.type}))}catch(_e){}if(!m)return null;
 var vals=[m.title,m.name,m.original_title,m.original_name],alt=m.alternative_titles&&(m.alternative_titles.titles||m.alternative_titles.results||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)vals.push(alt[i]&&(alt[i].title||alt[i].name));
 var date=s(q.type==="movie"?(m.release_date||m.first_air_date):(m.first_air_date||m.release_date)),year=(date.match(/^(\d{4})/)||[])[1]||s(m.year),names=[];for(var j=0;j<vals.length;j++){var z=s(vals[j]);if(z&&names.indexOf(z)<0)names.push(z)}
 return names.length?{title:names[0],aliases:names.slice(0,6),year:/^\d{4}$/.test(year)?year:""}:null}
function headers(ref){var h={"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function doc(url,ref){try{var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||r.ok===false)return null;return{url:s(r.url)||url,text:await r.text(),status:Number(r.status)||200}}catch(_e){return null}}
function abs(href,base){try{return new URL(href,base).href}catch(_e){return""}}
function anchors(html,base){var out=[],re=/<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<180){var u=abs(m[1],base),label=s(String(m[2]||"").replace(/<[^>]+>/g," ").replace(/&nbsp;/gi," "));if(u)out.push({url:u,label:label})}return out}
function score(row,m,q){var z=norm((row.label||"")+" "+(row.url||"")),t=norm(m.title);if(!t||!z)return 0;var v=0;if(z.indexOf(t)>=0)v+=100;var parts=t.split(" ").filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<parts.length;i++)if(z.indexOf(parts[i])>=0)hit++;v+=Math.round(50*hit/Math.max(1,parts.length));if(m.year&&z.indexOf(m.year)>=0)v+=25;if(q.type==="tv"&&/(?:serie|series|saison|episode)/i.test(z))v+=10;return v}
function candidateDetail(u,base){try{var a=new URL(u),b=new URL(base);if(a.origin!==b.origin)return false;return /\/streaming\//i.test(a.pathname)&&!/\/streaming\/(?:episodes?|years?|genres?|categories?)\/?$/i.test(a.pathname)}catch(_e){return false}}
async function searchAt(base,m,q){base=base.replace(/\/$/,"");for(var ai=0;ai<m.aliases.length;ai++){var name=m.aliases[ai],paths=["/?s="+encodeURIComponent(name),"/search/"+encodeURIComponent(slug(name))+"/"];for(var pi=0;pi<paths.length;pi++){var p=await doc(base+paths[pi],base+"/");if(!p)continue;var rows=anchors(p.text,p.url).filter(function(x){return candidateDetail(x.url,base)}),best=null,bestScore=0;for(var i=0;i<rows.length;i++){var sc=score(rows[i],m,q);if(sc>bestScore){best=rows[i];bestScore=sc}}if(best&&bestScore>=c.minIdentityScore){var d=await doc(best.url,p.url);if(d)return d}}}
 var sl=slug(m.title),fallbacks=q.type==="tv"?["/streaming/series/"+sl+"/","/streaming/"+sl+"/"]:["/streaming/"+sl+"/","/streaming/aventure/"+sl+"/"];for(var fi=0;fi<fallbacks.length;fi++){var f=await doc(base+fallbacks[fi],base+"/");if(f)return f}return null}
function episodeScore(row,q){var z=norm((row.label||"")+" "+(row.url||"")),s1=Number(q.season)||1,e1=Number(q.episode)||1,v=0;if(new RegExp("(?:saison|season|s)[^0-9]*0?"+s1+"\\b","i").test(z))v+=60;if(new RegExp("(?:episode|ep|e)[^0-9]*0?"+e1+"\\b","i").test(z))v+=80;if(new RegExp("(?:saison|season)[-_ ]*0?"+s1+"[-_ ]*(?:episode|ep)[-_ ]*0?"+e1,"i").test(z))v+=80;return v}
async function episodePage(detail,q){if(q.type!=="tv")return detail;var rows=anchors(detail.text,detail.url),best=null,bestScore=0;for(var i=0;i<rows.length;i++){if(!/\/(?:episodes?|streaming)\//i.test(rows[i].url))continue;var sc=episodeScore(rows[i],q);if(sc>bestScore){best=rows[i];bestScore=sc}}if(best&&bestScore>=80){var p=await doc(best.url,detail.url);if(p)return p}
 var base="";try{base=new URL(detail.url).origin}catch(_e){}if(base){var sl=(detail.url.match(/\/streaming\/(?:series\/)?([^/?#]+)\/?$/i)||[])[1]||"";if(sl){var guesses=["/streaming/episodes/"+sl+"-saison-"+q.season+"-episode-"+q.episode+"/","/episodes/"+sl+"-saison-"+q.season+"-episode-"+q.episode+"/"];for(var gi=0;gi<guesses.length;gi++){var gdoc=await doc(base+guesses[gi],detail.url);if(gdoc)return gdoc}}}return detail}
function media(u){return /\.(?:m3u8|mpd|mp4|m4v|mkv|webm)(?:[?#]|$)/i.test(s(u))}
function bad(u){return /(?:googleads|doubleclick|googlesyndication|googletagmanager|facebook\.com\/plugins|cloudflareinsights|youtube\.com)/i.test(s(u))}
function playerSeeds(page){var out=[],seen={};function add(raw){var u=abs(raw,page.url);if(!u||bad(u)||seen[u])return;try{var a=new URL(u),b=new URL(page.url),x=(a.hostname+a.pathname).toLowerCase();if(a.origin!==b.origin||media(u)||/(?:embed|player|video|watch|stream|playlist|lecteurvideo|vidmoly|vidzy|streamtape|sendvid|vidoza|uqload|voe|sibnet|dailymotion|up4fun|lulustream|luluvid|filemoon|moonplayer)/i.test(x)){seen[u]=1;out.push(u)}}catch(_e){}}
 var h=page.text||"",re=/<iframe\b[^>]*(?:src|data-src)\s*=\s*["']([^"']+)["']/gi,m;while((m=re.exec(h))!==null)add(m[1]);var re2=/(?:src|url|file|embedUrl|playerUrl|data-src)\s*[:=]\s*["']([^"']+)["']/gi;while((m=re2.exec(h))!==null)add(m[1]);var rows=anchors(h,page.url);for(var i=0;i<rows.length;i++)add(rows[i].url);return out.slice(0,c.maxPlayers)}
function row(u,ref){return{name:"Wookafr",title:"Wookafr",url:u,provider:"wookafr",headers:{"Referer":ref||"","User-Agent":c.userAgent},isDirect:media(u)}}
async function crawlOne(seed,ref){if(media(seed))return[row(seed,ref)];try{if(typeof _crawlDirectMedia==="function"){var got=await _crawlDirectMedia([seed],ref,c.crawlDepth);if(Array.isArray(got)&&got.length){var out=[];for(var i=0;i<got.length;i++){var x=got[i]||{},u=s(x.url);if(!u)continue;var y=Object.assign({},x);y.url=u;y.provider="wookafr";y.name="Wookafr";if(!y.headers)y.headers={"Referer":seed,"User-Agent":c.userAgent};out.push(y)}return out}}}catch(_e){}return[]}
async function resolve(a){var q=req(a);if(!q)return[];var m=await meta(q);if(!m)return[];for(var bi=0;bi<c.bases.length;bi++){var detail=await searchAt(c.bases[bi],m,q);if(!detail)continue;var page=await episodePage(detail,q),seeds=playerSeeds(page),out=[],seen={};for(var si=0;si<seeds.length&&out.length<c.maxStreams;si++){var rows=await crawlOne(seeds[si],page.url);for(var ri=0;ri<rows.length&&out.length<c.maxStreams;ri++){var u=s(rows[ri]&&rows[ri].url);if(u&&!seen[u]){seen[u]=1;out.push(rows[ri])}}}if(out.length)return out}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioWookafrCurrentV2)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioWookafrCurrentV2=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"wookafr",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "bases": ["https://wookafr.boston", "https://wookafr.center", "https://wookafr.plus"],
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "minIdentityScore": 80,
        "maxPlayers": 16,
        "maxStreams": 12,
        "crawlDepth": 4,
    }
    cfg.update(dict(options or {}))
    bases = []
    for value in cfg.get("bases") or []:
        base = str(value or "").rstrip("/")
        if base.startswith(("http://", "https://")) and base not in bases:
            bases.append(base)
    if not bases:
        raise ValueError(f"{MANAGED_FIX_ID}: at least one http(s) base is required")
    cfg["bases"] = bases[:8]
    cfg["minIdentityScore"] = max(50, min(int(cfg.get("minIdentityScore") or 80), 180))
    cfg["maxPlayers"] = max(1, min(int(cfg.get("maxPlayers") or 16), 24))
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 12), 24))
    cfg["crawlDepth"] = max(1, min(int(cfg.get("crawlDepth") or 4), 5))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "wookafr-current-multiplayer-v2",
            "identity": "tmdb-title-year-bounded",
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
            "terminalResolution": "all-player-seeds-sequential-bounded-crawl",
            "semanticLanes": ["movie", "tv"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
