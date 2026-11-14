#!/usr/bin/env python3
"""Webflix TMDB-direct FastFlux runtime oracle.

Residential Mac proof (2026-11-14):
- movie: /api/fastflux?type=movie&tmdb_id={tmdbId}
- episode: /api/fastflux?type=episode&tmdb_id={tmdbId}&season={season}&episode={episode}
Both returned exact structured identity and direct MP4 media for representative fixtures.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WEBFLIX.FASTFLUX.RUNTIME.V1"
MARKER = "NIAKVIO_WEBFLIX_FASTFLUX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_WEBFLIX_FASTFLUX_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function requestOf(a){
  var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
  try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&o.semanticType)||ctx.semanticType||"").toLowerCase();
  var raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||semantic||"").toLowerCase();
  if(raw==="series")raw="tv";
  var type=raw==="movie"?"movie":"tv";
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId);
  if(!/^\d+$/.test(id))return null;
  var season=Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:ctx.season))||1;
  var episode=Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:ctx.episode))||1;
  return{type:type,semantic:semantic==="anime"?"anime":type,tmdbId:id,season:season,episode:episode}
}
async function jsonGet(url){
  try{
    var r=await g.fetch(url,{headers:{
      "Accept":"application/json",
      "Referer":c.base+"/",
      "User-Agent":c.ua
    }});
    if(!r||!r.ok)return null;
    return await r.json();
  }catch(_e){return null}
}
function validUrl(v){return /^https?:\/\//i.test(s(v))&&!/\b(?:example\.com|localhost)\b/i.test(s(v))}
async function resolve(a,_ctx){
  var q=requestOf(a);if(!q)return[];
  var url=c.base+"/api/fastflux?type="+(q.type==="movie"?"movie":"episode")+"&tmdb_id="+encodeURIComponent(q.tmdbId);
  if(q.type!=="movie")url+="&season="+encodeURIComponent(String(q.season))+"&episode="+encodeURIComponent(String(q.episode));
  var body=await jsonGet(url);
  if(!body||body.success!==true||body.available!==true||!body.data||typeof body.data!=="object")return[];
  var d=body.data;
  if(q.type==="movie"){
    if(String(d.tmdb_id||"")!==q.tmdbId)return[];
  }else{
    if(Number(d.season)!==q.season||Number(d.episode)!==q.episode)return[];
  }
  if(!validUrl(d.url))return[];
  var lang=s(d.language||"VF").toUpperCase();
  var quality=s(d.quality||"HD");
  var title=s(d.title||"Webflix");
  if(q.type!=="movie")title="Webflix S"+q.season+"E"+q.episode;
  return [{
    name:c.name,
    title:title,
    url:s(d.url),
    quality:quality,
    language:lang,
    size:s(d.size||""),
    provider:"webflix",
    headers:{"Referer":c.base+"/"}
  }]
}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"webflix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://webflix.art",
        "name": "Webflix",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("Webflix base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "tmdb-direct-json-media-v1",
            "identity": "movie=tmdb_id; tv=tmdb-request-plus-exact-season-episode",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "tv"],
            "terminalMedia": "direct-mp4-or-hls",
            "residentialOracle": True,
            "upstreamJsExecuted": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
