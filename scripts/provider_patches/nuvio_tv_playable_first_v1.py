"""Nuvio TV-only direct-link health ordering wrapper.

For providers returning several direct media candidates, a stale first link can
make TV users hit a 403/5xx even though a later candidate is valid. The wrapper
probes a small bounded prefix only under the real NuvioTV QuickJS bridge (or an
explicit TV regression harness), removes conclusively dead rows and moves proven
HLS or video responses ahead of unverified rows. Other platforms are untouched.

Nuvio Desktop and Nuvio Mobile also expose ``__native_fetch``. Therefore its
mere presence is not a TV signal. At the pinned official client revisions their
fetch polyfill forwards a fifth ``followRedirects`` argument; NuvioTV uses a
four-argument native call and handles ``options.signal`` around it. The runtime
fingerprint below deliberately distinguishes those contracts.
"""
from __future__ import annotations

MARKER = "NUVIO_TV_PLAYABLE_FIRST_V1"

LEGACY_TV_PREDICATE = r'''function isTv(){try{if(typeof g.__native_fetch==="function")return true;var ua=String((g.navigator&&g.navigator.userAgent)||"");return /NuvioTV|Android TV/i.test(ua);}catch(_e){return false}}'''

TV_PREDICATE = r'''function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative;}catch(_e){return false}}'''


def apply(source: str, options: dict | None = None, **_kwargs) -> str:
    # Existing published providers may already contain the original V1 wrapper.
    # Upgrade its predicate in place instead of appending a second wrapper; this
    # keeps generation idempotent and removes the cross-platform probing bug from
    # content-addressed bundles on the next durable reapply.
    if MARKER in source:
        if LEGACY_TV_PREDICATE in source:
            return source.replace(LEGACY_TV_PREDICATE, TV_PREDICATE, 1)
        return source

    cfg = dict(options or {})
    max_probes = max(1, min(int(cfg.get("max_probes", 6)), 8))
    timeout_ms = max(1500, min(int(cfg.get("timeout_ms", 6500)), 12000))
    shim = r'''
/* NUVIO_TV_PLAYABLE_FIRST_V1 */
;(function(g){
 const MAX=__MAX__, TIMEOUT=__TIMEOUT__;
 __TV_PREDICATE__
 function slot(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(const k of ["streams","results","data"]){if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
 function rebuild(v,s,list){if(s.key===null)return list;return Object.assign({},v,{[s.key]:list})}
 function direct(u){return /^https?:\/\//i.test(u)&&!/\.(?:html?|php)(?:[?#]|$)/i.test(u)}
 function mergedHeaders(row){var h={};try{Object.assign(h,row&&row.headers||{},row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request||{})}catch(_e){}if(!h.Accept)h.Accept="*/*";if(!/\.m3u8(?:[?#]|$)/i.test(String(row&&row.url||""))&&!h.Range)h.Range="bytes=0-32767";return h}
 async function probe(row){
   const u=String(row&&row.url||"").trim();
   if(!direct(u))return {rank:1,dead:false};
   let timer;try{
     const c=typeof AbortController!=="undefined"?new AbortController():null;if(c)timer=setTimeout(()=>c.abort(),TIMEOUT);
     const r=await g.fetch(u,{headers:mergedHeaders(row),redirect:"follow",signal:c?c.signal:void 0});
     const st=Number(r&&r.status||0),ct=String(r&&r.headers&&r.headers.get?r.headers.get("content-type")||"":"").toLowerCase();
     if([401,403,404,410].includes(st)||st>=500)return {rank:3,dead:true,status:st};
     if(/^video\//.test(ct)&&(st===200||st===206))return {rank:0,dead:false,status:st};
     let text="";try{if(r&&typeof r.text==="function")text=String(await r.text()).replace(/^\uFEFF/,"").trimStart()}catch(_e){}
     if(text.startsWith("#EXTM3U"))return {rank:0,dead:false,status:st};
     if(/text\/html|application\/xhtml/.test(ct)||/^<!doctype html|^<html/i.test(text))return {rank:3,dead:true,status:st};
     return {rank:1,dead:false,status:st};
   }catch(_e){return {rank:2,dead:false};}finally{if(timer)clearTimeout(timer)}
 }
 function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioTvPlayableFirstV1)return;const native=t.getStreams;
   const wrapped=async function(){const v=await native.apply(t,arguments);if(!isTv())return v;const s=slot(v);if(!s||s.list.length<1)return v;
     const head=s.list.slice(0,MAX),tail=s.list.slice(MAX),checks=await Promise.all(head.map(probe));
     const kept=head.map((row,i)=>({row,i,c:checks[i]})).filter(x=>!x.c.dead).sort((a,b)=>(a.c.rank-b.c.rank)||(a.i-b.i)).map(x=>x.row);
     return rebuild(v,s,kept.concat(tail));
   };wrapped.__nuvioTvPlayableFirstV1=true;wrapped.__nuvioTvPlayableFirstOriginal=native;t.getStreams=wrapped;
 }
 try{if(typeof module!=="undefined"&&module.exports)install(module.exports)}catch(_e){}
 try{if(g&&typeof g.getStreams==="function"){const o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''.replace("__MAX__", str(max_probes)).replace("__TIMEOUT__", str(timeout_ms)).replace("__TV_PREDICATE__", TV_PREDICATE)
    return source.rstrip() + "\n" + shim + "\n"
