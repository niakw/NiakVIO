#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix
import dle_anime_runtime_v1 as common

MANAGED_FIX_ID = "PROVIDER.VOIRANIME-HOMES.DLE.RUNTIME.V1"
SEARCH_ITEM_MARKER = "NIAKVIO_VOIRANIME_HOMES_SEARCH_ITEM_V2"


def _voiranime_homes_wrapper() -> str:
    """Extend the shared DLE parser with VoirAnime-Homes' live AJAX card shape."""
    needle = "    return out\n  }\n  function bestCandidate"
    replacement = r'''    /* NIAKVIO_VOIRANIME_HOMES_SEARCH_ITEM_V2 */
    var itemRe=/onclick=(["'])[^"']*location\.href\s*=\s*['"]([^'"]+)['"][^"']*\1/gi,im;
    while((im=itemRe.exec(html||""))!==null&&out.length<100){
      var href=absolute(im[2],c.base),from=Math.max(0,im.index-700),to=Math.min((html||"").length,itemRe.lastIndex+1200),chunk=(html||"").slice(from,to);
      var idm=href.match(/\/(\d+)-/)||href.match(/[?&](?:newsid|id)=(\d{1,12})/i)||chunk.match(/(?:newsid|data-news-id|data-id)["'=:\s]+(\d{1,12})/i);
      var titlem=chunk.match(/class=["'][^"']*(?:search-title|search-item-title)[^"']*["'][^>]*>([\s\S]{0,500}?)<\//i),title=titlem?stripTags(titlem[1]):"";
      var key=(idm?idm[1]:"")+"|"+href;if(href&&!seen[key]){seen[key]=1;out.push({id:idm?idm[1]:"",url:href,title:title})}
    }
    return out
  }
  function bestCandidate'''
    if needle not in common.WRAPPER:
        raise ValueError("shared DLE candidate parser anchor missing")
    return common.WRAPPER.replace(needle, replacement, 1)


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://voiranime.homes").rstrip("/"),
        "provider": "voiranime-homes",
        "name": str(cfg.get("name") or "VoirAnime Homes"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 6), 12)),
    }
    wrapper = _voiranime_homes_wrapper().replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "sharedEngine": "dle_anime_runtime_v1",
            "runtimeResolverRegistration": True,
            "fallbackOnly": True,
            "searchResultShape": "div.search-item onclick=location.href + .search-title + numeric URL news id",
            "searchItemRevision": SEARCH_ITEM_MARKER,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
