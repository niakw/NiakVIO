#!/usr/bin/env python3
"""HindMoviez exact WordPress -> MVLink -> HindShare -> HCloud runtime.

The provider is accessed with the currently proven mobile-browser fingerprint.
Identity is IMDb-based. Movie rows expose direct MVLink pages; TV rows expose
/web/ pages whose filenames carry exact SxxEyy identity. Download signatures are
requested from MVLink's hindshare_sign endpoint, then HShare/HCloud pages are
followed structurally. Site JavaScript is never evaluated and fixture-specific
IDs are never embedded.
"""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.HINDMOVIEZ.RUNTIME.V1"
MARKER = "NIAKVIO_HINDMOVIEZ_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_HINDMOVIEZ_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function S(v){return String(v==null?"":v).trim()}
function A(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g.__nuvioMediaContext||{}}catch(_e){}var t=S((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.mediaType||"").toLowerCase();if(t==="series")t="tv";if(t!=="movie"&&t!=="tv")return null;var imdb=S((o&&(o.imdbId||o.imdb_id||o.imdb))||x.imdbId||x.imdb_id||x.imdb||"");return{type:t,imdbId:imdb,season:Number((o&&o.season)||a[2]||x.season)||1,episode:Number((o&&o.episode)||a[3]||x.episode)||1}}
function H(ref,accept){var h={"User-Agent":c.ua,"Accept":accept||"text/html,application/xhtml+xml,application/json,*/*","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function G(url,ref){try{var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:H(ref)});if(!r||!r.ok)return null;return{text:await r.text(),url:r.url||url,status:r.status}}catch(_e){return null}}
async function POST(url,body,ref){try{var h=H(ref,"application/json,text/plain,*/*");h["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8";h["X-Requested-With"]="XMLHttpRequest";var r=await g.fetch(url,{method:"POST",redirect:"follow",headers:h,body:body});if(!r||!r.ok)return null;return{text:await r.text(),url:r.url||url,status:r.status}}catch(_e){return null}}
function B64(s){var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",out="",i=0;for(;i<s.length;i+=3){var a=s.charCodeAt(i)&255,b=i+1<s.length?s.charCodeAt(i+1)&255:NaN,d=i+2<s.length?s.charCodeAt(i+2)&255:NaN;out+=chars.charAt(a>>2);out+=chars.charAt(((a&3)<<4)|((b||0)>>4));out+=isNaN(b)?"=":chars.charAt(((b&15)<<2)|((d||0)>>6));out+=isNaN(d)?"=":chars.charAt(d&63)}return out.replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"")}
function URLs(src,re){var out=[],seen={},m;re.lastIndex=0;while((m=re.exec(S(src).replace(/\\\//g,"/").replace(/&amp;/g,"&")))!==null){var u=S(m[0]).replace(/["'<>),;]+$/g,"");if(u&&!seen[u]){seen[u]=1;out.push(u)}}return out}
function mvlinks(row,type){var src="";try{src=JSON.stringify(row||{})}catch(_e){src=S(row)}var all=URLs(src,/https?:\/\/mvlink\.blog\/(?:web\/)?\d+/gi),out=[];for(var i=0;i<all.length;i++){var web=/\/web\//i.test(all[i]);if((type==="tv"&&web)||(type==="movie"&&!web))out.push(all[i])}return out.slice(0,8)}
function files(src,type,season,episode){var out=[],seen={},re=/[A-Za-z0-9._+()\[\] -]{12,260}\.(?:mkv|mp4|avi)/gi,m,tag=new RegExp("S0*"+season+"E0*"+episode+"(?:[^0-9]|$)","i");while((m=re.exec(S(src)))!==null){var f=S(m[0]).replace(/\s+/g," ");if(type==="tv"&&!tag.test(f))continue;if(!seen[f]){seen[f]=1;out.push(f)}}return out.slice(0,3)}
function quality(f){var m=/(2160|1080|720|480|360)p/i.exec(f);return m?m[1]+"p":"HD"}
function hshareUrl(src){try{var d=JSON.parse(src);var u=S(d&&d.data&&d.data.url);if(/^https?:\/\/hshare\.ink\//i.test(u))return u}catch(_e){}var xs=URLs(src,/https?:\/\/hshare\.ink\/[^\s"'<>\\]+/gi);return xs[0]||""}
function hcloudUrl(src){var xs=URLs(src,/https?:\/\/hcloud\.ink\/[^\s"'<>\\]+/gi);return xs[0]||""}
function finals(src){var xs=URLs(src,/https?:\/\/[A-Za-z0-9.-]+\.workers\.dev\/[^\s"'<>\\]+/gi),out=[];for(var i=0;i<xs.length;i++){if(/[?&]file=/i.test(xs[i]))out.push(xs[i])}return out.slice(0,4)}
async function chain(mv,type,season,episode){var page=await G(mv,c.siteRef);if(!page)return[];var names=files(page.text,type,season,episode),out=[];for(var i=0;i<names.length;i++){var f=names[i],body="action=hindshare_sign&d="+encodeURIComponent(B64(f)),sig=await POST(c.mvAjax,body,page.url);if(!sig)continue;var hs=hshareUrl(sig.text);if(!hs)continue;var hp=await G(hs,page.url);if(!hp)continue;var hc=hcloudUrl(hp.text);if(!hc)continue;var cp=await G(hc,hp.url);if(!cp)continue;var us=finals(cp.text);for(var j=0;j<us.length;j++)out.push({name:"HindMoviez | "+quality(f),title:"HindMoviez | "+quality(f),url:us[j],quality:quality(f),language:"Hindi/English",headers:H(cp.url,"*/*"),provider:"hindmoviez",isDirect:true});if(out.length>=4)break}return out}
async function resolve(a){var q=A(a);if(!q||!q.imdbId)return q===null?null:[];var api=c.api+"?search="+encodeURIComponent(q.imdbId)+"&per_page=100",r=await G(api,c.siteRef);if(!r)return[];var rows=[];try{rows=JSON.parse(r.text)}catch(_e){}if(!Array.isArray(rows))return[];var links=[],seen={};for(var i=0;i<rows.length;i++){var m=mvlinks(rows[i],q.type);for(var j=0;j<m.length;j++)if(!seen[m[j]]){seen[m[j]]=1;links.push(m[j])}}var out=[],urlSeen={};for(var k=0;k<links.length&&k<8;k++){var z=await chain(links[k],q.type,q.season,q.episode);for(var n=0;n<z.length;n++)if(!urlSeen[z[n].url]){urlSeen[z[n].url]=1;out.push(z[n])}if(out.length>=4)break}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"hindmoviez",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    payload={
        "api":str(cfg.get("api") or "https://hindmovie.icu/wp-json/wp/v2/posts"),
        "siteRef":str(cfg.get("site_ref") or "https://hindmovie.fit/"),
        "mvAjax":str(cfg.get("mv_ajax") or "https://mvlink.blog/wp-admin/admin-ajax.php"),
        "ua":str(cfg.get("user_agent") or "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"),
    }
    return replace_managed_fix(text,MANAGED_FIX_ID,WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":"))),data={"semanticLanes":["movie","tv"],"identity":"IMDb","catalog":"WordPress REST search","chain":["mvlink","hindshare_sign","hshare","hcloud","workers"],"tvIdentity":"filename SxxEyy","siteJavascriptExecuted":False,"fixtureHardcodes":False,"runtimeResolverRegistration":True})


if __name__ == "__main__":
    raise SystemExit("patch module only")
