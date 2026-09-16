#!/usr/bin/env python3
"""AllWish clean current-site runtime (search -> episode -> server -> embed)."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLWISH.CURRENT.RUNTIME.V1"
MARKER = "NIAKVIO_ALLWISH_CURRENT_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ALLWISH_CURRENT_RUNTIME_V1 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioAllWishCurrentV1)return;
    var original=_spv4GetStreams;
    var BASE="https://all-wish.me";
    var UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36";
    function headers(ref,json){
      var h={"User-Agent":UA,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Accept":json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,text/plain,*/*"};
      if(ref)h.Referer=ref;
      if(json)h["X-Requested-With"]="XMLHttpRequest";
      return h;
    }
    function attr(raw,name){
      var re=new RegExp("(?:^|\\s)"+name+"\\s*=\\s*([\\\"'])((?:.(?!\\1))*.?)\\1","i"),m=re.exec(String(raw||""));
      if(m)return m[2];
      re=new RegExp("(?:^|\\s)"+name+"\\s*=\\s*\\\"([^\\\"]*)\\\"","i");m=re.exec(String(raw||""));
      if(m)return m[1];
      re=new RegExp("(?:^|\\s)"+name+"\\s*=\\s*'([^']*)'","i");m=re.exec(String(raw||""));
      return m?m[1]:"";
    }
    function candidates(html,meta){
      var out=[],re=/<a\b([^>]*)href=["']([^"']*\/watch\/[^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,m;
      var expected=_uniq([meta&&meta.title].concat(meta&&Array.isArray(meta.aliases)?meta.aliases:[])).map(_slug).filter(Boolean);
      while((m=re.exec(String(html||"")))&&out.length<80){
        var attrs=String(m[1]||"")+" "+String(m[3]||""),href=_absolute(m[2],BASE);if(!href)continue;
        var path="";try{path=new URL(href).pathname.toLowerCase()}catch(_e){}
        var score=0;
        for(var i=0;i<expected.length;i++){var s=expected[i];if(s.length>=4&&path.indexOf("/watch/"+s)>=0)score=Math.max(score,80);}
        var body=_slug(String(m[4]||"").replace(/<[^>]+>/g," "));
        for(var j=0;j<expected.length;j++){var e=expected[j];if(e&&body.indexOf(e)>=0)score=Math.max(score,100);}
        if(score>0)out.push({href:href,id:attr(attrs,"data-tip"),score:score});
      }
      out.sort(function(a,b){return b.score-a.score});return out;
    }
    async function current(tmdbId,mediaType,season,episode){
      if(_mediaNamespace(mediaType)==="movie")return [];
      var ep=Math.floor(Number(episode)||0);if(ep<=0)return [];
      var meta=await _tmdb(tmdbId,mediaType);if(!meta||!meta.title)return [];
      var search=BASE+"/filter?keyword="+encodeURIComponent(meta.title),sr;
      try{sr=await _fetch(search,{headers:headers(BASE+"/",false)})}catch(_e){return []}
      var searchHtml=await sr.text(),rows=candidates(searchHtml,meta);if(!rows.length)return [];
      for(var ci=0;ci<Math.min(rows.length,3);ci++){
        var candidate=rows[ci],watch=candidate.href.replace(/\/ep-\d+(?:[/?#].*)?$/i,"/ep-"+ep),wr,watchHtml;
        try{wr=await _fetch(watch,{headers:headers(search,false)});watchHtml=await wr.text()}catch(_e){continue}
        var showId="",wm=watchHtml.match(/id=["']watch-page["'][^>]*\bdata-id=["'](\d+)["']/i)||watchHtml.match(/\bdata-id=["'](\d+)["'][^>]*\bid=["']watch-page["']/i);
        if(wm)showId=wm[1];if(!showId&&/^\d+$/.test(String(candidate.id||"")))showId=String(candidate.id);if(!showId)continue;
        var listValue;
        try{var lr=await _fetch(BASE+"/ajax/episode/list/"+encodeURIComponent(showId),{headers:headers(watch,true)});listValue=await lr.json()}catch(_e){continue}
        var result=String(listValue&&listValue.result||""),ar=/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,am,serverKey="";
        while((am=ar.exec(result))){var attrs=am[1]||"",slug=attr(attrs,"data-slug");if(String(slug)!==String(ep))continue;serverKey=attr(attrs,"data-ids");if(serverKey)break;}
        if(!serverKey)continue;
        var serverList;
        try{var sl=await _fetch(BASE+"/ajax/server/list?servers="+encodeURIComponent(serverKey),{headers:headers(watch,true)});serverList=await sl.json()}catch(_e){continue}
        var markup=String(serverList&&serverList.result||""),ids=[],seen=Object.create(null),ir=/data-link-id=["']([^"']+)["']/gi,im;
        while((im=ir.exec(markup))&&ids.length<8){if(!seen[im[1]]){seen[im[1]]=1;ids.push(im[1]);}}
        var streams=[];
        for(var ii=0;ii<ids.length&&streams.length<6;ii++){
          try{
            var rr=await _fetch(BASE+"/ajax/server?get="+encodeURIComponent(ids[ii]),{headers:headers(watch,true)}),rv=await rr.json();
            var u=rv&&rv.result&&typeof rv.result.url==="string"?rv.result.url:"";if(!/^https?:\/\//i.test(u))continue;
            streams.push({name:NIAKVIO_PROVIDER_MODEL.displayName,title:NIAKVIO_PROVIDER_MODEL.displayName+(streams.length?" #"+(streams.length+1):""),url:u,headers:{Referer:watch,Origin:BASE}});
          }catch(_e){}
        }
        if(streams.length)return streams;
      }
      return [];
    }
    var wrapped=async function(tmdbId,mediaType,season,episode){
      try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}
      try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return []}
    };
    wrapped.__niakvioAllWishCurrentV1=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;
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
            "scope": "provider-local-current-search-episode-server-embed",
            "providerBaseModified": False,
            "fixtureIdsHardcoded": False,
            "identityRequired": True,
            "currentApi": ["/filter?keyword=", "/ajax/episode/list/{id}", "/ajax/server/list?servers=", "/ajax/server?get="],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")