#!/usr/bin/env python3
"""Coflix current REST resolver adapter.

The public player uses GET /wp-json/coflix/v1/resolve with raw TMDB identity.
Signed play URLs are ephemeral runtime output and are never persisted in DATA.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.COFLIX.REST.RUNTIME.V1"
MARKER = "NIAKVIO_COFLIX_REST_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_COFLIX_REST_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function request(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var canonical=s((obj&&(obj.canonicalMediaType||obj.semanticType))||ctx.canonicalMediaType||"").toLowerCase();
    var rawType=s((obj&&(obj.mediaType||obj.type))||args[1]||ctx.requestType||ctx.mediaType||"").toLowerCase();
    var season=Number((obj&&obj.season)!=null?obj.season:(ctx.season!=null?ctx.season:args[2]))||0;
    var episode=Number((obj&&obj.episode)!=null?obj.episode:(ctx.episode!=null?ctx.episode:args[3]))||0;
    var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0];
    if(!/^\d+$/.test(id))return null;
    var type=(canonical==="movie"||rawType==="movie")?"movie":"tv";
    if(canonical==="anime")type=(season>0&&episode>0)?"tv":"movie";
    if(type==="tv"&&(!season||!episode))return null;
    return {id:id,type:type,season:season,episode:episode,canonical:canonical};
  }
  function headers(referer,accept){return {"User-Agent":c.userAgent,"Accept":accept||"application/json,*/*","Referer":referer||c.site+"/"}}
  async function getJson(url){try{var r=await g.fetch(url,{headers:headers(c.site+"/","application/json,*/*"),redirect:"follow"});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
  async function validHls(url){try{var r=await g.fetch(url,{headers:headers(c.site+"/","application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),redirect:"follow"});if(!r||!r.ok)return null;var text=await r.text();return /^#EXTM3U/m.test(text)?text:null}catch(_e){return null}}
  function quality(text){var best=0,re=/RESOLUTION=\d+x(\d+)/gi,m;while((m=re.exec(text||""))!==null){var n=parseInt(m[1],10)||0;if(n>best)best=n}return best?best+"p":"HD"}
  async function resolve(args){
    var q=request(args);if(!q)return [];
    var url=c.endpoint+"?tmdb="+encodeURIComponent(q.id)+"&type="+encodeURIComponent(q.type);
    if(q.type==="tv")url+="&season="+q.season+"&episode="+q.episode;
    var data=null;
    for(var i=0;i<c.maxResolveAttempts;i++){data=await getJson(url);if(data&&data.ok)break;if(!(data&&data.pending))break}
    if(!data||!data.ok)return [];
    var play=s(data.play);if(!/^https?:\/\//i.test(play))return [];
    var manifest=await validHls(play);if(!manifest)return [];
    var lang=s(data.lang||"Original");var host=s(data.host||"Direct");
    return [{name:"Coflix | "+host+" | "+lang,title:"Coflix | "+host+" | "+lang,url:play,quality:quality(manifest),language:lang,headers:headers(c.site+"/","application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"coflix",isDirect:true}];
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__niakvioCoflixRestV1)return false;var wrapped=async function(){return await resolve(arguments)};wrapped.__niakvioCoflixRestV1=true;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "site": str(cfg.get("site") or "https://coflix.group"),
        "endpoint": str(cfg.get("endpoint") or "https://coflix.group/wp-json/coflix/v1/resolve"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"),
        "maxResolveAttempts": int(cfg.get("max_resolve_attempts") or 3),
    }
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={"runtime": payload, "identity": "raw-tmdb-direct", "method": "GET-query", "signedMediaPersisted": False, "legacyExecutableSeed": False},
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
