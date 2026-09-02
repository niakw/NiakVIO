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
import sys
from pathlib import Path
from typing import Any

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from provider_patch_blocks import has_managed_fix, replace_managed_fix

MARKER = "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1"
MANAGED_FIX_ID = "CORE.MEDIA_TYPE_RESOLUTION.V1"
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
        "providerTimeoutMs": max(5_000, min(int(cfg.get("provider_timeout_ms", 30_000)), 120_000)),
        "tvProviderTimeoutMs": max(5_000, min(int(cfg.get("tv_provider_timeout_ms", 25_000)), 30_000)),
        "semanticTypes": semantic_types,
        "requestTypeAliases": {
            str(key).strip().lower(): str(value).strip().lower()
            for key, value in (cfg.get("request_type_aliases") or {}).items()
            if str(key).strip() and str(value).strip()
        },
        "revision": "tmdb-data-contract-launch-gate-v25-client-budget-aligned",
        **_runtime_key_payload(),
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    # Existing managed ownership is updated in place. Legacy stripping is only
    # a one-time migration for pre-START/END bundles.
    if not has_managed_fix(text, MANAGED_FIX_ID):
        text = _strip_existing(text)

    js = r'''
/* MARKER_PLACEHOLDER */
/* NUVIO_GLOBAL_PROVIDER_EXECUTION_BUDGET_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function normalizeKey(v){var x=s(v);if(x.length===33&&x.charCodeAt(0)===92&&/^[0-9a-fA-F]{32}$/.test(x.slice(1)))x=x.slice(1);return /^[0-9a-fA-F]{32}$/.test(x)?x:""}
function alias(v){var x=s(v||"movie").toLowerCase();if(x==="series"||x==="show"||x==="other")return"tv";if(x==="anime")return"anime";if(x==="movie")return"movie";return"tv"}
function namespaceOf(v){var x=alias(v);return x==="movie"?"movie":"tv"}
function providerTransport(canonical,namespace){
  var map=c.requestTypeAliases&&typeof c.requestTypeAliases==="object"?c.requestTypeAliases:{};
  var mapped=s(map[canonical]).toLowerCase();
  if(mapped==="tmdb_namespace")return namespace==="movie"?"movie":"tv";
  if(mapped)return alias(mapped);
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  if(canonical==="anime"){
    var ns=namespace==="movie"?"movie":"tv";
    if(semantic.indexOf(ns)>=0)return ns;
    return"anime";
  }
  return canonical==="movie"?"movie":"tv";
}
function namespaceCandidates(v,season,episode){
  // Client media type is only a lookup hint. Never let it remove the alternate
  // TMDB namespace before canonical identity has been established.
  if(season!=null||episode!=null)return["tv","movie"];
  var hint=alias(v);
  if(hint==="movie")return["movie","tv"];
  return["tv","movie"];
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
  if(value&&value.state==="unavailable")delete mediaCache[cacheKey];else mediaCache[cacheKey]=value;
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
  if(value&&value.state==="unavailable")delete mediaCache[cacheKey];else mediaCache[cacheKey]=value;
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
  var candidates=namespaceCandidates(input,season,episode);
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
    return{type:type,namespace:namespace,tmdbId:/^\d+$/.test(tmdbId)?tmdbId:"",imdbId:imdbId,metadata:metadata,authoritative:true,degraded:false};
  }
  var unavailable=false;
  for(var i=0;i<candidates.length;i++){
    var namespace=candidates[i],probe=await tmdb(namespace,tmdbId);
    if(!probe||probe.state==="unavailable"){unavailable=true;continue}
    if(probe.state==="not_found")continue;
    var m=probe.metadata,type=animeMeta(m)?"anime":namespace;
    return{type:type,namespace:namespace,tmdbId:tmdbId,imdbId:imdbId,metadata:m,authoritative:true,degraded:false};
  }
  if(unavailable&&seedMetadata){
    var seedNamespace=candidates[0]||namespaceOf(input),seedType=animeMeta(seedMetadata)?"anime":seedNamespace;
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
function provisional(a){
  var first=a[0],obj=objectRequest(first),q=obj?Object.assign({},first):null;
  var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a[1]||"movie");
  var raw=s(input).toLowerCase(),namespace=namespaceOf(input);
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  var type=raw==="anime"?"anime":namespace;
  // Native Nuvio bridges may expose only a non-abortable host fetch. For a
  // numeric TMDB id, let a semantic-anime provider run provisionally even when
  // the client transports the work as tv/movie; authoritative TMDB verification
  // still happens before any positive output can escape.
  if(semantic.length&&semantic.indexOf(type)<0){
    if(semantic.indexOf(namespace)>=0)type=namespace;
    else if(semantic.indexOf("anime")>=0&&(namespace==="tv"||namespace==="movie"))type="anime";
    else if(semantic.length===1)type=semantic[0];
    else return null;
  }
  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first);
  var providerType=providerTransport(type,namespace);
  var resolvedTmdbId=/^\d+$/.test(id)?id:"";
  var resolvedImdbId=s(obj&&(q.imdbId||q.imdb_id)||(/^tt\d+$/i.test(id)?id:"")).toLowerCase();
  var context={
    tmdbId:resolvedTmdbId,
    imdbId:resolvedImdbId,
    tmdbNamespace:namespace,
    tmdbIdentity:namespace+":"+(resolvedTmdbId||id),
    tmdbMetadata:null,
    canonicalMediaType:type,
    tmdbResolutionDegraded:true,
    tmdbVerificationDeferred:true,
    nuvioInputMediaType:input,
    providerMediaType:providerType
  };
  if(obj){
    q.nuvioInputMediaType=input;
    if(resolvedTmdbId)q.tmdbId=resolvedTmdbId;
    if(resolvedImdbId)q.imdbId=resolvedImdbId;
    q.tmdbNamespace=namespace;
    q.tmdbIdentity=namespace+":"+(resolvedTmdbId||id);
    q.canonicalMediaType=type;
    q.providerMediaType=providerType;
    q.mediaType=providerType;q.type=providerType;
    if(type==="anime")q.category="anime";else if(!q.category||["series","show","other"].indexOf(s(q.category).toLowerCase())>=0)q.category=type;
    var out=[q];for(var i=1;i<a.length;i++)out.push(a[i]);out.__nuvioContext=context;return out;
  }
  var out=Array.prototype.slice.call(a);out[1]=providerType;out.__nuvioContext=context;return out;
}
function hasProviderOutput(value){
  if(Array.isArray(value))return value.length>0;
  if(!value||typeof value!=="object")return false;
  for(var i=0;i<3;i++){
    var key=["streams","results","data"][i];
    if(Array.isArray(value[key]))return value[key].length>0;
  }
  var url=value.url;
  if(typeof url==="string"&&s(url))return true;
  if(url&&typeof url==="object"&&typeof url.url==="string"&&s(url.url))return true;
  return false;
}
function invocationEvent(a){
  var first=a[0],obj=objectRequest(first),settings=obj?first:(a[4]&&typeof a[4]==="object"?a[4]:null),event="";
  try{event=s(settings&&(settings.providerEvent||settings.event)||"")}catch(_){}
  try{if(!event&&g)event=s(g.__nuvioProviderEvent||g.__nuvioEvent||"")}catch(_){}
  event=event.toLowerCase();
  return event||"launch";
}
function providerNeedsTmdbBeforeStreams(container){
  try{
    var model=container&&container.__niakvioProviderBase;
    var contract=model&&model.identityInput;
    if(!contract||contract.requiresTmdbBeforeRun!==true)return false;
    var mode=s(contract.mode).toLowerCase();
    return mode==="catalog_search"||mode==="external_id";
  }catch(_){return false}
}
function hasResolvedTmdbMetadata(args){
  try{return !!(args&&args.__nuvioContext&&args.__nuvioContext.tmdbMetadata)}catch(_){return false}
}

async function resolve(a){
  var first=a[0],obj=objectRequest(first),q=obj?Object.assign({},first):null;
  var input=obj?s(q.mediaType||q.type||q.category||"movie"):s(a[1]||"movie");
  var namespace=namespaceOf(input);
  var semantic=rows(c.semanticTypes).map(function(x){return s(x).toLowerCase()});
  // TMDB identity/type resolution is the first provider gate for every request.
  // Provider capability filtering happens only after canonical movie|tv|anime
  // classification so transport aliases can never suppress a valid anime match.
  // Per-request isolation: canonical type/metadata must come only from the
  // current work request (plus TMDB), never from a previous getStreams call.
  var metadata=obj&&(q.tmdbMetadata||q.tmdb_metadata||q.metadata||q);
  var id=obj?s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id):s(first);
  var season=obj?q.season:a[2],episode=obj?q.episode:a[3];
  var resolved=await canonicalResolution(id,input,metadata,season,episode,semantic);
  if(!resolved)return null;
  var type=resolved.type;namespace=resolved.namespace;
  if(resolved.authoritative&&semantic.length&&semantic.indexOf(type)<0)return null;
  var providerType=providerTransport(type,namespace);
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
    nuvioInputMediaType:input,
    providerMediaType:providerType
  };
  if(obj){
    q.nuvioInputMediaType=input;
    if(resolvedTmdbId)q.tmdbId=resolvedTmdbId;
    if(resolvedImdbId)q.imdbId=resolvedImdbId;
    q.tmdbNamespace=namespace;
    q.tmdbIdentity=namespace+":"+(resolvedTmdbId||id);
    q.tmdbMetadata=resolved.metadata||q.tmdbMetadata||q.tmdb_metadata||null;
    q.canonicalMediaType=type;
    q.providerMediaType=providerType;
    q.mediaType=providerType;q.type=providerType;
    if(type==="anime")q.category="anime";else if(!q.category||["series","show","other"].indexOf(s(q.category).toLowerCase())>=0)q.category=type;
    var out=[q];for(var i=1;i<a.length;i++)out.push(a[i]);out.__nuvioContext=context;return out;
  }
  var out=Array.prototype.slice.call(a);if(resolvedTmdbId)out[0]=resolvedTmdbId;out[1]=providerType;out.__nuvioContext=context;return out;
}
var requestSerial=0;
function providerTimeoutError(){var e=new Error("nuvio_provider_timeout");e.name="TimeoutError";e.code="NUVIO_PROVIDER_TIMEOUT";e.__nuvioProviderTimeout=true;return e}
function deadlineExpired(deadline){var n=Number(deadline);return Number.isFinite(n)&&n>0&&Date.now()>=n}
function tvRuntime(){try{var ua=s(g&&g.navigator&&g.navigator.userAgent);return /NuvioTV|Android TV/i.test(ua)||(g&&g.__NUVIO_TV_RUNTIME__===true)}catch(_){return false}}
function providerBudgetMs(){return tvRuntime()?Number(c.tvProviderTimeoutMs||25000):Number(c.providerTimeoutMs||30000)}
function budgetedFetch(original,deadline){
  if(typeof original!=="function")return original;
  var base=original.__nuvioProviderExecutionBudgetBase||original;
  var wrapped=async function(){
    if(deadlineExpired(deadline))throw providerTimeoutError();
    var args=Array.prototype.slice.call(arguments),remaining=deadline>0?Math.max(1,deadline-Date.now()):0;
    if(remaining>0&&args.length>=1){
      var init=args[1]&&typeof args[1]==="object"?Object.assign({},args[1]):{};
      if(!init.signal){try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)init.signal=AbortSignal.timeout(remaining)}catch(_){}}
      args[1]=init;
    }
    if(remaining<=0)return await base.apply(this,args);
    var timer=null;
    var timeoutPromise=new Promise(function(_resolve,reject){
      if(typeof setTimeout!=="function")return;
      timer=setTimeout(function(){reject(providerTimeoutError())},remaining);
    });
    var value;
    try{
      value=typeof setTimeout==="function"
        ? await Promise.race([base.apply(this,args),timeoutPromise])
        : await base.apply(this,args);
    }finally{
      try{if(timer!=null&&typeof clearTimeout==="function")clearTimeout(timer)}catch(_){}
    }
    if(deadlineExpired(deadline))throw providerTimeoutError();
    return value;
  };
  try{
    Object.defineProperty(wrapped,"__nuvioProviderExecutionBudgetV1",{value:true});
    Object.defineProperty(wrapped,"__nuvioProviderExecutionBudgetBase",{value:base});
  }catch(_){
    wrapped.__nuvioProviderExecutionBudgetV1=true;
    wrapped.__nuvioProviderExecutionBudgetBase=base;
  }
  return wrapped;
}
function install(o,k){
  if(!o||typeof o[k]!=="function"||o[k].__nuvioMediaTypeResolutionV1)return false;
  var native=o[k];
  var wrap=async function(){
    var originalArgs=Array.prototype.slice.call(arguments);
    var providerEvent=invocationEvent(originalArgs);
    // Absolute first gate: non-launch invocations do not touch provider runtime state.
    if(providerEvent!=="launch")return [];

    var requestToken=0,requestDeadline=0,hadFetch=false,previousFetch,fetchBase,budgetFetchInstalled=false;
    try{
      // Hard-reset media context at every provider invocation. This prevents
      // tv/anime/movie (including anime movies transported as movie) from
      // becoming sticky for the lifetime of a native QuickJS instance.
      if(g&&Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"))delete g.__nuvioMediaContext;
      if(g){
        var priorSerial=Number(g.__nuvioProviderRequestSerial||requestSerial);
        requestToken=(Number.isFinite(priorSerial)&&priorSerial>=0?priorSerial:requestSerial)+1;
        requestSerial=requestToken;
        g.__nuvioProviderRequestSerial=requestToken;
        g.__nuvioProviderRequestToken=requestToken;
      }
      hadFetch=!!(g&&Object.prototype.hasOwnProperty.call(g,"fetch"));
      previousFetch=g&&g.fetch;
      fetchBase=previousFetch&&previousFetch.__nuvioProviderExecutionBudgetBase||previousFetch;
    }catch(_){}
    try{
      requestDeadline=Date.now()+providerBudgetMs();
      if(g){
        g.__nuvioProviderDeadlineMs=requestDeadline;
        if(typeof fetchBase==="function"){g.fetch=budgetedFetch(fetchBase,requestDeadline);budgetFetchInstalled=g.fetch!==fetchBase;}
      }
      // Gate 2: build request-local provisional transport without TMDB by default.
      // A provider whose declared DATA contract requires a title-based catalogue
      // lookup is the only exception: resolve TMDB once before its first call.
      var a=provisional(originalArgs);
      if(!a||deadlineExpired(requestDeadline))return [];
      if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
      if(a.__nuvioContext)a.__nuvioContext.requestToken=requestToken;
      if(g)g.__nuvioMediaContext=a.__nuvioContext||null;

      var verified=null;
      var tmdbBeforeStreams=providerNeedsTmdbBeforeStreams(o);
      if(tmdbBeforeStreams){
        verified=await resolve(originalArgs);
        if(!verified||deadlineExpired(requestDeadline))return [];
        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
        if(!hasResolvedTmdbMetadata(verified))return [];
        if(verified.__nuvioContext)verified.__nuvioContext.requestToken=requestToken;
        if(g)g.__nuvioMediaContext=verified.__nuvioContext||null;
        a=verified;
      }

      var value=await native.apply(this,a);
      if(deadlineExpired(requestDeadline))return [];
      if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
      if(!hasProviderOutput(value))return [];

      // Gate 3: ordinary providers pay TMDB/type cost only after positive output.
      // Providers which required TMDB to execute their declared plan already ran
      // with verified context, so the same verified object is reused with no
      // second metadata call.
      if(!verified){
        verified=await resolve(originalArgs);
        if(!verified||deadlineExpired(requestDeadline))return [];
        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
      }
      var provisionalContext=a.__nuvioContext||{},verifiedContext=verified.__nuvioContext||{};
      var rerun=(
        s(provisionalContext.canonicalMediaType)!==s(verifiedContext.canonicalMediaType)
        || s(provisionalContext.providerMediaType)!==s(verifiedContext.providerMediaType)
        || s(provisionalContext.tmdbNamespace)!==s(verifiedContext.tmdbNamespace)
        || s(provisionalContext.tmdbId)!==s(verifiedContext.tmdbId)
        || s(provisionalContext.tmdbIdentity)!==s(verifiedContext.tmdbIdentity)
      );
      if(rerun){
        if(verified.__nuvioContext)verified.__nuvioContext.requestToken=requestToken;
        if(g)g.__nuvioMediaContext=verified.__nuvioContext||null;
        value=await native.apply(this,verified);
        if(deadlineExpired(requestDeadline))return [];
        if(g&&requestToken&&g.__nuvioProviderRequestToken!==requestToken)return [];
        if(!hasProviderOutput(value))return [];
      }
      return value;
    }catch(error){
      if(error&&error.__nuvioProviderTimeout)return [];
      throw error;
    }finally{
      try{
        if(g){
          // An older request must never clean state owned by a newer request.
          var ownsRequest=!requestToken||g.__nuvioProviderRequestToken===requestToken;
          if(ownsRequest){
            if(Object.prototype.hasOwnProperty.call(g,"__nuvioMediaContext"))delete g.__nuvioMediaContext;
            if(budgetFetchInstalled){if(hadFetch&&typeof fetchBase==="function")g.fetch=fetchBase;else if(!hadFetch)delete g.fetch}
            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderDeadlineMs"))delete g.__nuvioProviderDeadlineMs;
            if(Object.prototype.hasOwnProperty.call(g,"__nuvioProviderRequestToken"))delete g.__nuvioProviderRequestToken;
          }
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

    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data=payload,
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
