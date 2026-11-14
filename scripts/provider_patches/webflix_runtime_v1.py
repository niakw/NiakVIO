#!/usr/bin/env python3
"""Webflix provider-owned direct FastFlux runtime.

The public Webflix API exposes TMDB-addressed movie and episode endpoints.
This Lego intentionally uses only those deterministic public JSON contracts:
no challenge solver, browser automation, upstream JavaScript execution or
title-only matching is required for the primary path.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WEBFLIX.RUNTIME.V1"
MARKER = "NIAKVIO_WEBFLIX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_WEBFLIX_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function argsOf(args){
    var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
    try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
    var type=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    if(type==="series")type="tv";
    return {
      id:id,
      type:type==="movie"?"movie":"tv",
      season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,
      episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1
    };
  }
  function headers(){
    return {
      "Accept":"application/json,text/plain,*/*",
      "Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7",
      "Referer":c.base+"/",
      "User-Agent":c.userAgent
    };
  }
  async function jsonGet(path){
    var response=await g.fetch(c.base+path,{headers:headers(),redirect:"follow"});
    if(!response||!response.ok)throw new Error("webflix_http_"+String(response&&response.status||0));
    return await response.json();
  }
  function mediaUrl(row){
    var u=s(row&&row.url);
    if(!/^https?:\/\//i.test(u))return "";
    if(!/\.(?:mp4|m3u8)(?:$|[?#])/i.test(u))return "";
    return u;
  }
  function stream(row,q,label){
    var url=mediaUrl(row);if(!url)return [];
    return [{
      name:"Webflix"+(label?" - "+label:""),
      title:"Webflix"+(q.type==="tv"?" S"+String(q.season).padStart(2,"0")+"E"+String(q.episode).padStart(2,"0"):""),
      url:url,
      quality:s(row.quality||"Auto"),
      language:s(row.language||"fr"),
      size:s(row.size||""),
      provider:"webflix",
      headers:{
        "Referer":c.base+"/",
        "User-Agent":c.userAgent,
        "Accept":"video/*,*/*;q=0.8"
      }
    }];
  }
  async function movie(q){
    var data=await jsonGet("/api/fastflux?type=movie&tmdb_id="+encodeURIComponent(q.id));
    if(!data||data.success!==true||data.available!==true||!data.data)return [];
    var returned=s(data.data.tmdb_id);
    if(returned&&returned!==q.id)return [];
    return stream(data.data,q,"FastFlux");
  }
  async function episode(q){
    var discovery=await jsonGet("/api/series-season-discovery?tmdb_id="+encodeURIComponent(q.id));
    if(!discovery||discovery.success!==true||s(discovery.tmdb_id)!==q.id)return [];
    var key=String(q.season)+"-"+String(q.episode);
    var row=discovery.fastflux&&discovery.fastflux[key];
    if(row&&Number(row.season)===q.season&&Number(row.episode)===q.episode){
      var out=stream(row,q,"FastFlux");if(out.length)return out;
    }
    var data=await jsonGet(
      "/api/fastflux?type=episode&tmdb_id="+encodeURIComponent(q.id)+
      "&season="+encodeURIComponent(String(q.season))+
      "&episode="+encodeURIComponent(String(q.episode))
    );
    if(!data||data.success!==true||data.available!==true||!data.data)return [];
    if(Number(data.data.season)!==q.season||Number(data.data.episode)!==q.episode)return [];
    return stream(data.data,q,"FastFlux");
  }
  async function webflix(args){
    var q=argsOf(args);
    if(!/^\d+$/.test(q.id))return [];
    try{return q.type==="movie"?await movie(q):await episode(q)}catch(_e){return []}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioWebflixRuntimeV1)return false;
    var wrapped=async function(){return await webflix(arguments)};
    wrapped.__niakvioWebflixRuntimeV1=true;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://webflix.art").rstrip("/"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        ),
    }
    if not payload["base"].startswith(("http://", "https://")):
        raise ValueError("webflix runtime base must be http(s)")
    wrapper = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtimeFamily": "tmdb-direct-fastflux-v1",
            "identity": "requested-tmdb-id-plus-exact-tv-season-episode",
            "terminal": "direct-mp4-or-hls-only",
            "challengeSolver": False,
            "upstreamJsExecuted": False,
            "legacyExecutableSeed": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
