#!/usr/bin/env python3
"""Append one Core-wide JS runtime portability bootstrap to every provider bundle.

The bootstrap only fills semantic gaps observed between official Nuvio runtimes.
It does not resolve provider domains, alter stream rows, or invent provider data.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_GLOBAL_RUNTIME_COMPAT_V1"
RESERVED_KEY = "__nuvioGlobalRuntimeCompatV1"
REVISION = 1


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    if MARKER in text or RESERVED_KEY in text:
        return text

    wrapper = r'''
/* NUVIO_GLOBAL_RUNTIME_COMPAT_V1 */
;(function(g){
  "use strict";
  if(!g||g.__nuvioGlobalRuntimeCompatV1)return;
  g.__nuvioGlobalRuntimeCompatV1={revision:1};

  // NuvioDesktop's current URL polyfill stores href independently from hostname,
  // host, pathname, search and hash. Replacing hostname therefore leaves
  // URL#toString() stale. Keep the official parser, but return instances whose
  // string form is reconstructed from their current public URL fields.
  var NativeURL=g.URL;
  if(typeof NativeURL==="function"){
    function renderUrl(u){
      try{
        var protocol=String(u.protocol||"");
        var host=String(u.host||"");
        if(!host){
          host=String(u.hostname||"");
          var port=String(u.port||"");
          if(port&&host.indexOf(":")<0)host+=":"+port;
        }else if(u.hostname&&String(u.hostname)!==host.split(":")[0]){
          host=String(u.hostname||"")+(u.port?":"+String(u.port):"");
        }
        var hierarchical=protocol&&host?protocol+"//"+host:"";
        return hierarchical+String(u.pathname||"")+String(u.search||"")+String(u.hash||"");
      }catch(_error){
        try{return String(u.href||"");}catch(_ignored){return "";}
      }
    }
    var staleMutableUrl=false;
    try{
      var probe=new NativeURL("https://old.invalid/a?b=1#c");
      probe.hostname="new.invalid";
      staleMutableUrl=String(probe).indexOf("new.invalid")<0;
    }catch(_error){}
    if(staleMutableUrl){
      var CompatURL=function(input,base){
        var u=arguments.length>1?new NativeURL(input,base):new NativeURL(input);
        try{
          u.toString=function(){return renderUrl(u);};
          u.toJSON=function(){return renderUrl(u);};
        }catch(_error){}
        return u;
      };
      try{CompatURL.prototype=NativeURL.prototype;}catch(_error){}
      try{
        Object.getOwnPropertyNames(NativeURL).forEach(function(name){
          if(name==="length"||name==="name"||name==="prototype")return;
          try{CompatURL[name]=NativeURL[name];}catch(_ignored){}
        });
      }catch(_error){}
      g.URL=CompatURL;
    }
  }

  // Normalize URL/Request-like inputs before the official Desktop fetch bridge.
  // QuickJS host bindings stringify arbitrary objects differently across clients;
  // the network bridge itself expects one concrete URL string.
  if(typeof g.fetch==="function"&&!g.fetch.__nuvioGlobalRuntimeCompatV1){
    var nativeFetch=g.fetch.bind(g);
    var compatFetch=function(input,init){
      var next=input;
      try{
        if(input&&typeof input==="object"){
          if(typeof input.url==="string")next=input.url;
          else if(typeof input.href==="string"||typeof input.toString==="function")next=String(input);
        }
      }catch(_error){next=input;}
      return nativeFetch(next,init);
    };
    compatFetch.__nuvioGlobalRuntimeCompatV1=true;
    compatFetch.__nuvioOriginal=nativeFetch;
    g.fetch=compatFetch;
  }

  // Some provider helpers install abort timeouts even though NuvioDesktop QuickJS
  // currently exposes no timer API. A positive delay is intentionally a no-op:
  // firing an abort immediately is worse than allowing the native request budget
  // to govern the request. Zero-delay callbacks keep microtask semantics.
  if(typeof g.setTimeout!=="function"){
    g.setTimeout=function(callback,delay){
      if((Number(delay)||0)<=0&&typeof callback==="function"&&typeof Promise!=="undefined"){
        Promise.resolve().then(callback).catch(function(){});
      }
      return 0;
    };
  }
  if(typeof g.clearTimeout!=="function")g.clearTimeout=function(){};
  if(typeof g.setInterval!=="function")g.setInterval=function(){return 0;};
  if(typeof g.clearInterval!=="function")g.clearInterval=function(){};
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return text.rstrip() + "\n" + wrapper.lstrip()
