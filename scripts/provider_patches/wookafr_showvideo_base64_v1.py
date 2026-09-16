#!/usr/bin/env python3
"""WookaFR provider-local decoder for lecteurvideo showVideo(base64, ...)."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WOOKAFR.SHOWVIDEO.BASE64.V1"
MARKER = "NIAKVIO_WOOKAFR_SHOWVIDEO_BASE64_V1"

WRAPPER = r'''
/* NIAKVIO_WOOKAFR_SHOWVIDEO_BASE64_V1 */
;(function(){
  "use strict";
  try{
    if(typeof _extractUrls!=="function"||_extractUrls.__niakvioWookaShowVideoV1)return;
    var original=_extractUrls;
    function decode64(input){
      var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
      var clean=String(input==null?"":input).replace(/[^A-Za-z0-9+/=]/g,"");
      var out="",i=0;
      while(i<clean.length){
        var e1=chars.indexOf(clean.charAt(i++)),e2=chars.indexOf(clean.charAt(i++));
        var c3=clean.charAt(i++),c4=clean.charAt(i++);
        var e3=c3==="="?64:chars.indexOf(c3),e4=c4==="="?64:chars.indexOf(c4);
        if(e1<0||e2<0)break;
        out+=String.fromCharCode((e1<<2)|(e2>>4));
        if(e3!==64&&e3>=0)out+=String.fromCharCode(((e2&15)<<4)|(e3>>2));
        if(e4!==64&&e4>=0)out+=String.fromCharCode(((e3&3)<<6)|e4);
      }
      try{return decodeURIComponent(out.split("").map(function(ch){return "%"+("0"+ch.charCodeAt(0).toString(16)).slice(-2)}).join(""))}catch(_e){return out}
    }
    var wrapped=function(text,base){
      var out=original(text,base)||[],seen=Object.create(null),result=[];
      function add(u){u=String(u||"").trim();if(!u)return;try{u=_absolute(u,base)}catch(_e){}if(!/^https?:/i.test(u)||seen[u])return;seen[u]=1;result.push(u)}
      for(var i=0;i<out.length;i++)add(out[i]);
      var src=String(text==null?"":text),re=/showVideo\(\s*["']([^"']+)["']\s*,/gi,m,count=0;
      while((m=re.exec(src))&&count++<40){var decoded=decode64(m[1]);if(/^https?:\/\//i.test(decoded))add(decoded)}
      return result;
    };
    wrapped.__niakvioWookaShowVideoV1=true;
    wrapped.__niakvioOriginal=original;
    _extractUrls=wrapped;
  }catch(_e){}
})();
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        WRAPPER,
        data={
            "scope": "provider-local-lecteurvideo-showVideo-base64",
            "providerBaseModified": False,
            "fixtureUrlHardcoded": False,
            "sharedCrawlerPreserved": True,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")