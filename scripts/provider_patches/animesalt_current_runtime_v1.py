#!/usr/bin/env python3
"""AnimeSalt current-site resolver (series page -> exact episode -> correlated player)."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMESALT.CURRENT.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMESALT_CURRENT_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMESALT_CURRENT_RUNTIME_V1 */
/* NIAKVIO_ANIMESALT_REFERER_ONLY_PLAYER_V72 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioAnimeSaltCurrentV1)return;
    var original=_spv4GetStreams;
    var UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36";
    function base(){
      try{
        var m=(typeof NIAKVIO_PROVIDER_MODEL==="object"&&NIAKVIO_PROVIDER_MODEL)||{};
        var v=String(m.officialSite||m.knownSite||"").replace(/\/+$/g,"");
        return /^https?:\/\//i.test(v)?v:"";
      }catch(_e){return "";}
    }
    function h(ref){
      var x={"User-Agent":UA,"Accept-Language":"en-US,en;q=0.9","Accept":"text/html,application/xhtml+xml,*/*;q=0.8"};
      if(ref)x.Referer=ref;
      return x;
    }
    function cleanText(v){return _slug(String(v||"").replace(/<[^>]+>/g," "));}
    function titleOk(html,expected){
      var text=cleanText(String(html||"").replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," "));
      for(var i=0;i<expected.length;i++)if(expected[i]&&text.indexOf(expected[i])>=0)return true;
      return false;
    }
    async function current(tmdbId,mediaType,season,episode){
      if(_mediaNamespace(mediaType)==="movie")return [];
      var s=Math.floor(Number(season)||0),e=Math.floor(Number(episode)||0);if(s<=0||e<=0)return [];
      var B=base();if(!B)return [];
      var meta=await _tmdb(tmdbId,mediaType);if(!meta||!meta.title)return [];
      var expected=_uniq([meta.title].concat(Array.isArray(meta.aliases)?meta.aliases:[])).map(_slug).filter(Boolean);
      var seriesUrl="",seriesHtml="";
      for(var i=0;i<expected.length&&i<6;i++){
        var slug=expected[i];if(!slug)continue;
        var u=B+"/series/"+slug+"/",r,txt="";
        try{r=await _fetch(u,{headers:h(B+"/")});if(!r||Number(r.status||0)>=400)continue;txt=await r.text()}catch(_e){continue}
        if(!titleOk(txt,expected))continue;
        seriesUrl=u;seriesHtml=txt;break;
      }
      if(!seriesUrl||!seriesHtml)return [];
      var target=String(s)+"x"+String(e),re=/<a\b[^>]*href=["']([^"']*\/episode\/[^"']+)["'][^>]*>/gi,m,episodeUrl="";
      while((m=re.exec(seriesHtml))){
        var u2=_absolute(m[1],B);if(!u2)continue;
        var path="";try{path=new URL(u2).pathname.toLowerCase()}catch(_e){}
        if(new RegExp("-"+target.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"/?$").test(path)){episodeUrl=u2;break;}
      }
      if(!episodeUrl)return [];
      var er,episodeHtml="";
      try{er=await _fetch(episodeUrl,{headers:h(seriesUrl)});if(!er||Number(er.status||0)>=400)return [];episodeHtml=await er.text()}catch(_e){return []}
      var im=/<iframe\b[^>]*src=["']([^"']+)["']/i.exec(episodeHtml);if(!im)return [];
      var player=_absolute(im[1],episodeUrl);if(!/^https?:\/\//i.test(player))return [];
      return [{
        name:NIAKVIO_PROVIDER_MODEL.displayName,
        title:NIAKVIO_PROVIDER_MODEL.displayName,
        url:player,
        headers:{Referer:episodeUrl},
        __nuvioCorrelatedPlayerFallbackV1:{url:player}
      }];
    }
    var wrapped=async function(tmdbId,mediaType,season,episode){
      try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}
      try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return []}
    };
    wrapped.__niakvioAnimeSaltCurrentV1=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;
    try{if(typeof module!=="undefined"&&module.exports&&typeof module.exports==="object")module.exports.getStreams=wrapped}catch(_e){}
  }catch(_e){}
})();
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        WRAPPER,
        data={
            "scope": "provider-local-current-series-episode-player",
            "providerBaseModified": False,
            "fixtureIdsHardcoded": False,
            "identityRequired": True,
            "playerHeaders": "referer-only-no-origin",
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")