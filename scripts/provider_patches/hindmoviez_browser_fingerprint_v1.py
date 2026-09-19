#!/usr/bin/env python3
"""HindMoviez browser-fingerprint transport Lego.

The live upstream and NiakVIO issue the same WordPress catalogue request, but the
site returns 200 to a normal mobile browser fingerprint and 403 to the generic
NiakVIO ProviderBase fingerprint. This Lego does not own discovery or output: it
runs the existing native provider runtime through the Core dispatch context while
scoping a browser-like request fingerprint to the HindMoviez catalogue host.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.HINDMOVIEZ.BROWSER_FINGERPRINT.V1"
MARKER = "NIAKVIO_HINDMOVIEZ_BROWSER_FINGERPRINT_V1"

WRAPPER = r'''
/* NIAKVIO_HINDMOVIEZ_BROWSER_FINGERPRINT_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
  function host(v){try{return new URL(String(v||"")).hostname.toLowerCase()}catch(_e){return ""}}
  function allowed(h){
    if(!h)return false;
    for(var i=0;i<c.hosts.length;i++){
      var x=String(c.hosts[i]||"").toLowerCase();
      if(h===x||h.slice(-(x.length+1))==="."+x)return true;
    }
    return false;
  }
  async function resolve(args,ctx){
    if(!ctx||typeof ctx.native!=="function"||typeof g.fetch!=="function")return null;
    var nativeFetch=g.fetch;
    g.fetch=async function(url,opt){
      var o=opt&&typeof opt==="object"?Object.assign({},opt):{};
      if(allowed(host(url))){
        var headers=Object.assign({},o.headers||{});
        headers["User-Agent"]=c.ua;
        if(!headers.Accept&&!headers.accept)headers.Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8";
        if(!headers["Accept-Language"]&&!headers["accept-language"])headers["Accept-Language"]="en-US,en;q=0.9";
        o.headers=headers;
        o.redirect=o.redirect||"follow";
      }
      return nativeFetch.call(this,url,o);
    };
    try{return await ctx.native.apply(ctx.receiver,args)}finally{g.fetch=nativeFetch}
  }
  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"hindmoviez",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    hosts=cfg.get("hosts") if isinstance(cfg.get("hosts"),list) else ["hindmovie.icu","hindmovie.fit"]
    payload={
        "hosts":[str(v).strip() for v in hosts if str(v).strip()],
        "ua":str(cfg.get("user_agent") or "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"),
    }
    wrapper=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(
        text,MANAGED_FIX_ID,wrapper,
        data={"transport":"scoped-browser-fingerprint","hosts":payload["hosts"],"nativeRuntimeDelegation":True,"runtimeResolverRegistration":True,"fixtureHardcodes":False},
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
