#!/usr/bin/env python3
"""Core-wide contextual media-type resolver.

Nuvio client aliases (series/show/other) mean TV by default. A trusted anime
identity, including TMDB metadata, may refine that TV-shaped request to anime
before any provider-specific resolver sees it.

TMDB API metadata is authoritative when available. The build may embed an
obfuscated runtime-only TMDB v3 API key generated from the repository secret;
the plaintext key is never committed and is never passed into provider business
logic. Object-style requests can also carry trusted TMDB metadata directly.

A conclusive TMDB classification still enforces provider semantic capabilities.
Only infrastructure failure (timeout/network/auth/rate-limit/5xx/unparseable
response) degrades to a fail-open transport/semantic fallback so one metadata
outage cannot suppress the entire provider catalogue. No public HTML scraping is
used as a classification substitute.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MARKER = "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1"
ROOT = Path(__file__).resolve().parents[2]
RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"


def _runtime_key_payload() -> dict[str, Any]:
    try:
        value = json.loads(RUNTIME_KEY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict) or int(value.get("version") or 0) != 1:
        return {}
    salt = str(value.get("salt") or "").strip()
    cipher = value.get("cipher")
    if not salt or not isinstance(cipher, list) or not cipher:
        return {}
    cleaned: list[int] = []
    for item in cipher:
        try:
            number = int(item)
        except (TypeError, ValueError):
            return {}
        if number < 0 or number > 255:
            return {}
        cleaned.append(number)
    return {"tmdbKeySalt": salt, "tmdbKeyCipher": cleaned}


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
        "providerTimeoutMs": max(5_000, min(int(cfg.get("provider_timeout_ms", 25_000)), 120_000)),
        "semanticTypes": semantic_types,
        "revision": "tmdb-api-first-every-provider-v11-global-budget",
        **_runtime_key_payload(),
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    # This resolver is the outermost request layer. Even when the exact marker
    # already exists, strip and re-append it so any Core layer rebuilt during
    # the same pass cannot move outside the canonical media-type boundary.
    text = _strip_existing(text)

    js = r'''
/* MARKER_PLACEHOLDER */
/* NUVIO_GLOBAL_PROVIDER_EXECUTION_BUDGET_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function normalizeKey(v){var x=s(v);if(x.length===33&&x.charCodeAt(0)===92&&/^[0-9a-fA-F]{32}$/.test(x.slice(1)))x=x.slice(1);return /^[0-9a-fA-F]{32}$/.test(x)?x:""}
function alias(v){var x=s(v||"movie").toLowerCase();if(x==="series"||x==="show"||x==="other")return"tv";if(x==="anime")return"anime";if(x==="movie")return"movie";return"tv"}
function namespaceOf(v){var x=alias(v);return x==="movie"?"movie":"tv"}
function namespaceCandidates(v,season,episode,semantic){
  var raw=s(v||"movie").toLowerCase();
  if(raw==="movie")return["movie"];
  if(raw==="anime"){
    if(season!=null||episode!=null)return["tv"];
    return["tv","movie"];
  }
  return["tv"];
}
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
function embeddedKey(){
  var salt=s(c.tmdbKeySalt),cipher=rows(c.tmdbKeyCipher);
  if(!salt||!cipher.length)return"";
  var material=salt+"|NiakVIO/TMDB/v1",seed=2166136261>>>0;
  for(var i=0;i<material.length;i++){seed^=material.charCodeAt(i);seed=Math.imul(seed,16777619)>>>0}
  var out="";
  for(var j=0;j<cipher.length;j++){
    seed^=(seed<<13);seed>>>=0;seed^=(seed>>>17);seed>>>=0;seed^=(seed<<5);seed>>>=0;
    out+=String.fromCharCode((Number(cipher[j])&255)^(seed&255));
  }
  return out;
}
function localKey(){
  var key="";
  try{key=normalizeKey(g&&g.TMDB_API_KEY);if(key)return key}catch(_){}
  try{if(typeof TMDB_API_KEY!=="undefined"){key=normalizeKey(TMDB_API_KEY);if(key)return key}}catch(_){}
  try{return normalizeKey(embeddedKey())}catch(_){return""}
}
function localToken(){
  try{if(g&&s(g.TMDB_ACCESS_TOKEN))return s(g.TMDB_ACCESS_TOKEN)}catch(_){}
  try{if(typeof TMDB_ACCESS_TOKEN!=="undefined"&&s(TMDB_ACCESS_TOKEN))return s(TMDB_ACCESS_TOKEN)}catch(_){}
  return "";
}
var mediaCache=Object.create(null);
try{if(g)g.__nuvioTmdbMetadataCacheV1=mediaCache}catch(_){}
function hasTmdbMetadata(m){
  return !!(m&&typeof m==="object"&&(
    Array.isArray(m.genres)||Array.isArray(m.genre_ids)||Array.isArray(m.genreIds)||
    m.original_language||m.originalLanguage||m.origin_country||m.originCountry||
    m.production_countries||m.productionCountries||m.keywords
  ));
}
async function apiJson(url){
  var key=localKey(),token=localToken();
  if(!g||typeof g.fetch!=="function"||(!key&&!token))return{state:"unavailable",value:null};
  try{
    if(key)url+=(url.indexOf("?")>=0?"&":"?")+"api_key="+encodeURIComponent(key);
    var h={Accept:"application/json"};if(token)h.Authorization="Bearer "+token;
    var api=await g.fetch(url,{headers:h,redirect:"follow",signal:timeout()});
    if(!api)return{state:"unavailable",value:null};
    if(api.status===404)return{state:"not_found",value:null};
    if(!api.ok||typeof api.json!=="function")return{state:"unavailable",value:null};
    var value=await api.json();
    if(!value||typeof value!=="object")return{state:"unavailable",value:null};
    return{state:"ok",value:value};
  }catch(_){return{state:"unavailable",value:null}}
}
async function findTmdb(imdbId,candidates){
  var imdb=s(imdbId).replace(/^imdb:/i,"").toLowerCase(),cacheKey="find:"+imdb;
  if(!/^tt\d+$/.test(imdb))return{state:"not_found",tmdbId:"",namespace:"",metadata:null,imdbId:""};
  if(Object.prototype.hasOwnProperty.call(mediaCache,cacheKey))return await mediaCache[cacheKey];
  var pending=(async function(){
    var probe=await apiJson("https://api.themoviedb.org/3/find/"+encodeURIComponent(imdb)+"?external_source=imdb_id");
    if(!probe||probe.state!=="ok")return{state:probe&&probe.state||"unavailable",tmdbId:"",namespace:"",metadata:null,imdbId:imdb};
    for(var i=0;i<candidates.length;i++){
      var namespace=candidates[i]==="movie"?"movie":"tv";
      var list=namespace==="movie"?rows(probe.value.movie_results):rows(probe.value.tv_results);
      for(var j=0;j<list.length;j++){
        var row=list[j],id=s(row&&row.id);
        if(/^\d+$/.test(id))return{state:"ok",tmdbId:id,namespace:namespace,metadata:row,imdbId:imdb};
      }
    }
    return{state:"not_found",tmdbId:"",namespace:"",metadata:null,imdbId:imdb};
  })();
  mediaCache[cacheKey]=pending;
  var value=await pending;
  mediaCache[cacheKey]=value;
  return value;
}
async function tmdb(namespaceValue,tmdbId){
  var namespace=namespaceValue==="movie"?"movie":"tv",id=s(tmdbId),cacheKey=namespace+":"+id;
  if(!/^\d+$/.test(id))return{state:"unavailable",metadata:null};
  if(Object.prototype.hasOwnProperty.call(mediaCache,cacheKey))return await mediaCache[cacheKey];
  var pending=(async function(){
    var probe=await apiJson("https://api.themoviedb.org/3/"+namespace+"/"+encodeURIComponent(id)+"?append_to_response=keywords,alternative_titles,external_ids&language=fr-FR");
    if(!probe||probe.state!=="ok")return{state:probe&&probe.state||"unavailable",metadata:null};
    var value=probe.value;
    if(Number(value.id||0)<=0)return{state:"unavailable",metadata:null};
    value.__nuvioTmdbNamespace=namespace;
    value.__nuvioTmdbId=id;
    return{state:"ok",metadata:value};
  })();
  mediaCache[cacheKey]=pending;
  var value=await pending;
  mediaCache[cacheKey]=value;
  return value;
}
function fallbackType(input,semantic){
  var raw=s(input||"movie").toLowerCase(),transport=alias(input);
  if(raw==="anime")return"anime";
  if(transport==="tv"&&semantic.indexOf("tv")<0&&semantic.indexOf("anime")>=0)return"anime";
  if(raw==="movie"&&semantic.indexOf("movie")<0&&semantic.indexOf("anime")>=0)return"anime";
  return transport;
}
async function canonicalResolution(id,input,metadata,season,episode,semantic){
  var candidates=namespaceCandidates(input,season,episode,semantic),raw=s(input||"movie").toLowerCase();
  var rawId=s(id),tmdbId=rawId.replace(/^tmdb:/i,""),imdbId="",seedMetadata=null;
  var imdbMatch=/^(?:imdb:)?(tt\d+)$/i.exec(rawId);
  if(imdbMatch){
    imdbId=imdbMatch[1].toLowerCase();
    var found=await findTmdb(imdbId,candidates);
    if(found&&found.state==="ok"){
      tmdbId=found.tmdbId;
      candidates=[found.namespace];
      seedMetadata=found.metadata||null;
    }else if(found&&found.state==="unavailable"){
      var degradedType=fallbackType(input,semantic),degradedNamespace=namespaceOf(input);
      return{type:degradedType,namespace:degradedNamespace,tmdbId:"",imdbId:imdbId,metadata:null,authoritative:false,degraded:true};
    }else return null;
  }
  if(hasTmdbMetadata(metadata)){
    var declared=s(metadata&&metadata.__nuvioTmdbNamespace).toLowerCase();
    var namespace=declared==="movie"?"movie":declared==="tv"?"tv":candidates[0];
    var declaredId=s(metadata&&metadata.__nuvioTmdbId||metadata&&metadata.id);
    if(/^\d+$/.test(declaredId))tmdbId=declaredId;
    var type=animeMeta(metadata)?"anime":namespace;
    if(raw==="anime"&&type!=="anime")return null;
    return{type:type,namespace:namespace,tmdbId:/^\d+$/.test(tmdbId)?tmdbId:"",imdbId:imdbId,metadata:metadata,authoritative:true,degraded:false};
  }
  var unavailable=false;
  for(var i=0;i<candidates.length;i++){
    var namespace=candidates[i],probe=await tmdb(namespace,tmdbId);
    if(!probe||probe.state==="unavailable"){unavailable=true;continue}
    if(probe.state==="not_found")continue;
    var m=probe.metadata,type=animeMeta(m)?"anime":namespace;
    if(raw==="anime"&&type!=="anime")continue;
    return{type:type,namespace:namespace,tmdbId:tmdbId,imdbId:imdbId,metadata:m,authoritative:true,degraded:false};
  }
  if(unavailable&&seedMetadata){
    var seedNamespace=candidates[0]||namespaceOf(input),seedType=animeMeta(seedMetadata)?"anime":seedNamespace;
    if(raw==="anime"&&seedType!=="anime")return null;
    seedMetadata.__nuvioTmdbNamespace=seedNamespace;
    seedMetadata.__nuvioTmdbId=tmdbId;
    return{type:seedType,namespace:seedNamespace,tmdbId:tmdbId,imdbId:imdbId,metadata:seedMetadata,authoritative:true,degraded:true};
  }
  if(unavailable){
    var fallback=fallbackType(input,semantic),fallbackNamespace=namespaceOf(input);
    return{type:fallback,namespace:fallbackNamespace,tmdbId:/^\d+$/.test(tmdbId)?tmdbId:"",imdbId:imdbId,metadata:null,authoritative:false,degraded:true};
  }
  return null;
}
function objectRequest(a){return a&&typeof a==="object"&&!Array.isArray(a)}
async function resolve(a){
  var first=a[0],obj=objectRequest(first),q=obj?Object.assign({},first):null;
  var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a[1]||"movie");
  var transport=alias(input),namespace=namespaceOf(input),raw=s(input).toLowerCase();
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  // TMDB identity/type resolution is the first provider gate for every request.
  // Provider capability filtering happens only after canonical movie|tv|anime
  // classification so transport aliases can never suppress a valid anime match.
  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);
  if(!metadata){try{var existingContext=g&&g.__nuvioMediaContext;if(existingContext&&existingContext.tmdbMetadata)metadata=existingContext.tmdbMetadata}catch(_){}}
  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first);
  var season=obj?q.season:a[2],episode=obj?q.episode:a[3];
  var resolved=await canonicalResolution(id,input,metadata,season,episode,semantic);
  if(!resolved)return null;
  var type=resolved.type;namespace=resolved.namespace;
  if(semantic.length&&semantic.indexOf(type)<0)return null;
  var resolvedTmdbId=s(resolved.tmdbId||(/^\d+$/.test(id)?id:""));
  var resolvedImdbId=s(resolved.imdbId||obj&&(q.imdbId||q.imdb_id)||(/^tt\d+$/i.test(id)?id:"")).toLowerCase();
  var context={
    tmdbId:resolvedTmdbId,
    imdbId:resolvedImdbId,
    tmdbNamespace:namespace,
    tmdbIdentity:namespace+":"+(resolvedTmdbId||id),
    tmdbMetadata:resolved.metadata||null,
    canonicalMediaType:type,
    tmdbResolutionDegraded:resolved.degraded===true,
    nuvioInputMediaType:input
  };
  if(obj){
    q.nuvioInputMediaType=input;
    if(resolvedTmdbId)q.tmdbId=resolvedTmdbId;
    if(resolvedImdbId)q.imdbId=resolvedImdbId;
    q.tmdbNamespace=namespace;
    q.tmdbIdentity=namespace+":"+(resolvedTmdbId||id);
    q.tmdbMetadata=resolved.metadata||q.tmdbMetadata||q.tmdb_metadata||null;
    q.canonicalMediaType=type;
    q.mediaType=type;q.type=type;
    if(type==="anime")q.category="anime";else if(!q.category||["series","show","other"].indexOf(s(q.category).toLowerCase())>=0)q.category=type;
    var out=[q];for(var i=1;i<a.length;i++)out.push(a[i]);out.__nuvioContext=context;return out;
  }
  var out=Array.prototype.slice.call(a);if(resolvedTmdbId)out[0]=resolvedTmdbId;out[1]=type;out.__nuvioContext=context;return out;
}
function providerTimeoutError(){var e=new Error("nuvio_provider_timeout");e.name="TimeoutError";e.code="NUVIO_PROVIDER_TIMEOUT";e.__nuvioProviderTimeout=true;return e}
function deadlineValue(){try{var n=Number(g&&g.__nuvioProviderDeadlineMs);return Number.isFinite(n)&&n>0?n:0}catch(_){return 0}}
function deadlineExpired(){var n=deadlineValue();return n>0&&Date.now()>=n}
function budgetedFetch(original){
  if(typeof original!=="function")return original;
  if(original.__nuvioProviderExecutionBudgetV1)return original;
  var wrapped=async function(){
    if(deadlineExpired())throw providerTimeoutError();
    var args=Array.prototype.slice.call(arguments),deadline=deadlineValue(),remaining=deadline>0?Math.max(1,deadline-Date.now()):0;
    if(remaining>0&&args.length>=1){
      var init=args[1]&&typeof args[1]==="object"?Object.assign({},args[1]):{};
      if(!init.signal){try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)init.signal=AbortSignal.timeout(remaining)}catch(_){}}
      args[1]=init;
    }
    var value=await original.apply(this,args);
    if(deadlineExpired())throw providerTimeoutError();
    return value;
  };
  try{Object.defineProperty(wrapped,"__nuvioProviderExecutionBudgetV1",{value:true})}catch(_){wrapped.__nuvioProviderExecutionBudgetV1=true}
  return wrapped;
}
function install(o,k){
  if(!o||typeof o[k]!=="function"||o[k].__nuvioMediaTypeResolutionV1)return false;
  var native=o[k];
  var wrap=async function(){
    var had=false,previous,hadDeadline=false,previousDeadline,hadFetch=false,previousFetch,budgetFetchInstalled=false;
    try{
      had=!!(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"));
      previous=g&&g.__nuvioMediaContext;
      hadDeadline=!!(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioProviderDeadlineMs"));
      previousDeadline=g&&g.__nuvioProviderDeadlineMs;
      hadFetch=!!(g&&Object.prototype.hasOwnProperty.call(g,"fetch"));
      previousFetch=g&&g.fetch;
    }catch(_){}
    try{
      if(g){
        var existing=Number(previousDeadline);
        if(!(Number.isFinite(existing)&&existing>Date.now()))g.__nuvioProviderDeadlineMs=Date.now()+c.providerTimeoutMs;
        if(typeof previousFetch==="function"){g.fetch=budgetedFetch(previousFetch);budgetFetchInstalled=g.fetch!==previousFetch;}
      }
      var a=await resolve(arguments);
      if(!a||deadlineExpired())return [];
      if(g)g.__nuvioMediaContext=a.__nuvioContext||null;
      var value=await native.apply(this,a);
      if(deadlineExpired())return [];
      return value;
    }catch(error){
      if(error&&error.__nuvioProviderTimeout)return [];
      throw error;
    }finally{
      try{
        if(g){
          if(had)g.__nuvioMediaContext=previous;else delete g.__nuvioMediaContext;
          if(budgetFetchInstalled){if(hadFetch)g.fetch=previousFetch;else delete g.fetch}
          if(hadDeadline)g.__nuvioProviderDeadlineMs=previousDeadline;else delete g.__nuvioProviderDeadlineMs;
        }
      }catch(_){}
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
