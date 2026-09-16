#!/usr/bin/env python3
"""Coflix Livavid terminal-context bridge.

The Coflix V1 resolver already discovers the correct Livavid player and HLS.
This provider-owned follow-up preserves the player Referer and adds its Origin
for terminal HLS validation/playback. It does not change catalogue matching,
select another title, or modify shared Core crawling behavior.
"""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.COFLIX.LIVAVID.ORIGIN.V2"
MARKER = "NIAKVIO_COFLIX_LIVAVID_ORIGIN_V2"

WRAPPER = r'''
/* NIAKVIO_COFLIX_LIVAVID_ORIGIN_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g){
  "use strict";
  var prior=null;
  try{prior=g&&g.__niakvioProviderRuntimeResolverV1}catch(_e){}
  if(!prior||prior.provider!=="coflix"||typeof prior.resolve!=="function")return;
  var previous=prior.resolve;
  function s(v){return String(v==null?"":v).trim()}
  function origin(v){try{return new URL(v).origin}catch(_e){return""}}
  async function resolve(args,ctx){
    var rows=await previous(args,ctx);
    if(!Array.isArray(rows))return rows;
    for(var i=0;i<rows.length;i++){
      var row=rows[i];
      if(!row||typeof row!=="object")continue;
      var headers=Object.assign({},row.headers||{});
      var ref=s(headers.Referer||headers.referer||"");
      if(!/https?:\/\/[^/]*livavid\./i.test(ref))continue;
      var o=origin(ref);
      if(!o)continue;
      headers.Referer=ref;
      headers.Origin=o;
      delete headers.referer;
      row.headers=headers;
    }
    return rows;
  }
  try{g.__niakvioProviderRuntimeResolverV1={provider:"coflix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    _ = options
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        WRAPPER,
        data={
            "scope": "coflix-only",
            "catalogueMatchingChanged": False,
            "terminalContext": "preserve Livavid Referer + matching Origin",
            "sharedCoreChanged": False,
            "fixtureHardcodes": False,
            "runtimeResolverRegistration": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
