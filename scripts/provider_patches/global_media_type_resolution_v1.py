#!/usr/bin/env python3
"""Core-wide contextual media-type resolver.

Nuvio client aliases (series/show/other) mean TV by default. A trusted anime
identity, including TMDB metadata, may refine that TV-shaped request to anime
before any provider-specific resolver sees it.

No NiakVIO credential is embedded. The resolver first reuses a runtime/provider
TMDB credential when one already exists; otherwise it may classify TV-shaped
requests from the public TMDB title page. Object-style requests can also carry
trusted metadata directly. Ambiguous TV/anime metadata failure is fail-closed.
TMDB identity is namespaced: anime-series share the TMDB TV namespace.
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
    before = text[:old].rstrip()
    after = text[end + 2 :].lstrip()
    if before and after:
        return before + "\n" + after
    return before or after


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    semantic_types = []
    for value in cfg.get("semantic_types") or []:
        item = str(value).strip().lower()
        if item in {"movie", "tv", "anime"} and item not in semantic_types:
            semantic_types.append(item)
    payload = {
        "timeoutMs": max(900, min(int(cfg.get("timeout_ms", 1800)), 5000)),
        "semanticTypes": semantic_types,
        "revision": "tmdb-first-provider-entity-gate-v3",
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    # This resolver is the outermost request layer. Even when the exact marker
    # already exists, strip and re-append it so any Core layer rebuilt during
    # the same pass cannot move outside the canonical media-type boundary.
    text = _strip_existing(text)

    js = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function alias(v){var x=s(v||"movie").toLowerCase();if(x==="series"||x==="show"||x==="other")return"tv";if(x==="anime")return"anime";if(x==="movie")return"movie";return"tv"}
function namespaceOf(v){var x=alias(v);return x==="movie"?"movie":"tv"}
function rows(v){return Array.isArray(v)?v:[]}
function keywordRows(m){var k=m&&m.keywords;return rows(k&&((k.results||k.keywords)||k))}
function htmlAnime(h){
  var x=s(h);if(!x)return false;
  var keyword=/(?:>|\"|&quot;)\s*anime\s*(?:<|\"|&quot;)/i.test(x)||/\/keyword\/[^"'<>\s]*anime/i.test(x);
  var animation=/\/genre\/16(?:-|\/|\?|\")/i.test(x)||/>\s*Animation\s*</i.test(x)||/\"name\"\s*:\s*\"Animation\"/i.test(x);
  var japanese=/Original\s+Language[\s\S]{0,260}Japanese/i.test(x)||/\"original_language\"\s*:\s*\"ja\"/i.test(x);
  return keyword||(animation&&japanese);
}
function animeMeta(m){
  if(!m||typeof m!=="object")return false;
  if(typeof m.__nuvioPublicHtml==="string")return htmlAnime(m.__nuvioPublicHtml);
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
function localKey(){
  try{if(g&&s(g.TMDB_API_KEY))return s(g.TMDB_API_KEY)}catch(_){}
  try{if(typeof TMDB_API_KEY!=="undefined"&&s(TMDB_API_KEY))return s(TMDB_API_KEY)}catch(_){}
  return "";
}
function localToken(){
  try{if(g&&s(g.TMDB_ACCESS_TOKEN))return s(g.TMDB_ACCESS_TOKEN)}catch(_){}
  try{if(typeof TMDB_ACCESS_TOKEN!=="undefined"&&s(TMDB_ACCESS_TOKEN))return s(TMDB_ACCESS_TOKEN)}catch(_){}
  return "";
}
var mediaCache=Object.create(null);
try{if(g)g.__nuvioTmdbMetadataCacheV1=mediaCache}catch(_){}
function htmlDecode(v){return s(v).replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/&amp;/gi,"&").replace(/&lt;/gi,"<").replace(/&gt;/gi,">")}
function publicMeta(html,namespace,id){
  var h=s(html),title="",year="";
  var m=h.match(/<meta[^>]+(?:property|name)=["'](?:og:title|twitter:title|title)["'][^>]+content=["']([^"']+)["']/i)
    ||h.match(/<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["'](?:og:title|twitter:title|title)["']/i)
    ||h.match(/<title[^>]*>([^<]+)<\/title>/i);
  if(m)title=htmlDecode(m[1]).replace(/\s*[—|-]\s*The Movie Database.*$/i,"").replace(/\s*\((?:TV Series|Movie)?\s*(\d{4})[^)]*\)\s*$/i,function(_x,y){if(!year)year=y;return""}).trim();
  var y=h.match(/(?:datePublished|release_date|first_air_date)["'\s:=]+(?:content=["'])?(\d{4})[-/]/i)
    ||h.match(/(?:release_date|first_air_date)[\s\S]{0,160}?(19\d{2}|20\d{2})/i)
    ||h.match(/class=["'][^"']*release_date[^"']*["'][^>]*>[^(<]*\(?(19\d{2}|20\d{2})/i);
  if(y&&!year)year=y[1];
  var out={__nuvioPublicHtml:h,__nuvioTmdbNamespace:namespace,__nuvioTmdbId:id};
  if(namespace==="movie"){out.title=title;out.original_title=title;if(year)out.release_date=year+"-01-01"}
  else{out.name=title;out.original_name=title;if(year)out.first_air_date=year+"-01-01"}
  return out;
}
function hasTmdbMetadata(m){
  return !!(m&&typeof m==="object"&&(
    Array.isArray(m.genres)||Array.isArray(m.genre_ids)||Array.isArray(m.genreIds)||
    m.original_language||m.originalLanguage||m.origin_country||m.originCountry||
    m.production_countries||m.productionCountries||m.keywords
  ));
}
async function tmdb(namespaceValue,tmdbId){
  var namespace=namespaceValue==="movie"?"movie":"tv",id=s(tmdbId),cacheKey=namespace+":"+id,key=localKey(),token=localToken();
  if(!/^\d+$/.test(id)||!g||typeof g.fetch!=="function")return null;
  if(Object.prototype.hasOwnProperty.call(mediaCache,cacheKey))return await mediaCache[cacheKey];
  var pending=(async function(){
    try{
      if(key||token){
        var u="https://api.themoviedb.org/3/"+namespace+"/"+encodeURIComponent(id)+"?append_to_response=keywords&language=en-US";
        if(key)u+="&api_key="+encodeURIComponent(key);
        var h={Accept:"application/json"};if(token)h.Authorization="Bearer "+token;
        var api=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});
        if(api&&api.ok&&typeof api.json==="function")return await api.json();
      }
      var publicUrl="https://www.themoviedb.org/"+namespace+"/"+encodeURIComponent(id)+"?language=en-US";
      var page=await g.fetch(publicUrl,{
        headers:{Accept:"text/html","Range":"bytes=0-65535","Cache-Control":"max-stale=86400"},
        redirect:"follow",
        signal:timeout()
      });
      if(!page||!page.ok||typeof page.text!=="function")return null;
      return publicMeta(await page.text(),namespace,id);
    }catch(_){return null}
  })();
  mediaCache[cacheKey]=pending;
  var value=await pending;
  mediaCache[cacheKey]=value;
  return value;
}
async function canonicalType(id,input,metadata){
  var namespace=namespaceOf(input);
  var m=hasTmdbMetadata(metadata)?metadata:await tmdb(namespace,id);
  if(!m)return null;
  return animeMeta(m)?"anime":namespace;
}
function objectRequest(a){return a&&typeof a==="object"&&!Array.isArray(a)}
async function resolve(a){
  var first=a[0],obj=objectRequest(first),q=obj?Object.assign({},first):null;
  var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a[1]||"movie");
  var transport=alias(input),namespace=namespaceOf(input);
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  if(semantic.length){
    if(namespace==="movie"&&semantic.indexOf("movie")<0&&semantic.indexOf("anime")<0)return null;
    if(namespace==="tv"&&semantic.indexOf("tv")<0&&semantic.indexOf("anime")<0)return null;
  }
  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);
  var id=obj?s(q.tmdbId||q.tmdb_id||q.id):s(first);
  var type=await canonicalType(id,input,metadata);
  if(!type)return null;
  if(semantic.length&&semantic.indexOf(type)<0)return null;
  var context={
    tmdbId:id,
    tmdbNamespace:namespace,
    tmdbIdentity:namespace+":"+id,
    canonicalMediaType:type,
    nuvioInputMediaType:input
  };
  if(obj){
    q.nuvioInputMediaType=input;
    q.tmdbNamespace=namespace;
    q.tmdbIdentity=namespace+":"+id;
    q.canonicalMediaType=type;
    q.mediaType=type;q.type=type;
    if(type==="anime")q.category="anime";else if(!q.category||["series","show","other"].indexOf(s(q.category).toLowerCase())>=0)q.category=type;
    var out=[q];for(var i=1;i<a.length;i++)out.push(a[i]);out.__nuvioContext=context;return out;
  }
  var out=Array.prototype.slice.call(a);out[1]=type;out.__nuvioContext=context;return out;
}
function install(o,k){
  if(!o||typeof o[k]!=="function"||o[k].__nuvioMediaTypeResolutionV1)return false;
  var native=o[k];
  var wrap=async function(){
    var a=await resolve(arguments);
    if(!a)return [];
    var had=false,previous;
    try{had=!!(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"));previous=g&&g.__nuvioMediaContext}catch(_){}
    try{
      if(g)g.__nuvioMediaContext=a.__nuvioContext||null;
      return await native.apply(this,a);
    }finally{
      try{if(g){if(had)g.__nuvioMediaContext=previous;else delete g.__nuvioMediaContext}}catch(_){}
    }
  };
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
