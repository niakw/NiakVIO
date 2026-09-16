#!/usr/bin/env python3
"""AllAnime current WordPress runtime: search -> anime detail -> exact episode -> embeds."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLANIME.CURRENT.RUNTIME.V1"
MARKER = "NIAKVIO_ALLANIME_CURRENT_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ALLANIME_CURRENT_RUNTIME_V1 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioAllAnimeCurrentV1)return;
    var original=_spv4GetStreams,BASE="https://ww2.aniwatch.fit",UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36";
    function headers(ref){return {"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,text/plain,*/*","Accept-Language":"en-US,en;q=0.9","Referer":ref||BASE+"/"};}
    function clean(v){return String(v==null?"":v).replace(/<[^>]+>/g," ").replace(/&amp;/gi,"&").replace(/&quot;/gi,'"').replace(/&#39;/gi,"'").replace(/\s+/g," ").trim();}
    function expected(meta){return _uniq([meta&&meta.title].concat(meta&&Array.isArray(meta.aliases)?meta.aliases:[])).map(_slug).filter(Boolean);}
    function detailCandidates(html,meta){
      var exp=expected(meta),out=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;
      while((m=re.exec(String(html||"")))&&out.length<120){
        var u=_absolute(m[1],BASE+"/"),label=clean(m[2]);if(!u||seen[u])continue;
        var path="";try{path=new URL(u).pathname}catch(_e){}
        if(!/^\/[a-z0-9][^?#]*\/$/i.test(path)||/episode-/i.test(path))continue;
        var hay=_slug(label+" "+path),score=0;
        for(var i=0;i<exp.length;i++){var e=exp[i];if(!e)continue;if(hay===e||path.toLowerCase()==="/"+e+"/")score=Math.max(score,120);else if(e.length>=5&&hay.indexOf(e)>=0)score=Math.max(score,80);}
        if(score>0){seen[u]=1;out.push({url:u,score:score});}
      }
      out.sort(function(a,b){return b.score-a.score});return out;
    }
    function episodeUrl(html,base,episode){
      var wanted=Math.floor(Number(episode)||0);if(wanted<=0)return "";
      var re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;
      while((m=re.exec(String(html||"")))){
        var body=String(m[2]||""),num=body.match(/class=["'][^"']*epl-num[^"']*["'][^>]*>\s*(\d+)\s*</i);
        if(num&&Number(num[1])===wanted)return _absolute(m[1],base);
        var u=_absolute(m[1],base);if(u&&new RegExp("(?:^|[-_/])episode[-_]?0*"+wanted+"(?:$|[/?#-])","i").test(u))return u;
      }
      return "";
    }
    function embeds(html,base){
      var out=[],seen=Object.create(null),re=/<iframe[^>]+src=["']([^"']+)["']/gi,m;
      while((m=re.exec(String(html||"")))&&out.length<10){
        var u=_absolute(m[1],base);if(!/^https?:/i.test(u)||seen[u])continue;
        var host="";try{host=new URL(u).hostname.toLowerCase()}catch(_e){}
        if(/(?:megaplay\.buzz|vidmoly\.|vidmoly\.to|vidmoly\.net|streamwish|filemoon|voe\.)/i.test(host)){seen[u]=1;out.push(u);}
      }
      return out;
    }
    async function current(tmdbId,mediaType,season,episode){
      var lane=String(mediaType||"").toLowerCase();if(lane!=="anime"&&lane!=="tv")return [];
      var ep=Math.floor(Number(episode)||0);if(ep<=0)return [];
      var meta=await _tmdb(tmdbId,mediaType);if(!meta||!meta.title)return [];
      var search=BASE+"/?s="+encodeURIComponent(meta.title),sr,sh;
      try{sr=await _fetch(search,{headers:headers(BASE+"/")});sh=await sr.text()}catch(_e){return []}
      var candidates=detailCandidates(sh,meta);if(!candidates.length)return [];
      for(var i=0;i<Math.min(candidates.length,3);i++){
        try{
          var dr=await _fetch(candidates[i].url,{headers:headers(search)}),detailUrl=dr.url||candidates[i].url,dh=await dr.text();
          var epUrl=episodeUrl(dh,detailUrl,ep);if(!epUrl)continue;
          var er=await _fetch(epUrl,{headers:headers(detailUrl)}),finalEp=er.url||epUrl,eh=await er.text(),rows=embeds(eh,finalEp);
          if(rows.length){var name=NIAKVIO_PROVIDER_MODEL.displayName;return rows.slice(0,8).map(function(u,index){return {name:name,title:name+(index?" #"+(index+1):""),url:u,headers:{Referer:finalEp}}});}
        }catch(_e){}
      }
      return [];
    }
    var wrapped=async function(tmdbId,mediaType,season,episode){try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return []}};
    wrapped.__niakvioAllAnimeCurrentV1=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;
    try{if(typeof module!=="undefined"&&module.exports&&typeof module.exports==="object")module.exports.getStreams=wrapped}catch(_e){}
  }catch(_e){}
})();
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(text, MANAGED_FIX_ID, WRAPPER, data={
        "scope": "provider-local-current-wordpress-search-episode-embed",
        "providerBaseModified": False,
        "fixtureIdsHardcoded": False,
        "searchRoute": "/?s={title}",
        "episodeIdentity": "epl-num",
        "preserveEmbeds": True,
    })


if __name__ == "__main__":
    raise SystemExit("patch module only")