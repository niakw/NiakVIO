#!/usr/bin/env python3
"""VidLove provider-local source selector for the current api.vidlove.cc contract."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDLOVE.CURRENT.API.V1"
MARKER = "NIAKVIO_VIDLOVE_CURRENT_API_V1"

WRAPPER = r'''
/* NIAKVIO_VIDLOVE_CURRENT_API_V1 */
;(function(){
  "use strict";
  try{
    if(typeof _sourceUrls!=="function"||_sourceUrls.__niakvioVidLoveCurrentApiV1)return;
    var original=_sourceUrls;
    var wrapped=function(value,base,out){
      try{
        if(value&&typeof value==="object"&&!Array.isArray(value)&&value.source&&typeof value.source==="object"&&typeof value.source.url==="string"){
          out=out||[];
          var absolute=_absolute(value.source.url,base);
          if(absolute&&/^https?:/i.test(absolute))out.push(absolute);
          return out;
        }
      }catch(_e){}
      return original(value,base,out);
    };
    wrapped.__niakvioVidLoveCurrentApiV1=true;
    wrapped.__niakvioOriginal=original;
    _sourceUrls=wrapped;
  }catch(_e){}
})();
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        WRAPPER,
        data={
            "scope": "provider-local-current-api-source-url",
            "providerBaseModified": False,
            "fixtureUrlHardcoded": False,
            "subtitleUrlsExcluded": True,
            "sharedStreamGuardsPreserved": True,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")