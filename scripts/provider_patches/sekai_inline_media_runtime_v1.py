#!/usr/bin/env python3
"""NiakVIO-owned Sekai current-site inline media runtime.

Current contract: TMDB/Core metadata -> Sekai catalogue page -> inline video.js
configuration -> decoded mugiwara host + per-episode MP4 template. The runtime
never executes upstream JavaScript; it only parses observable page data and
verifies the selected media URL with a bounded range request before returning it.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.SEKAI.INLINE_MEDIA.RUNTIME.V1"
MARKER = "NIAKVIO_SEKAI_INLINE_MEDIA_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_SEKAI_INLINE_MEDIA_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function uniq(a){return Array.from(new Set((a||[]).filter(Boolean)))}
function q(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||ctx.canonicalMediaType||a[1]||"anime").toLowerCase();if(raw==="tv")raw="anime";if(raw!=="anime")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return null;return{type:"anime",tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:ctx.episode))||1}}
function hdr(ref,extra){var h={"User-Agent":c.ua,"Accept":"text/html,application/xhtml+xml,text/plain,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return Object.assign(h,extra||{})}
async function get(url,ref){try{var r=await g.fetch(url,{headers:hdr(ref),redirect:"follow"});if(!r||!r.ok)return null;return{url:r.url||url,body:await r.text()}}catch(_e){return null}}
async function metadata(x){try{var fn=g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:x.tmdbId,mediaType:"tv",tmdbNamespace:"tv"}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var ctx=g.__nuvioMediaContext||{};return ctx.tmdbMetadata||ctx.fixtureMetadata||null}catch(_e){return null}}
function titles(m){var a=[];if(m){a.push(m.name,m.title,m.original_name,m.original_title);if(Array.isArray(m.aliases))a=a.concat(m.aliases);if(m.alternative_titles&&Array.isArray(m.alternative_titles.results))for(var i=0;i<m.alternative_titles.results.length;i++)a.push(m.alternative_titles.results[i]&&m.alternative_titles.results[i].title)}return uniq(a.map(s)).slice(0,8)}
function text(v){return s(v).replace(/<script\b[\s\S]*?<\/script>/gi," ").replace(/<style\b[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ").replace(/\s+/g," ")}
function scoreTitle(wanted,label,href){var a=norm(wanted),b=norm(label),u=norm(href);if(!a)return 0;var n=0;if(b===a)n=260;else if(b&&(b.indexOf(a)>=0||a.indexOf(b)>=0))n=150;for(var t of a.split(" "))if(t.length>=3&&(b.indexOf(t)>=0||u.indexOf(t)>=0))n+=18;if(u.replace(/ /g,"-").indexOf(a.replace(/ /g,"-"))>=0)n+=100;return n}
function anchors(html,titles){var out=[],re=/<a\b([^>]*?)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))&&out.length<500){var href=s(m[2]);if(!href||href.charAt(0)==="#"||/^javascript:/i.test(href))continue;var label=text(m[4]),best=0;for(var i=0;i<titles.length;i++)best=Math.max(best,scoreTitle(titles[i],label,href));if(best>=60)out.push({href:href,score:best,label:label})}out.sort(function(a,b){return b.score-a.score});return out.slice(0,8)}
function abs(v,base){try{var u=new URL(v,base);if(u.hostname!==new URL(c.base).hostname)return"";return u.toString()}catch(_e){return""}}
function slug(v){return norm(v).replace(/ /g,"-")}
async function pages(tt){var out=[],seen={};var home=await get(c.base+"/",c.base+"/");if(home){var aa=anchors(home.body,tt);for(var i=0;i<aa.length;i++){var u=abs(aa[i].href,home.url);if(u&&!seen[u]){seen[u]=1;out.push(u)}}}for(var j=0;j<Math.min(4,tt.length);j++){var sl=slug(tt[j]);if(sl){var u2=c.base+"/"+sl;if(!seen[u2]){seen[u2]=1;out.push(u2)}}}return out.slice(0,12)}
function b64(v){try{if(typeof atob==="function")return atob(v);if(typeof Buffer!=="undefined")return Buffer.from(v,"base64").toString("utf8")}catch(_e){}return""}
function hosts(html){var map={},re=/(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*atob\(\s*["']([^"']+)["']\s*\)/g,m;while((m=re.exec(html||""))){var u=b64(m[2]);if(/^https?:\/\//i.test(u))map[m[1]]=u}return map}
function mediaFromPage(html,ep){var hm=hosts(html),cands=[],seen={};function add(host,path){host=s(host);path=s(path);if(!host||!path)return;try{var u=new URL(path,host).toString();if(/^https?:\/\//i.test(u)&&!seen[u]){seen[u]=1;cands.push(u)}}catch(_e){}}
var explicit=new RegExp("episode\\s*\\[\\s*"+String(ep)+"\\s*\\]\\s*=\\s*([A-Za-z_$][\\w$]*)\\s*\\+\\s*[\\\"']([^\\\"']+)[\\\"']","gi"),m;while((m=explicit.exec(html||"")))add(hm[m[1]],m[2]);
var dyn=/episode\s*\[\s*([A-Za-z_$][\w$]*)\s*\]\s*=\s*([A-Za-z_$][\w$]*)\s*\+\s*["']([^"']*)["']\s*\+\s*\1\s*\+\s*["']([^"']*)["']/gi;while((m=dyn.exec(html||"")))add(hm[m[2]],m[3]+String(ep)+m[4]);
var direct=/https?:\/\/[^"'<>\s\\]+\.mp4(?:\?[^"'<>\s\\]*)?/gi;while((m=direct.exec(html||""))&&cands.length<20){if(!seen[m[0]]){seen[m[0]]=1;cands.push(m[0])}}
return cands.slice(0,12)}
async function verify(url,ref){var ctrl=null,timer=null;try{if(typeof AbortController!=="undefined"){ctrl=new AbortController();timer=setTimeout(function(){try{ctrl.abort()}catch(_e){}},6500)}var r=await g.fetch(url,{headers:hdr(ref,{Range:"bytes=0-1023",Accept:"video/mp4,video/*;q=0.9,*/*;q=0.2"}),redirect:"follow",signal:ctrl?ctrl.signal:undefined});var ct=s(r&&r.headers&&r.headers.get&&r.headers.get("content-type")).toLowerCase(),st=Number(r&&r.status||0);return !!r&&(st===200||st===206)&&(ct.indexOf("video/")===0||ct.indexOf("octet-stream")>=0)}catch(_e){return false}finally{if(timer)clearTimeout(timer)}}
async function resolve(a,_ctx){var x=q(a);if(!x||x.season!==1)return[];var md=await metadata(x),tt=titles(md);if(!tt.length)return[];var pp=await pages(tt);for(var i=0;i<pp.length;i++){var page=await get(pp[i],c.base+"/");if(!page)continue;var n=0;for(var j=0;j<tt.length;j++)n=Math.max(n,scoreTitle(tt[j],text((/<title[^>]*>([\s\S]*?)<\/title>/i.exec(page.body)||[])[1]||""),page.url));if(n<45)continue;var media=mediaFromPage(page.body,x.episode);for(var k=0;k<media.length;k++){if(!await verify(media[k],page.url))continue;return[{name:"Sekai",title:"Sekai",provider:"sekai",url:media[k],isDirect:true,headers:{Referer:page.url,"User-Agent":c.ua}}]}}return[]}
try{g.__niakvioProviderRuntimeResolverV1={provider:"sekai",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://sekai.one",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "sekai-current-inline-videojs-v1",
            "identity": "core-tmdb-title-to-current-catalogue-page",
            "mediaExtraction": "parse-atob-host-and-episode-mp4-template-no-upstream-js-execution",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["anime"],
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
