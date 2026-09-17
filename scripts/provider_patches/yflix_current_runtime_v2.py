#!/usr/bin/env python3
"""NiakVIO-owned current YFlix/1Movies resolver.

The public metadata DB is authoritative for TMDB identity and media namespace.
For TV requests this runtime always queries ``type=tv``; it never reuses the
movie route, which could resolve the same numeric TMDB id to an unrelated film.
When a current frontend is reachable, the documented encrypted AJAX link chain
is followed. Otherwise the provider fails closed instead of returning wrong
content.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.YFLIX.CURRENT.RUNTIME.V2"
MARKER = "NIAKVIO_YFLIX_CURRENT_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_YFLIX_CURRENT_RUNTIME_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function q(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||ctx.canonicalMediaType||a[1]||"").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return null;return{type:raw,tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:ctx.episode))||1}}
function hdr(ref,accept){var h={"User-Agent":c.ua,"Accept":accept||"application/json,text/html,text/plain,*/*","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function res(url,opt){try{var o=Object.assign({redirect:"follow"},opt||{});o.headers=Object.assign(hdr(o.referer||""),o.headers||{});delete o.referer;var r=await g.fetch(url,o);return r||null}catch(_e){return null}}
async function jsonGet(url,ref){var r=await res(url,{referer:ref,headers:{Accept:"application/json,*/*"}});if(!r||!r.ok)return null;try{return await r.json()}catch(_e){try{return JSON.parse(await r.text())}catch(_x){return null}}}
async function jsonPost(url,obj,ref){var r=await res(url,{method:"POST",referer:ref,headers:{"Content-Type":"application/json","Accept":"application/json,*/*"},body:JSON.stringify(obj)});if(!r||!r.ok)return null;try{return await r.json()}catch(_e){try{return JSON.parse(await r.text())}catch(_x){return null}}}
function urls(v,out,depth){out=out||[];depth=depth||0;if(depth>5||v==null)return out;if(typeof v==="string"){var m=v.match(/https?:\/\/[^"'<>\s\\]+/g)||[];for(var i=0;i<m.length;i++)if(!out.includes(m[i]))out.push(m[i]);return out}if(Array.isArray(v)){for(var j=0;j<v.length;j++)urls(v[j],out,depth+1);return out}if(typeof v==="object"){for(var k of Object.keys(v))urls(v[k],out,depth+1)}return out}
function terminal(u){return /\.(?:m3u8|mp4|mkv|webm)(?:[?#]|$)/i.test(s(u))}
function playerish(u){try{var x=new URL(u),p=x.pathname.toLowerCase();return /(?:embed|watch|player|stream|video)/.test(p)||/(?:megaup|rapidshare|vid|stream|player)/.test(x.hostname.toLowerCase())}catch(_e){return false}}
async function verifyEmbed(u,ref){try{var r=await res(u,{referer:ref,headers:{Accept:"text/html,application/xhtml+xml,*/*;q=0.8"}});if(!r||!r.ok)return false;var ct=s(r.headers&&r.headers.get&&r.headers.get("content-type")).toLowerCase();return ct.indexOf("text/html")>=0||ct.indexOf("application/xhtml")>=0}catch(_e){return false}}
function row(u,ref,direct){var x={name:"YFlix",title:"YFlix",provider:"yflix",url:u,isDirect:!!direct,headers:{Referer:ref||c.dbBase+"/","User-Agent":c.ua}};if(!direct)x.__nuvioCorrelatedPlayerFallbackV1={url:u};return x}
function pickServer(v){if(!v||typeof v!=="object")return null;if(v.lid)return v;if(Array.isArray(v)){for(var i=0;i<v.length;i++){var r=pickServer(v[i]);if(r)return r}return null}for(var k of Object.keys(v)){var r2=pickServer(v[k]);if(r2)return r2}return null}
async function enc(text){var j=await jsonGet(c.api+"/enc-movies-flix?text="+encodeURIComponent(text),c.dbBase+"/");return s(j&&j.result)}
async function db(x){var u=c.dbBase+"/db/flix/find?tmdb_id="+encodeURIComponent(x.tmdbId)+"&type="+encodeURIComponent(x.type),j=await jsonGet(u,c.dbBase+"/");var r=Array.isArray(j)?j[0]:j,info=r&&r.info;if(!r||!info)return null;if(s(info.tmdb_id)!==x.tmdbId)return null;if(s(info.type).toLowerCase()!==x.type)return null;return r}
function episode(r,x){var eps=r&&r.episodes;if(!eps||typeof eps!=="object")return null;var season=eps[String(x.season)];if(!season||typeof season!=="object")return null;return season[String(x.episode)]||null}
async function fromKnownSources(ep,ref){var uu=urls(ep&&ep.sources||{});for(var i=0;i<uu.length;i++){if(terminal(uu[i]))return[row(uu[i],ref,true)];if(playerish(uu[i])&&await verifyEmbed(uu[i],ref))return[row(uu[i],ref,false)]}return[]}
async function frontend(base,eid){var token=await enc(eid);if(!token)return[];var list=await jsonGet(base+"/ajax/links/list?eid="+encodeURIComponent(eid)+"&_="+encodeURIComponent(token),base+"/");if(!list||!list.result)return[];var parsed=await jsonPost(c.api+"/parse-html",{text:list.result},base+"/"),srv=pickServer(parsed&&parsed.result);if(!srv||!srv.lid)return[];var lid=s(srv.lid),tok2=await enc(lid);if(!tok2)return[];var view=await jsonGet(base+"/ajax/links/view?id="+encodeURIComponent(lid)+"&_="+encodeURIComponent(tok2),base+"/");if(!view||!view.result)return[];var dec=await jsonPost(c.api+"/dec-movies-flix",{text:view.result},base+"/"),uu=urls(dec&&dec.result!=null?dec.result:dec);for(var i=0;i<uu.length;i++){if(terminal(uu[i]))return[row(uu[i],base+"/",true)];if(playerish(uu[i])&&await verifyEmbed(uu[i],base+"/"))return[row(uu[i],base+"/",false)]}return[]}
async function resolve(a,_ctx){var x=q(a);if(!x)return[];var r=await db(x);if(!r)return[];var ep=episode(r,x);if(!ep&&x.type==="movie")ep=episode(r,{season:1,episode:1});if(!ep)return[];var known=await fromKnownSources(ep,c.dbBase+"/");if(known.length)return known;var eid=s(ep.eid);if(!eid)return[];for(var i=0;i<c.frontends.length;i++){var out=await frontend(c.frontends[i],eid);if(out.length)return out}return[]}
try{g.__niakvioProviderRuntimeResolverV1={provider:"yflix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "dbBase": "https://enc-dec.app",
        "api": "https://enc-dec.app/api",
        "frontends": ["https://yflix.to", "https://1movies.bz", "https://solarmovie.fi"],
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "yflix-current-namespace-aware-v2",
            "identityAuthority": "enc-dec-db-flix-tmdb-id-plus-type",
            "movieRoute": "/db/flix/find?tmdb_id={tmdbId}&type=movie",
            "tvRoute": "/db/flix/find?tmdb_id={tmdbId}&type=tv",
            "frontendChain": "enc-eid-links-list-parse-html-enc-lid-links-view-decrypt",
            "failClosedOnFrontendUnavailable": True,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "tv"],
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
