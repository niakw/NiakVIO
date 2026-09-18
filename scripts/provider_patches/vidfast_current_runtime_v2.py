#!/usr/bin/env python3
"""VidFast current direct resolver v2 using its live enc-dec contract."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix, strip_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDFAST.CURRENT.RUNTIME.V2"
MARKER = "NIAKVIO_VIDFAST_CURRENT_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_VIDFAST_CURRENT_RUNTIME_V2 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function lane(v){v=s(v).toLowerCase();if(v==="series"||v==="anime")v="tv";return v==="movie"?"movie":v==="tv"?"tv":""}
function reqHeaders(token){var h={"User-Agent":c.ua,"Referer":c.base+"/","Origin":c.base,"X-Requested-With":"XMLHttpRequest"};if(token)h["X-CSRF-Token"]=token;return h}
async function json(url,opt){try{var r=await g.fetch(url,opt||{});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function text(url,opt){try{var r=await g.fetch(url,opt||{});if(!r||!r.ok)return null;return await r.text()}catch(_e){return null}}
function pageToken(html){html=String(html||"");var m=/\\["'](?:en|token)\\["']\s*:\s*\\["'](.*?)\\["']/i.exec(html)||/["'](?:en|token)["']\s*:\s*["']([^"']+)["']/i.exec(html);return s(m&&m[1])}
function decoded(value){if(typeof value==="string"){try{var x=JSON.parse(value);if(x&&typeof x==="object")return x}catch(_e){}return value}return value}
function direct(v){return /^https?:\/\//i.test(s(v))}
function streamObject(v){v=decoded(v);if(!v||typeof v!=="object")return null;if(direct(v.url||v.file||v.src))return v;if(v.result&&typeof v.result==="object"&&direct(v.result.url||v.result.file||v.result.src))return v.result;return null}
function subs(v){var rows=Array.isArray(v&&v.captions)?v.captions:Array.isArray(v&&v.subtitles)?v.subtitles:[],out=[];for(var i=0;i<rows.length;i++){var r=rows[i]||{},u=s(r.file||r.url);if(direct(u))out.push({url:u,language:s(r.label||r.lang||""),name:s(r.label||r.lang||"")})}return out}
async function dec(payload){var r=await json(c.api+"/dec-vidfast",{method:"POST",headers:{"Content-Type":"application/json","Accept":"application/json,*/*"},body:JSON.stringify({text:String(payload==null?"":payload)})});return r&&Number(r.status)===200?r.result:null}
async function current(id,mediaType,season,episode){id=s(id);var type=lane(mediaType);if(!id||!type)return[];season=Math.floor(Number(season)||0);episode=Math.floor(Number(episode)||0);if(type==="tv"&&(season<=0||episode<=0))return[];var embed=type==="movie"?c.base+"/movie/"+encodeURIComponent(id)+"/":c.base+"/tv/"+encodeURIComponent(id)+"/"+season+"/"+episode+"/",html=await text(embed,{headers:{"User-Agent":c.ua,"Referer":c.base+"/"},redirect:"follow"});if(!html)return[];var tokenText=pageToken(html);if(!tokenText)return[];var enc=await json(c.api+"/enc-vidfast?text="+encodeURIComponent(tokenText)+"&version=1",{headers:{"Accept":"application/json,*/*","User-Agent":c.ua,"Referer":c.base+"/"}});if(!enc||Number(enc.status)!==200||!enc.result)return[];var meta=enc.result,serversUrl=s(meta.servers),streamBase=s(meta.stream),csrf=s(meta.token);if(!direct(serversUrl)||!direct(streamBase))return[];var encryptedServers=await text(serversUrl,{method:"POST",headers:reqHeaders(csrf)});if(!encryptedServers)return[];var servers=decoded(await dec(encryptedServers));if(!Array.isArray(servers))return[];var out=[],seen={};for(var i=0;i<servers.length&&i<c.maxServers&&out.length<c.maxRows;i++){var srv=servers[i]||{},key=s(srv.data);if(!key)continue;var encrypted=await text(streamBase.replace(/\/$/,"")+"/"+encodeURIComponent(key),{method:"POST",headers:reqHeaders(csrf)});if(!encrypted)continue;var obj=streamObject(await dec(encrypted));if(!obj)continue;var u=s(obj.url||obj.file||obj.src);if(!direct(u)||seen[u])continue;seen[u]=1;out.push({name:"VidFast"+(srv.name?" - "+s(srv.name):""),title:"VidFast",url:u,provider:"vidfast",isDirect:true,type:/\.m3u8(?:[?#]|$)/i.test(u)?"hls":/\.mpd(?:[?#]|$)/i.test(u)?"dash":"direct",headers:reqHeaders(csrf),subtitles:subs(obj)})}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioVidFastCurrentRuntimeV2)return false;var original=o[k],wrapped=async function(tmdbId,mediaType,season,episode){try{var out=await current(tmdbId,mediaType,season,episode);if(out.length)return out}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return[]}};wrapped.__niakvioVidFastCurrentRuntimeV2=true;wrapped.__niakvioOriginal=original;o[k]=wrapped;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(typeof _spv4GetStreams==="function"&&!_spv4GetStreams.__niakvioVidFastCurrentRuntimeV2){var orig=_spv4GetStreams;_spv4GetStreams=async function(tmdbId,mediaType,season,episode){try{var out=await current(tmdbId,mediaType,season,episode);if(out.length)return out}catch(_e){}try{return await orig(tmdbId,mediaType,season,episode)}catch(_e){return[]}};_spv4GetStreams.__niakvioVidFastCurrentRuntimeV2=true}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    text = strip_managed_fix(text, "PROVIDER.VIDFAST.CURRENT.EMBED.V1")
    cfg = {
        "base": "https://vidfast.vc",
        "api": "https://enc-dec.app/api",
        "maxServers": 8,
        "maxRows": 8,
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(text, MANAGED_FIX_ID, js.lstrip(), data={
        "scope": "provider-local-current-enc-dec-direct-runtime-v2",
        "providerBaseModified": False,
        "fixtureIdsHardcoded": False,
        "embedRoute": "vidfast.vc/{movie|tv}/{tmdbId}",
        "decryptApi": cfg["api"],
        "terminalMediaReturned": True,
    })


if __name__ == "__main__":
    raise SystemExit("patch module only")
