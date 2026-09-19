#!/usr/bin/env python3
"""NiakVIO-owned UHDMovies movie runtime.

Observed provider-local chain:
site search -> movie post -> release gateway -> two landing forms -> ?go token
-> DriveSeed/download page -> direct media URL.

Domain authority is read from NIAKVIO_PROVIDER_MODEL. No upstream JavaScript is
embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.UHDMOVIES.RUNTIME.V1"
MARKER = "NIAKVIO_UHDMOVIES_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_UHDMOVIES_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return""}}
function origin(v){try{return new URL(v).origin}catch(_e){return""}}
function visible(v){return s(v).replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ").replace(/&amp;/gi,"&").replace(/&quot;/gi,'"').replace(/&#0*39;|&apos;/gi,"'").replace(/\s+/g," ").trim()}
function attr(tag,key){var m=String(tag||"").match(new RegExp("\\b"+key+"\\s*=\\s*([\"'])([\\s\\S]*?)\\1","i"));return m?m[2].replace(/&amp;/gi,"&"):""}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.mediaType||"movie").toLowerCase();if(raw!=="movie")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{tmdbId:id,type:"movie"}}
function headers(ref){var h={"User-Agent":c.ua,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function request(url,opt){try{var o=Object.assign({redirect:"follow"},opt||{});o.headers=Object.assign(headers(o.referer||""),o.headers||{});delete o.referer;var r=typeof _fetch==="function"?await _fetch(url,o):await g.fetch(url,o);if(!r||r.ok===false)return null;return{url:r.url||url,text:await r.text(),status:r.status,headers:r.headers}}catch(_e){return null}}
async function meta(q){try{var fn=g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"movie",tmdbNamespace:"movie"}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var x=g.__nuvioMediaContext||{};return x.tmdbMetadata||x.fixtureMetadata||null}catch(_e){return null}}
function titleMeta(m,q){var title=s(m&&(m.title||m.name||m.original_title||m.original_name)),year=s(m&&(m.release_date||m.year)).slice(0,4);return{title:title,year:year,tmdbId:q.tmdbId}}
function base(){try{var m=typeof NIAKVIO_PROVIDER_MODEL!=="undefined"&&NIAKVIO_PROVIDER_MODEL;return s(m&&(m.officialSite||m.knownSite)||c.base).replace(/\/$/,"")}catch(_e){return s(c.base).replace(/\/$/,"")}}
function articleRows(html){var blocks=String(html||"").match(/<article\b[^>]*>[\s\S]*?<\/article>/gi)||[],out=[];for(var i=0;i<blocks.length;i++){var a=(blocks[i].match(/<a\b[^>]+href=["'][^"']+["'][^>]*>[\s\S]*?<\/a>/i)||[])[0]||"",u=attr(a,"href"),label=attr(a,"title")||visible(a)||visible(blocks[i]);if(u)out.push({url:u,label:label})}return out}
function score(row,m){var label=norm(row.label),want=norm(m.title),sc=0;if(want&&label.indexOf(want)>=0)sc+=100;var y=(row.label||"").match(/\b(19|20)\d{2}\b/);if(m.year&&y){if(y[0]===m.year)sc+=30;else if(Math.abs(Number(y[0])-Number(m.year))>1)sc-=80}if(/\bseason\b|\bs\d{1,2}\b/i.test(row.label))sc-=100;return sc}
async function findPosts(m){var b=base();if(!b||!m.title)return[];var q=await request(b+"/?s="+encodeURIComponent(m.title),{referer:b+"/"});if(!q)return[];var rows=articleRows(q.text).map(function(r){return{url:abs(r.url,b),label:r.label,score:score(r,m)}}).filter(function(r){return r.url&&r.score>=70});rows.sort(function(a,b){return b.score-a.score});return rows.slice(0,3)}
function anchors(html,b){var out=[],re=/<a\b[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<300){var u=abs(m[1],b);if(u)out.push({url:u,text:visible(m[2])})}return out}
function quality(v){var x=s(v).toLowerCase();if(/2160p|\b4k\b|\buhd\b/.test(x))return"2160p";var m=x.match(/\b(1080|720|480)p\b/);return m?m[1]+"p":""}
function size(v){var m=s(v).match(/\[\s*(\d+(?:\.\d+)?\s*(?:GB|MB))\s*\]/i);return m?m[1].replace(/\s+/g," "):""}
function releases(html,b){var ps=String(html||"").match(/<p\b[^>]*>[\s\S]*?<\/p>/gi)||[],out=[],seen={};for(var i=0;i<ps.length;i++){var label=visible(ps[i]);if(!/\[\s*(?:\d+(?:\.\d+)?\s*)?(?:GB|MB)\s*\]/i.test(label))continue;var joined=ps.slice(i,i+3).join(""),aa=anchors(joined,b),hit=null;for(var j=0;j<aa.length;j++)if(/unblockedgames/i.test(aa[j].url)){hit=aa[j];break}if(!hit||seen[hit.url])continue;seen[hit.url]=1;out.push({url:hit.url,label:label,quality:quality(label),size:size(label),language:/english audio/i.test(label)&&!/dual[ -]?audio/i.test(label)?"en":"multi"})}return out.slice(0,c.maxReleases)}
function parseForm(html,b){var forms=String(html||"").match(/<form\b[^>]*>[\s\S]*?<\/form>/gi)||[],chosen="";for(var i=0;i<forms.length;i++){if(/\bid\s*=\s*["']landing["']/i.test(forms[i])){chosen=forms[i];break}}if(!chosen)chosen=forms[0]||"";if(!chosen)return null;var open=(chosen.match(/<form\b[^>]*>/i)||[])[0]||"",action=abs(attr(open,"action")||b,b),fields={},inputs=chosen.match(/<input\b[^>]*>/gi)||[];for(var j=0;j<inputs.length;j++){var name=attr(inputs[j],"name");if(name)fields[name]=attr(inputs[j],"value")}return action?{action:action,fields:fields}:null}
function formBody(fields){return Object.keys(fields||{}).map(function(k){return encodeURIComponent(k)+"="+encodeURIComponent(fields[k]||"")}).join("&")}
function redirectTarget(html,b){var m=String(html||"").match(/http-equiv=["']refresh["'][^>]+content=["'][^"']*url\s*=\s*([^"']+)/i);if(m)return abs(m[1],b);m=String(html||"").match(/(?:window\.)?location(?:\.href|\.replace)?\s*(?:=|\()\s*["']([^"']+)/i);return m?abs(m[1],b):""}
async function gateway(url){var first=await request(url,{referer:base()+"/"});if(!first)return"";var f1=parseForm(first.text,first.url);if(!f1)return"";var r1=await request(f1.action,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:formBody(f1.fields),referer:first.url});if(!r1)return"";var f2=parseForm(r1.text,r1.url);if(!f2)return"";var r2=await request(f2.action,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:formBody(f2.fields),referer:r1.url});if(!r2)return"";var gm=String(r2.text||"").match(/\?go=([^"'&<\s]+)/i);if(!gm)return redirectTarget(r2.text,r2.url);var token=gm[1],o=origin(url),values=Object.values(f2.fields||{}).map(s).filter(Boolean).slice(0,c.maxGatewayValues);if(!values.length)values=[""];for(var i=0;i<values.length;i++){var h=headers(r2.url);h.Cookie=token+"="+values[i];var z=await request(o+"/?go="+encodeURIComponent(token),{headers:h,referer:r2.url});if(!z)continue;var target=redirectTarget(z.text,z.url);if(target)return target}return""}
function directCandidate(v){var u=s(v);if(!/^https?:\/\//i.test(u))return false;try{var p=new URL(u),h=p.hostname.toLowerCase(),path=p.pathname.toLowerCase();return /\.(?:mkv|mp4|m3u8)(?:$|[?#])/i.test(u)||h.endsWith(".workers.dev")||h.endsWith(".r2.dev")||h.endsWith(".r2.cloudflarestorage.com")||h==="video-downloads.googleusercontent.com"||h.endsWith(".googlevideo.com")||h==="cdn.video-gen.xyz"||path.indexOf("download")>=0}catch(_e){return false}}
function directLinks(html,b){var out=[],seen={},aa=anchors(html,b);for(var i=0;i<aa.length;i++){if(directCandidate(aa[i].url)&&!seen[aa[i].url]){seen[aa[i].url]=1;out.push(aa[i].url)}}var re=/https?:\\?\/\\?\/[^\s"'<>\\]+/gi,m;while((m=re.exec(String(html||"")))!==null&&out.length<50){var u=m[0].replace(/\\\//g,"/");if(directCandidate(u)&&!seen[u]){seen[u]=1;out.push(u)}}return out}
function downloadButtons(html,b){return anchors(html,b).filter(function(a){return /resume cloud|cloud download|instant download|direct download|download now/i.test(a.text)})}
function redirectedDirect(v){var u=s(v),q="";try{q=new URL(u).searchParams.get("url")||""}catch(_e){}if(q){try{q=decodeURIComponent(q)}catch(_e2){}if(directCandidate(q))return q}return directCandidate(u)?u:""}
async function followDownload(url,referer){try{var o={headers:headers(referer),redirect:"follow"},r=typeof _fetch==="function"?await _fetch(url,o):await g.fetch(url,o);if(!r)return null;var final=r.url||url,direct=redirectedDirect(final);if(direct)return{url:final,direct:direct,text:""};var text="";try{text=await r.text()}catch(_bodyError){}return{url:final,direct:"",text:text}}catch(_e){return null}}
async function driveSeed(url){var cur=url;if(/\/r\?key=/i.test(cur)){var rr=await request(cur,{referer:base()+"/"});if(!rr)return[];var t=redirectTarget(rr.text,rr.url);if(t)cur=t}var page=await request(cur,{referer:base()+"/"});if(!page)return[];var direct=directLinks(page.text,page.url);if(direct.length)return direct.slice(0,4);var buttons=downloadButtons(page.text,page.url);for(var i=0;i<buttons.length&&i<5;i++){var u=buttons[i].url;if(directCandidate(u))return[u];var rr=await followDownload(u,page.url);if(!rr)continue;if(rr.direct)return[rr.direct];var more=directLinks(rr.text,rr.url);if(more.length)return more.slice(0,4)}try{if(typeof _crawlDirectMedia==="function"){var crawled=await _crawlDirectMedia([cur],cur,2);if(Array.isArray(crawled)&&crawled.length)return crawled.map(function(x){var u=x&&x.url;return redirectedDirect(u)||u}).filter(Boolean).slice(0,4)}}catch(_e){}return[]}
async function resolveRelease(rel,meta){var ds=await gateway(rel.url);if(!ds)return[];var urls=await driveSeed(ds),out=[];for(var i=0;i<urls.length;i++){if(!urls[i])continue;out.push({name:"UHDMovies"+(rel.quality?" | "+rel.quality:""),title:(meta.title||"UHDMovies")+(meta.year?" ("+meta.year+")":"")+(rel.size?" | "+rel.size:""),url:urls[i],quality:rel.quality||"",language:rel.language||"multi",provider:"uhdmovies",headers:{"Referer":ds}})}return out}
async function resolve(a,_ctx){var q=req(a);if(!q)return[];var m=titleMeta(await meta(q),q);if(!m.title)return[];var posts=await findPosts(m),out=[],seen={};for(var p=0;p<posts.length&&out.length<8;p++){var page=await request(posts[p].url,{referer:base()+"/"});if(!page)continue;var rels=releases(page.text,page.url);for(var r=0;r<rels.length&&out.length<8;r++){var rows=await resolveRelease(rels[r],m);for(var j=0;j<rows.length&&out.length<8;j++){var st=rows[j];if(st.url&&!seen[st.url]){seen[st.url]=1;out.push(st)}}}}return out}
try{g.__niakvioProviderRuntimeResolverV1={provider:"uhdmovies",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "",
        "maxReleases": 4,
        "maxGatewayValues": 8,
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["maxReleases"] = max(1, min(int(cfg.get("maxReleases") or 4), 8))
    cfg["maxGatewayValues"] = max(1, min(int(cfg.get("maxGatewayValues") or 8), 16))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "uhdmovies-search-gateway-driveseed-v2-final-url-first",
            "identity": "core-tmdb-movie-title-year",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie"],
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
