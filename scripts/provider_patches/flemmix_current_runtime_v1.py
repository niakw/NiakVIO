#!/usr/bin/env python3
"""Flemmix clean current-site runtime using its JSON search and signed embeds."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.FLEMMIX.CURRENT.RUNTIME.V1"
MARKER = "NIAKVIO_FLEMMIX_CURRENT_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_FLEMMIX_CURRENT_RUNTIME_V1 */
/* NIAKVIO_FLEMMIX_NO_STATIC_TERMINAL_FALLBACK_V61 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioFlemmixCurrentV1)return;
    var original=_spv4GetStreams,
        BASE=(function(){
          var raw="";
          try{raw=_text((NIAKVIO_PROVIDER_MODEL&&(
            NIAKVIO_PROVIDER_MODEL.officialSite||NIAKVIO_PROVIDER_MODEL.knownSite
          ))||"");}catch(_e){raw="";}
          try{raw=_substituteDomain(raw);}catch(_e){}
          return String(raw||"").replace(/\/+$/g,"");
        })(),
        UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36";
    function headers(ref,json){return {"User-Agent":UA,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Accept":json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,text/plain,*/*","Referer":ref||BASE+"/"};}
    function expectedSlugs(meta){return _uniq([meta&&meta.title].concat(meta&&Array.isArray(meta.aliases)?meta.aliases:[])).map(_slug).filter(Boolean);}
    function identityScore(row,meta,lane){
      if(!row||typeof row!=="object")return -1;
      var rt=String(row.type||"").toLowerCase();if(lane==="movie"&&rt!=="movie")return -1;if(lane!=="movie"&&!/(?:tv|series|show)/.test(rt))return -1;
      var actual=_slug(row.title||""),score=0,exp=expectedSlugs(meta);for(var i=0;i<exp.length;i++){if(actual===exp[i])score=Math.max(score,100);else if(exp[i].length>=5&&(actual.indexOf(exp[i])>=0||exp[i].indexOf(actual)>=0))score=Math.max(score,70);}
      var ey=String(meta&&meta.year||"").slice(0,4),ay=String(row.year||"").slice(0,4);if(ey&&ay){if(ey===ay)score+=20;else score-=30;}return score;
    }
    function embeds(html,base){
      var out=[],seen=Object.create(null),m,re=/data-url=["']([^"']+)["']/gi;
      function add(raw){var u=_absolute(raw,base);if(!/^https?:/i.test(u)||seen[u])return;if(/\/embed\/video\//i.test(u)){seen[u]=1;out.push(u);}}
      while((m=re.exec(String(html||"")))&&out.length<12)add(m[1]);
      re=/<iframe[^>]+src=["']([^"']+)["']/gi;while((m=re.exec(String(html||"")))&&out.length<12){var u=_absolute(m[1],base);if(/^https?:/i.test(u)&&/(?:vidsrc|vsembed|voe\.|\/embed\/)/i.test(u)&&!seen[u]){seen[u]=1;out.push(u);}}
      return out;
    }
    function visible(v){var src=String(v==null?"":v),out="",inTag=false;for(var i=0;i<src.length;i++){var ch=src.charAt(i);if(ch==="<"){inTag=true;out+=" ";continue}if(ch===">"){inTag=false;continue}if(!inTag)out+=ch}return out.replace(/\s+/g," ").trim()} function links(html,base){var out=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(String(html||"")))&&out.length<200){var u=_absolute(m[1],base);if(!u||seen[u])continue;seen[u]=1;out.push({url:u,text:visible(m[2])});}return out;}
    async function page(url,ref){var r=await _fetch(url,{headers:headers(ref,false)});return {url:r.url||url,text:await r.text()};}
    async function current(tmdbId,mediaType,season,episode){
      var lane=_mediaNamespace(mediaType),meta=await _tmdb(tmdbId,mediaType);if(!meta||!meta.title||!BASE)return [];
      var searchUrl=BASE+"/search?q="+encodeURIComponent(meta.title),rows;
      try{var sr=await _fetch(searchUrl,{headers:headers(BASE+"/",true)});rows=await sr.json()}catch(_e){return []}
      if(!Array.isArray(rows))return [];
      var ranked=rows.map(function(row){return {row:row,score:identityScore(row,meta,lane)}}).filter(function(x){return x.score>0}).sort(function(a,b){return b.score-a.score});if(!ranked.length)return [];
      for(var ri=0;ri<Math.min(ranked.length,3);ri++){
        var detailUrl=_absolute(ranked[ri].row.url,BASE+"/"),detail;try{detail=await page(detailUrl,searchUrl)}catch(_e){continue}
        var target=detail,found=[];
        if(lane!=="movie"){
          var s=Math.floor(Number(season)||0),e=Math.floor(Number(episode)||0);if(s<=0||e<=0)continue;
          var seasonRows=links(detail.text,detail.url).filter(function(row){return new RegExp("(?:saison|season)[-_/ ]*"+s+"(?:$|[/?#-])","i").test(row.url+" "+row.text)||new RegExp("^S"+s+"(?:\\s|$)","i").test(row.text)});
          if(seasonRows.length){try{target=await page(seasonRows[0].url,detail.url)}catch(_e){continue}}
          var epRows=links(target.text,target.url).filter(function(row){var hay=row.url+" "+row.text;return new RegExp("(?:episode|ep)[-_/ .]*0*"+e+"(?:$|[/?# .-])","i").test(hay)||new RegExp("(?:^|\\s)E0*"+e+"(?:\\s|$)","i").test(row.text)});
          if(epRows.length){try{target=await page(epRows[0].url,target.url)}catch(_e){continue}}
          found=embeds(target.text,target.url);
          if(!found.length){
            var marker=new RegExp("(?:episode|ep)[^0-9]{0,12}0*"+e+"(?:[^0-9]|$)","i"),mm=marker.exec(target.text);
            if(mm){var slice=target.text.slice(Math.max(0,mm.index-2500),Math.min(target.text.length,mm.index+10000));found=embeds(slice,target.url);}
          }
        }else found=embeds(detail.text,detail.url);
        if(found.length){var ref=target.url;return found.slice(0,8).map(function(u,index){return {name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName+(index?" #"+(index+1):""),url:u,headers:{Referer:ref,Origin:BASE},__nuvioCorrelatedPlayerFallbackV1:{url:u}}});}
      }
      return [];
    }
    var wrapped=async function(tmdbId,mediaType,season,episode){try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return []}};
    wrapped.__niakvioFlemmixCurrentV1=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;try{if(typeof module!=="undefined"&&module.exports&&typeof module.exports==="object")module.exports.getStreams=wrapped}catch(_e){}
  }catch(_e){}
})();
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        WRAPPER,
        data={
            "scope": "provider-local-json-search-signed-embed-runtime",
            "providerBaseModified": False,
            "fixtureIdsHardcoded": False,
            "searchRoute": "/search?q={title}",
            "identityRequired": True,
            "embedSignaturesHardcoded": False,
            "domainAuthority": "provider-model-official-site",
            "legacyHostHardcoded": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")