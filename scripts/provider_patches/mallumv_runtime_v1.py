#!/usr/bin/env python3
"""NiakVIO-owned MalluMV current catalogue -> confirm -> internal runtime.

The runtime rebuilds only the observable HTTP contract:
TMDB metadata -> MalluMV search -> content page -> confirm -> internal page ->
bounded terminal-media crawl. No upstream JavaScript is embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MALLUMV.RUNTIME.V1"
MARKER = "NIAKVIO_MALLUMV_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MALLUMV_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/&(?:amp|quot|apos|#39|raquo);/g," ").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]);if(x&&!seen[x]){seen[x]=1;out.push(x)}}return out}
function visibleHtml(v){var src=String(v==null?"":v),out="",tag=false,quote="";for(var i=0;i<src.length;i++){var ch=src[i];if(tag){if(quote){if(ch===quote)quote=""}else if(ch==="\""||ch==="'")quote=ch;else if(ch===">")tag=false;continue}if(ch==="<"){tag=true;continue}out+=ch}return s(out.replace(/&nbsp;|&#160;/gi," ").replace(/&amp;/gi,"&").replace(/&quot;|&#34;/gi,'"').replace(/&#39;|&apos;/gi,"'"))}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}
 var type=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.semanticType||x.mediaType||"movie").toLowerCase();if(type==="series")type="tv";if(type!=="movie")return null;
 var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
 return{id:id,type:"movie",metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||x.tmdbMetadata||x.fixtureMetadata||null}}
function projected(v){if(v&&v.state==="ok"&&v.metadata)v=v.metadata;return v&&typeof v==="object"?v:null}
async function meta(q){var m=projected(q.metadata);if(!m)try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function")m=projected(await fn({tmdbId:q.id,mediaType:"movie",tmdbNamespace:"movie"}))}catch(_e){}if(!m)return null;var title=s(m.title||m.name||m.original_title||m.original_name),date=s(m.release_date||m.first_air_date),year=(date.match(/^(\d{4})/)||[])[1]||s(m.year);return title?{title:title,year:/^\d{4}$/.test(year)?year:""}:null}
function headers(ref){var h={"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function doc(url,ref){try{var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||r.ok===false)return null;return{url:s(r.url)||url,text:await r.text()}}catch(_e){return null}}
function abs(href,base){try{return new URL(href,base).href}catch(_e){return""}}
function anchors(html,base){var out=[],re=/<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<120){var u=abs(m[1],base),label=visibleHtml(m[2]);if(u)out.push({url:u,label:label})}return out}
function identityScore(row,m){var a=norm(m.title),b=norm((row.label||"")+" "+(row.url||""));if(!a||!b)return 0;if(b.indexOf(a)>=0)return 100;var aa=a.split(" ").filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<aa.length;i++)if(b.indexOf(aa[i])>=0)hit++;var score=Math.round(100*hit/Math.max(1,aa.length));if(m.year&&b.indexOf(m.year)>=0)score+=20;return score}
async function detail(m){var base=c.base.replace(/\/$/,""),search=await doc(base+"/search.php?q="+encodeURIComponent(m.title),base+"/");if(!search)return null;var rows=anchors(search.text,search.url).filter(function(x){return /\/movie\/\d+\/[^?#]+\.xhtml(?:[?#]|$)/i.test(x.url)}),best=null,bestScore=0;for(var i=0;i<rows.length;i++){var sc=identityScore(rows[i],m);if(sc>bestScore){best=rows[i];bestScore=sc}}if(!best||bestScore<c.minIdentityScore)return null;return await doc(best.url,search.url)}
function confirmLinks(page){var out=[],seen={},rows=anchors(page.text,page.url);for(var i=0;i<rows.length;i++){var u=rows[i].url;if(/\/confirm\/\d+\/\d+\/[^?#]+\.xhtml(?:[?#]|$)/i.test(u)&&!seen[u]){seen[u]=1;out.push(u)}}var re=/\]\((\/confirm\/\d+\/\d+\/[^)]+\.xhtml)\)/gi,m;while((m=re.exec(page.text||""))!==null&&out.length<c.maxConfirm){var a=abs(m[1],page.url);if(a&&!seen[a]){seen[a]=1;out.push(a)}}return out.slice(0,c.maxConfirm)}
async function internalFrom(confirm,ref){var p=await doc(confirm,ref);if(!p)return null;var rows=anchors(p.text,p.url);for(var i=0;i<rows.length;i++)if(/\/internal\/\d+\/\d+\/[^?#]+\.xhtml(?:[?#]|$)/i.test(rows[i].url))return await doc(rows[i].url,p.url);var m=(p.text||"").match(/["'](\/internal\/\d+\/\d+\/[^"']+\.xhtml)["']/i);return m?await doc(abs(m[1],p.url),p.url):null}
function unwrap(u){var x=s(u);try{var z=new URL(x),link=z.searchParams.get("link");if(link&&/(?:gamerxyt\.com|360news4u\.net)$/i.test(z.hostname))x=decodeURIComponent(link)}catch(_e){}var p=x.match(/^https?:\/\/(?:www\.)?pixeldrain\.(?:net|dev)\/u\/([A-Za-z0-9_-]+)/i);if(p)x="https://pixeldrain.net/api/file/"+p[1];return x}
function plausible(u){var x=s(u);return /^https?:\/\//i.test(x)&&(/\.(?:m3u8|mpd|mp4|m4v|mkv|webm)(?:[?#]|$)/i.test(x)||/(?:hubcloud|hubdrive|pixeldrain|workers\.dev|r2\.dev|r2\.cloudflarestorage\.com|googleusercontent\.com|sharepoint\.com|drive\.google\.com|gamerxyt\.com\/dl\.php|360news4u\.net\/dl\.php)/i.test(x))}
function candidates(page){var rows=anchors(page.text,page.url),out=[];for(var i=0;i<rows.length;i++){var u=unwrap(rows[i].url);if(plausible(u))out.push(u)}var re=/https?:\/\/[^"'<>\s)]+/gi,m;while((m=re.exec(page.text||""))!==null&&out.length<80){var u2=unwrap(m[0].replace(/&amp;/g,"&"));if(plausible(u2))out.push(u2)}return uniq(out)}
function direct(u){return /\.(?:m3u8|mpd|mp4|m4v|mkv|webm)(?:[?#]|$)/i.test(s(u))||/pixeldrain\.net\/api\/file\//i.test(s(u))||/r2\.cloudflarestorage\.com/i.test(s(u))||/video-downloads\.googleusercontent\.com/i.test(s(u))}
function stream(u,ref){return{name:"MalluMV",title:"MalluMV",url:u,provider:"mallumv",headers:{"Referer":ref||c.base+"/","User-Agent":c.userAgent},isDirect:direct(u)}}
async function resolveCandidate(u,ref){u=unwrap(u);if(direct(u))return[stream(u,ref)];try{if(typeof _crawlDirectMedia==="function"){var got=await _crawlDirectMedia([u],ref||c.base+"/",c.crawlDepth);if(Array.isArray(got)&&got.length){var out=[];for(var i=0;i<got.length;i++){var r=got[i]||{},v=unwrap(r.url);if(!v)continue;var row=Object.assign({},r);row.url=v;row.provider="mallumv";row.name="MalluMV";if(!row.headers)row.headers={"Referer":u,"User-Agent":c.userAgent};out.push(row)}if(out.length)return out}}}catch(_e){}
 var p=await doc(u,ref);if(!p)return[];var nested=candidates(p);for(var j=0;j<nested.length;j++)if(direct(nested[j]))return[stream(nested[j],u)];return[]}
async function resolve(a){var q=req(a);if(!q)return[];var m=await meta(q);if(!m)return[];var page=await detail(m);if(!page)return[];var conf=confirmLinks(page),out=[],seen={};for(var i=0;i<conf.length&&out.length<c.maxStreams;i++){var internal=await internalFrom(conf[i],page.url);if(!internal)continue;var cand=candidates(internal);for(var j=0;j<cand.length&&out.length<c.maxStreams;j++){var rows=await resolveCandidate(cand[j],internal.url);for(var k=0;k<rows.length&&out.length<c.maxStreams;k++){var u=s(rows[k]&&rows[k].url);if(u&&!seen[u]){seen[u]=1;out.push(rows[k])}}}}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioMalluMvRuntimeV1)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioMalluMvRuntimeV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"mallumv",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://mallumv.space",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "minIdentityScore": 55,
        "maxConfirm": 8,
        "maxStreams": 12,
        "crawlDepth": 4,
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: base must be http(s)")
    cfg["minIdentityScore"] = max(40, min(int(cfg.get("minIdentityScore") or 55), 100))
    cfg["maxConfirm"] = max(1, min(int(cfg.get("maxConfirm") or 8), 16))
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 12), 24))
    cfg["crawlDepth"] = max(1, min(int(cfg.get("crawlDepth") or 4), 5))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "mallumv-catalogue-confirm-internal-v1",
            "identity": "tmdb-title-year-bounded",
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
            "terminalResolution": "bounded-internal-link-crawl",
            "semanticLanes": ["movie"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
