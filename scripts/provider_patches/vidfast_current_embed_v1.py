#!/usr/bin/env python3
"""VidFast provider-local fallback for the current documented TMDB embed routes."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDFAST.CURRENT.EMBED.V1"
MARKER = "NIAKVIO_VIDFAST_CURRENT_EMBED_V1"

WRAPPER = r'''
/* NIAKVIO_VIDFAST_CURRENT_EMBED_V1 */
;(function(){
  "use strict";
  try{
    var exported=(typeof module!=="undefined"&&module&&module.exports&&typeof module.exports.getStreams==="function")?module.exports.getStreams:null;
    var internal=typeof _spv4GetStreams==="function"?_spv4GetStreams:null;
    var original=exported||internal;
    if(!original||original.__niakvioVidFastCurrentEmbedV1)return;
    var wrapped=async function(tmdbId,mediaType,season,episode){
      var rows=[];
      try{rows=await original(tmdbId,mediaType,season,episode)}catch(_e){}
      if(Array.isArray(rows)&&rows.length)return rows;
      var id=String(tmdbId==null?"":tmdbId).trim();if(!id)return [];
      var lane=typeof _mediaNamespace==="function"?_mediaNamespace(mediaType):(mediaType==="movie"?"movie":"tv"),url="";
      if(lane==="movie")url="https://vidfast.vc/movie/"+encodeURIComponent(id);
      else{
        var s=Math.floor(Number(season)||0),e=Math.floor(Number(episode)||0);
        if(s<=0||e<=0)return [];
        url="https://vidfast.vc/tv/"+encodeURIComponent(id)+"/"+s+"/"+e;
      }
      try{
        var response=await _fetch(url,{headers:{Referer:"https://vidfast.vc/"}});
        if(!response||response.ok===false)return [];
        var type=String(response&&response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
        if(type&&type.indexOf("text/html")<0)return [];
      }catch(_e){return []}
      return [{name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName,url:url,headers:{Referer:"https://vidfast.vc/"}}];
    };
    wrapped.__niakvioVidFastCurrentEmbedV1=true;
    wrapped.__niakvioOriginal=original;
    try{_spv4GetStreams=wrapped}catch(_e){}
    if(typeof module!=="undefined"&&module&&module.exports)module.exports.getStreams=wrapped;
  }catch(_e){}
})();
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        WRAPPER,
        data={
            "scope": "provider-local-exported-current-documented-embed-route",
            "providerBaseModified": False,
            "fixtureUrlHardcoded": False,
            "movieRoute": "/movie/{tmdbId}",
            "tvRoute": "/tv/{tmdbId}/{season}/{episode}",
            "wrapsExportedGetStreams": True,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")