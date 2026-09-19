#!/usr/bin/env python3
"""WookaFR provider-local player-seed prioritization.

The clean ProviderBase keeps a small bounded crawl budget. Live evidence on
2026-09-12 proved that Wooka's lecteurvideo.com embed structurally exposes a
valid direct movie URL through the existing shared extractor/crawler, but the
real detail page can expose enough other player-like URLs that lecteurvideo is
truncated before the crawl starts. This Lego only reorders Wooka seeds before
that existing bounded crawler; it does not change ProviderBase v3, hardcode a
fixture player id, or bypass shared stream/identity guards.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WOOKAFR.LECTEURVIDEO.PRIORITY.V1"
MARKER = "NIAKVIO_WOOKAFR_LECTEURVIDEO_PRIORITY_V1"

WRAPPER = r'''
/* NIAKVIO_WOOKAFR_LECTEURVIDEO_PRIORITY_V1 */
;(function(g,c){
  "use strict";
  try{
    if(typeof _crawlDirectMedia!=="function"||_crawlDirectMedia.__niakvioWookaPriorityV1)return;
    var original=_crawlDirectMedia;
    function text(v){return String(v==null?"":v)}
    function score(url){
      try{
        var p=new URL(text(url)),h=p.hostname.toLowerCase();
        if(h==="lecteurvideo.com"||/\.lecteurvideo\.com$/.test(h))return 1000;
        if(h==="lulustream.com"||/\.lulustream\.com$/.test(h))return 300;
        if(/(?:vidmoly|uqload|waaw|veev|xtremestream|emmmmbed)/i.test(h))return 200;
        return 0;
      }catch(_e){return -1}
    }
    var wrapped=async function(seedUrls,referer,maxDepth){
      var rows=[],seen=Object.create(null),src=Array.isArray(seedUrls)?seedUrls:[];
      for(var i=0;i<src.length;i++){
        var u=text(src[i]);if(!u||seen[u])continue;seen[u]=1;rows.push({url:u,index:i,score:score(u)});
      }
      rows.sort(function(a,b){return b.score-a.score||a.index-b.index});
      var ordered=rows.map(function(r){return r.url});
      return await original(ordered,referer,maxDepth);
    };
    wrapped.__niakvioWookaPriorityV1=true;
    wrapped.__niakvioOriginal=original;
    _crawlDirectMedia=wrapped;
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "priorityHost": str(cfg.get("priority_host") or "lecteurvideo.com"),
        "reason": "proven-direct-media-before-bounded-seed-truncation",
    }
    wrapper = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "scope": "provider-local-seed-order-only",
            "providerBaseModified": False,
            "fixtureUrlHardcoded": False,
            "sharedGuardsPreserved": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
