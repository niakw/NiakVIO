#!/usr/bin/env python3
"""Core-wide contextual media-type resolver.

Nuvio client aliases (series/show/other) mean TV by default. A trusted anime
identity, including TMDB metadata, may refine that TV-shaped request to anime
before any provider-specific resolver sees it.

No credential is embedded. TMDB enrichment runs only when the runtime exposes
TMDB_API_KEY or TMDB_ACCESS_TOKEN; object-style requests can also carry trusted
metadata directly. Metadata failure is fail-open to tv.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1"


def _strip_existing(text: str) -> str:
    old = text.find(f"/* {MARKER}:")
    if old < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', old)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global media type resolution wrapper")
    return (text[:old] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "timeoutMs": max(1200, min(int(cfg.get("timeout_ms", 4500)), 10000)),
        "revision": "series-tv-tmdb-anime-v1",
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if f"/* {marker} */" in text:
        return text
    text = _strip_existing(text)

    js = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function alias(v){var x=s(v||"movie").toLowerCase();if(x==="series"||x==="show"||x==="other")return"tv";if(x==="anime")return"anime";if(x==="movie")return"movie";return"tv"}
function rows(v){return Array.isArray(v)?v:[]}
function keywordRows(m){var k=m&&m.keywords;return rows(k&&((k.results||k.keywords)||k))}
function animeMeta(m){
  if(!m||typeof m!=="object")return false;
  var explicit=s(m.canonicalMediaType||m.canonical_media_type||m.category).toLowerCase();
  if(explicit==="anime")return true;
  var keywords=keywordRows(m).map(function(x){return s(x&&x.name).toLowerCase()});
  if(keywords.indexOf("anime")>=0)return true;
  var genres=rows(m.genres),ids=rows(m.genre_ids||m.genreIds).map(Number);
  for(var i=0;i<genres.length;i++){if(Number(genres[i]&&genres[i].id)===16)ids.push(16)}
  var animation=ids.indexOf(16)>=0||genres.some(function(x){return s(x&&x.name).toLowerCase()==="animation"});
  var lang=s(m.original_language||m.originalLanguage).toLowerCase();
  var countries=rows(m.origin_country||m.originCountry).map(function(x){return s(x).toUpperCase()});
  var prod=rows(m.production_countries||m.productionCountries).map(function(x){return s(x&&x.iso_3166_1).toUpperCase()});
  var japanese=lang==="ja"||countries.indexOf("JP")>=0||prod.indexOf("JP")>=0;
  return animation&&japanese;
}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
async function tmdb(tvId){
  var key=s(g&&g.TMDB_API_KEY),token=s(g&&g.TMDB_ACCESS_TOKEN);
  if(!/^\\d+$/.test(s(tvId))||(!key&&!token)||!g||typeof g.fetch!=="function")return null;
  try{
    var u="https://api.themoviedb.org/3/tv/"+encodeURIComponent(s(tvId))+"?append_to_response=keywords&language=en-US";
    if(key)u+="&api_key="+encodeURIComponent(key);
    var h={Accept:"application/json"};if(token)h.Authorization="Bearer "+token;
    var r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});
    if(!r||!r.ok||typeof r.json!=="function")return null;
    return await r.json();
  }catch(_){return null}
}
function objectRequest(a){return a&&typeof a==="object"&&!Array.isArray(a)}
async function resolve(a){
  var first=a[0],obj=objectRequest(first),q=obj?Object.assign({},first):null;
  var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a[1]||"movie");
  var type=alias(input);
  var category=obj?s(q.category).toLowerCase():"";
  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);
  if(category==="anime"||animeMeta(metadata))type="anime";
  var id=obj?s(q.tmdbId||q.tmdb_id||q.id):s(first);
  if(type==="tv"&&/^\\d+$/.test(id)){
    var m=await tmdb(id);if(animeMeta(m))type="anime";
  }
  if(obj){
    q.nuvioInputMediaType=input;
    q.mediaType=type;q.type=type;
    if(type==="anime")q.category="anime";else if(!q.category||["series","show","other"].indexOf(s(q.category).toLowerCase())>=0)q.category=type;
    var out=[q];for(var i=1;i<a.length;i++)out.push(a[i]);return out;
  }
  var out=Array.prototype.slice.call(a);out[1]=type;return out;
}
function install(o,k){
  if(!o||typeof o[k]!=="function"||o[k].__nuvioMediaTypeResolutionV1)return false;
  var native=o[k];
  var wrap=async function(){var a=await resolve(arguments);return native.apply(this,a)};
  wrap.__nuvioMediaTypeResolutionV1=true;
  o[k]=wrap;return true;
}
var ok=false;
try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}
try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)

    return text.rstrip() + "\n" + js.lstrip()


if __name__ == "__main__":
    raise SystemExit("patch module only")
