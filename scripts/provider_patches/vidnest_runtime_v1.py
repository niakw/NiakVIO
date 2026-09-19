#!/usr/bin/env python3
"""Vidnest clean-v3 direct API runtime adapter."""
from __future__ import annotations
import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDNEST.RUNTIME.V1"
MARKER = "NIAKVIO_VIDNEST_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VIDNEST_RUNTIME_V1 */
;(function(g,c){
"use strict";
function s(v){return String(v==null?"":v).trim()}
function args(a){
 var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
 var md=(o&&(o.tmdbMetadata||o.metadata))||ctx.tmdbMetadata||null;if(md&&md.state==="ok"&&md.metadata)md=md.metadata;md=md&&typeof md==="object"?md:{};
 var t=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||ctx.canonicalMediaType||a[1]||"movie").toLowerCase(),date=s(md.release_date||md.first_air_date||md.year);
 return {id:s((o&&(o.tmdbId||o.tmdb_id||o.id))||ctx.tmdbId||f).replace(/^tmdb:/i,"").split(":")[0],type:t==="movie"?"movie":"tv",season:Number((o&&o.season)!=null?o.season:a[2])||0,episode:Number((o&&o.episode)!=null?o.episode:a[3])||0,title:s(md.title||md.name||md.original_title||md.original_name||"Vidnest"),year:date.slice(0,4)};
}
function apiHeaders(){return {"Accept":"application/json,text/plain,*/*","Origin":"https://vidnest.fun","Referer":"https://vidnest.fun/","User-Agent":c.userAgent}}
async function decrypt(payload){
 try{var r=await g.fetch(c.decryptUrl,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({encryptedData:payload,passphrase:c.passphrase})});if(!r||!r.ok)return null;var j=await r.json();return j&&!j.error&&j.decrypted?s(j.decrypted):null}catch(_e){return null}
}
function proxy(url){
 var u=s(url);if(!u)return "";
 if(/flashstream\.cc|streamsvr\/|\/pl\/|rogflix|lethe399key\.com.*\/stream2\//i.test(u)){
   var origin=/lethe399key\.com/i.test(u)?"https://lethe399key.com":"https://flashstream.cc";
   var h={"user-agent":c.playbackUserAgent,"accept":"*/*","origin":origin,"referer":origin+"/"};
   return c.proxyUrl+"?url="+encodeURIComponent(u)+"&headers="+encodeURIComponent(JSON.stringify(h));
 }
 return u;
}
function sources(data){
 if(!data||typeof data!=="object")return [];
 if(Array.isArray(data.sources))return data.sources;
 if(Array.isArray(data.streams))return data.streams;
 if(typeof data.url==="string")return [{url:data.url,headers:data.headers}];
 if(typeof data.data==="string")return [{url:data.data,headers:data.headers}];
 return [];
}
function rows(data,server,q){
 var out=[],seen=Object.create(null),ss=sources(data);
 for(var i=0;i<ss.length;i++){var row=ss[i]||{},url=proxy(row.file||row.url||row.src||row.link);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;
   out.push({name:"Vidnest "+server,title:q.title+(q.type==="tv"?" S"+q.season+"E"+q.episode:(q.year?" ("+q.year+")":"")),url:url,quality:s(row.quality||row.label||"auto"),language:s(row.language||""),headers:row.headers&&typeof row.headers==="object"?row.headers:undefined,provider:"vidnest"});
 }
 return out;
}
async function one(server,q){
 var url=c.apiBase+"/"+server+"/"+q.type+"/"+encodeURIComponent(q.id);if(q.type==="tv")url+="/"+q.season+"/"+q.episode;if(server==="flixhq")url+="?server=upcloud";
 try{var r=await g.fetch(url,{headers:apiHeaders(),redirect:"follow"});if(!r||!r.ok)return [];var txt=await r.text(),data;try{data=JSON.parse(txt)}catch(_e){return []}
   if(data&&data.encrypted&&data.data){var clear=await decrypt(data.data);if(!clear)return [];try{data=JSON.parse(clear)}catch(_e){return []}}
   return rows(data,server,q);
 }catch(_e){return []}
}
async function resolve(a){var q=args(a);if(!/^\d+$/.test(q.id))return [];if(q.type==="tv"&&(!q.season||!q.episode))return [];
 var all=await Promise.all(c.servers.map(function(x){return one(x,q)})),out=[],seen=Object.create(null);for(var i=0;i<all.length;i++)for(var j=0;j<all[i].length;j++){var r=all[i][j];if(!seen[r.url]){seen[r.url]=1;out.push(r)}}return out.slice(0,40);
}
function install(x,k){if(!x||typeof x[k]!=="function"||x[k].__niakvioVidnestRuntimeV1)return false;var w=async function(){return await resolve(arguments)};w.__niakvioVidnestRuntimeV1=true;x[k]=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")||ok}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''
def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    payload={
      "apiBase":str(cfg.get("api_base") or "https://first.vidnest.fun").rstrip("/"),
      "proxyUrl":str(cfg.get("proxy_url") or "https://vidnest.animanga.fun/proxy"),
      "decryptUrl":str(cfg.get("decrypt_url") or "https://aesdec.nuvioapp.space/decrypt"),
      "passphrase":str(cfg.get("passphrase") or "A7kP9mQeXU2BWcD4fRZV+Sg8yN0/M5tLbC1HJQwYe6o="),
      "servers":list(cfg.get("servers") or ["hollymoviehd","primesrc","ophim","flixhq","vidlink","rogflix"]),
      "userAgent":str(cfg.get("user_agent") or "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/137 Mobile Safari/537.36"),
      "playbackUserAgent":str(cfg.get("playback_user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137 Safari/537.36")
    }
    return replace_managed_fix(text,MANAGED_FIX_ID,WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":"))),data={"runtime":payload,"identity":"tmdb-direct","legacyExecutableSeed":False})
if __name__ == "__main__": raise SystemExit("patch module only")
