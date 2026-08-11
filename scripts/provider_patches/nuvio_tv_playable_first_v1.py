"""Nuvio TV-only direct-link health ordering wrapper.

For providers returning several direct media candidates, a stale first link can
make TV users hit a 403/5xx even though a later candidate is valid.  The wrapper
probes a small bounded prefix only under the Android-TV/NuvioTV runtime,
removes conclusively dead direct-media rows and moves verified media ahead of
unverified rows.  Other platforms are untouched.
"""
from __future__ import annotations

import json

MARKER = "NUVIO_TV_PLAYABLE_FIRST_V1"


def apply(source: str, options: dict | None = None, **_kwargs) -> str:
    if MARKER in source:
        return source
    cfg = dict(options or {})
    max_probes = max(1, min(int(cfg.get("max_probes", 6)), 8))
    timeout_ms = max(1500, min(int(cfg.get("timeout_ms", 6500)), 12000))
    shim = r'''
/* NUVIO_TV_PLAYABLE_FIRST_V1 */
;(function(g){
 const MAX=__MAX__, TIMEOUT=__TIMEOUT__;
 function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");return /NuvioTV|Android TV/i.test(ua);}catch(_e){return false}}
 function rows(v){if(Array.isArray(v))return v;if(v&&typeof v==="object"){for(const k of ["streams","results","data"]){if(Array.isArray(v[k]))return v[k]}}return null}
 function direct(u){return /^https?:\/\//i.test(u)&&!/\.(?:html?|php)(?:[?#]|$)/i.test(u)}
 function sig(b){if(!b||b.length<4)return false;if(b.length>=12&&String.fromCharCode(...b.slice(4,8))==="ftyp")return true;if(b[0]===0x1a&&b[1]===0x45&&b[2]===0xdf&&b[3]===0xa3)return true;if(b.length>=188&&b[0]===0x47)return true;return false}
 async function probe(row){
   const u=String(row&&row.url||"").trim();
   if(!direct(u))return {rank:1,dead:false};
   const h=Object.assign({},row.headers||{});if(!h.Accept)h.Accept="*/*";if(!/\.m3u8(?:[?#]|$)/i.test(u)&&!h.Range)h.Range="bytes=0-32767";
   let timer;try{
     const c=new AbortController();timer=setTimeout(()=>c.abort(),TIMEOUT);
     const r=await fetch(u,{headers:h,redirect:"follow",signal:c.signal});
     const st=Number(r.status||0),ct=String(r.headers&&r.headers.get?r.headers.get("content-type")||"":"").toLowerCase();
     if([401,403,404,410].includes(st)||st>=500)return {rank:3,dead:true,status:st};
     const ab=await r.arrayBuffer(),b=new Uint8Array(ab.slice(0,65536));
     let txt="";try{txt=new TextDecoder().decode(b).replace(/^\uFEFF/,"").trimStart()}catch(_e){}
     if(txt.startsWith("#EXTM3U"))return {rank:0,dead:false,status:st};
     if(sig(b)||(/^video\//.test(ct)&&(st===200||st===206)))return {rank:0,dead:false,status:st};
     if(/text\/html|application\/xhtml/.test(ct)||/^<!doctype html|^<html/i.test(txt))return {rank:3,dead:true,status:st};
     return {rank:1,dead:false,status:st};
   }catch(_e){return {rank:2,dead:false};}finally{if(timer)clearTimeout(timer)}
 }
 function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioTvPlayableFirstV1)return;const native=t.getStreams;
   const wrapped=async function(){const v=await native.apply(t,arguments);if(!isTv())return v;const a=rows(v);if(!a||a.length<1)return v;
     const head=a.slice(0,MAX),tail=a.slice(MAX),checks=await Promise.all(head.map(probe));
     const kept=head.map((row,i)=>({row,i,c:checks[i]})).filter(x=>!x.c.dead).sort((a,b)=>(a.c.rank-b.c.rank)||(a.i-b.i)).map(x=>x.row);
     const out=kept.concat(tail);
     if(Array.isArray(v))return out;
     for(const k of ["streams","results","data"]){if(Array.isArray(v[k]))return Object.assign({},v,{[k]:out})}
     return v;
   };wrapped.__nuvioTvPlayableFirstV1=true;wrapped.__nuvioTvPlayableFirstOriginal=native;t.getStreams=wrapped;
 }
 try{if(typeof module!=="undefined"&&module.exports)install(module.exports)}catch(_e){}
 try{if(g&&typeof g.getStreams==="function"){const o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''.replace("__MAX__", str(max_probes)).replace("__TIMEOUT__", str(timeout_ms))
    return source.rstrip() + "\n" + shim + "\n"
