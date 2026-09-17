#!/usr/bin/env python3
"""MovieBox current embed resolver using vidsrcme's live vs_src contract."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIEBOX.CURRENT.EMBED.V2"
MARKER = "NIAKVIO_MOVIEBOX_CURRENT_EMBED_V2"

WRAPPER = r'''
/* NIAKVIO_MOVIEBOX_CURRENT_EMBED_V2 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioMovieBoxCurrentEmbedV2)return;
    var original=_spv4GetStreams,API="https://vidsrcme.ru/vs_src.php",REFERER="https://vidsrcme.ru/";
    async function current(tmdbId,mediaType,season,episode){
      var id=String(tmdbId==null?"":tmdbId).trim();if(!id)return [];
      var lane=_mediaNamespace(mediaType),query="type="+(lane==="movie"?"movie":"tv")+"&id="+encodeURIComponent(id);
      if(lane!=="movie"){
        var s=Math.floor(Number(season)||0),e=Math.floor(Number(episode)||0);if(s<=0||e<=0)return [];
        query+="&season="+s+"&episode="+e;
      }
      try{
        var r=await _fetch(API+"?"+query,{headers:{Accept:"application/json,text/plain,*/*",Referer:REFERER}}),value=await r.json();
        var src=value&&typeof value.src==="string"?value.src:"";if(!/^https?:\/\//i.test(src))return [];
        var check=await _fetch(src,{headers:{Referer:REFERER}}),ct=String(check.headers&&check.headers.get?check.headers.get("content-type")||"":"").toLowerCase();
        if(ct&&ct.indexOf("text/html")<0)return [];
        return [{name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName,url:src,headers:{Referer:REFERER},__nuvioCorrelatedPlayerFallbackV1:{url:src}}];
      }catch(_e){return []}
    }
    var wrapped=async function(tmdbId,mediaType,season,episode){try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return []}};
    wrapped.__niakvioMovieBoxCurrentEmbedV2=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;
    try{if(typeof module!=="undefined"&&module.exports&&typeof module.exports==="object")module.exports.getStreams=wrapped}catch(_e){}
  }catch(_e){}
})();
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(text, MANAGED_FIX_ID, WRAPPER, data={
        "scope": "provider-local-current-vs-src-embed",
        "providerBaseModified": False,
        "fixtureIdsHardcoded": False,
        "directStreamDecryptionImplemented": False,
        "encryptedStreamUrlsIgnored": True,
        "preserveEmbed": True,
    })


if __name__ == "__main__":
    raise SystemExit("patch module only")