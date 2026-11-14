#!/usr/bin/env python3
"""VidSrc TMDB-direct signed-embed runtime resolver.

Residential Mac proof (2026-11-14):
- /vs_src.php?type=movie&id=157336 -> JSON src bound to /embed/movie/157336
- /vs_src.php?type=tv&id=1396&season=1&episode=1 -> JSON src bound to /embed/tv/1396/1/1
The returned signed player is ephemeral. It is never persisted; ProviderBase's
bounded terminal crawler resolves it at request time.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDSRC.TMDB_EMBED.RUNTIME.V1"
MARKER = "NIAKVIO_VIDSRC_TMDB_EMBED_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VIDSRC_TMDB_EMBED_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(args){
  var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
  try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&o.semanticType)||ctx.semanticType||"").toLowerCase();
  var raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||semantic||"").toLowerCase();
  if(raw==="series"||raw==="anime")raw="tv";
  if(raw!=="movie"&&raw!=="tv")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
  if(!/^\d+$/.test(id))return null;
  var season=Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1;
  var episode=Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1;
  return{type:raw,id:id,season:season,episode:episode}
}
function headers(ref){var h={"User-Agent":c.userAgent,"Accept":"application/json,text/plain,*/*"};if(ref)h.Referer=ref;return h}
async function jsonGet(url,ref){
  try{
    var r=typeof _fetch==="function"?await _fetch(url,{headers:headers(ref),redirect:"follow"}):await g.fetch(url,{headers:headers(ref),redirect:"follow"});
    if(!r||r.ok===false)return null;
    return await r.json()
  }catch(_e){return null}
}
function validPlayer(src,q){
  try{
    var u=new URL(src);
    var path=decodeURIComponent(u.pathname||"");
    if(q.type==="movie")return new RegExp("/embed/movie/"+q.id+"(?:/|$)","i").test(path);
    return new RegExp("/embed/tv/"+q.id+"/"+q.season+"/"+q.episode+"(?:/|$)","i").test(path)
  }catch(_e){return false}
}
function directMedia(u){return /\.(?:m3u8|mpd|mp4|m4v|mkv|webm)(?:[?#]|$)|\/(?:hls|dash)(?:\/|[?#]|$)/i.test(s(u))}
async function resolve(args){
  var q=req(args);if(!q)return[];
  var embed=c.base+(q.type==="movie"?"/embed/movie/"+encodeURIComponent(q.id):"/embed/tv/"+encodeURIComponent(q.id)+"/"+q.season+"/"+q.episode);
  var api=c.base+"/vs_src.php?type="+encodeURIComponent(q.type)+"&id="+encodeURIComponent(q.id);
  if(q.type==="tv")api+="&season="+q.season+"&episode="+q.episode;
  var data=await jsonGet(api,embed),src=s(data&&data.src);
  if(!/^https?:\/\//i.test(src)||!validPlayer(src,q))return[];
  var rows=[];
  if(directMedia(src)){
    rows=[{url:src,headers:{"Referer":embed,"User-Agent":c.userAgent},isDirect:true}]
  }else{
    try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([src],embed,Math.max(1,Number(c.maxDepth)||3))}catch(_e){rows=[]}
  }
  if(!Array.isArray(rows)||!rows.length)return[];
  var out=[],seen={};
  for(var i=0;i<rows.length&&out.length<Math.max(1,Number(c.maxStreams)||8);i++){
    var row=rows[i]||{},u=s(row.url);
    if(!/^https?:\/\//i.test(u)||seen[u])continue;
    seen[u]=1;
    var x=Object.assign({},row);
    x.url=u;x.provider="vidsrc";x.name=x.name||c.name;
    x.title=(x.title||c.name)+(q.type==="tv"?" | S"+q.season+"E"+q.episode:"");
    if(!x.headers)x.headers={"Referer":src,"User-Agent":c.userAgent};
    out.push(x)
  }
  return out
}
function install(o,k){
  if(!o||typeof o[k]!=="function"||o[k].__niakvioVidsrcTmdbEmbedV1)return false;
  var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};
  fn.__niakvioVidsrcTmdbEmbedV1=true;o[k]=fn;return true
}
var installed=false;
try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"vidsrc",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://vidsrc.sh",
        "name": "VidSrc",
        "maxDepth": 3,
        "maxStreams": 8,
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("VidSrc base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "tmdb-direct-json-signed-embed-v1",
            "identity": "tmdb-route-plus-exact-signed-embed-path",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "tv"],
            "terminalTraversal": "providerbase-bounded-direct-media-crawler",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "ephemeralSignedPlayerPersisted": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
