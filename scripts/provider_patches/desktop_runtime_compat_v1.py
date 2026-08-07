#!/usr/bin/env python3
"""Append a Nuvio Desktop runtime compatibility wrapper to provider bundles.

The desktop QuickJS runtime currently does not expose browser timer globals,
while several provider recovery layers and the stream sanitizer use setTimeout
for cancellation. The wrapper installs safe no-op timer fallbacks before any
getStreams call, normalizes missing TV episode arguments, can filter/cap
oversized series results, and supports bounded evidence-backed domain failover
without changing the public manifest URL.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER_PREFIX = "NUVIO_DESKTOP_RUNTIME_COMPAT_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    options = dict(options or {})
    raw_replacements = options.get("domain_replacements") or {}
    domain_replacements = {
        str(source).strip().casefold(): str(target).strip().casefold()
        for source, target in dict(raw_replacements).items()
        if str(source).strip() and str(target).strip()
    }

    raw_failover = dict(options.get("domain_failover") or {})
    failover_prefixes = []
    for value in raw_failover.get("host_prefixes") or []:
        item = str(value).strip().casefold().strip(".")
        if item and item not in failover_prefixes:
            failover_prefixes.append(item)
    failover_suffixes = []
    for value in raw_failover.get("suffixes") or []:
        item = str(value).strip().casefold().strip(".")
        if item and item not in failover_suffixes:
            failover_suffixes.append(item)
    domain_failover = (
        {"hostPrefixes": failover_prefixes, "suffixes": failover_suffixes}
        if failover_prefixes and failover_suffixes
        else {}
    )

    config = {
        "normalizeMissingEpisodes": bool(options.get("normalize_missing_episodes", False)),
        "fallbackSeason": max(1, int(options.get("fallback_season", 1))),
        "fallbackEpisode": max(1, int(options.get("fallback_episode", 1))),
        "filterEpisodeLabels": bool(options.get("filter_episode_labels", False)),
        "maxSeriesStreams": max(0, min(int(options.get("max_series_streams", 0)), 100)),
        "domainReplacements": domain_replacements,
        "domainFailover": domain_failover,
    }
    payload = json.dumps(config, separators=(",", ":"))
    marker = f"{MARKER_PREFIX}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"
    if marker in text:
        return text

    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,config){
  "use strict";
  if(!g)return;

  // Install one shared fetch bridge. It supports exact evidence-backed host
  // replacements and bounded suffix failover rules. Failover only applies to
  // explicitly configured host prefixes and remembers the last healthy suffix.
  if((config.domainReplacements||config.domainFailover)&&typeof g.fetch==="function"){
    var fetchKey="__nuvioDesktopFetchCompatV1",fetchState=g[fetchKey];
    if(!fetchState){
      fetchState={native:g.fetch.bind(g),rules:Object.create(null),failovers:Object.create(null)};
      g[fetchKey]=fetchState;

      function requestWithUrl(input,urlText){
        try{
          if(typeof Request!=="undefined"&&input instanceof Request)return new Request(urlText,input);
        }catch(_error){}
        return urlText;
      }
      function rewriteInitHost(init,oldHost,newHost){
        if(!init||typeof init!=="object"||!oldHost||!newHost||oldHost===newHost)return init;
        var copy={},key;
        Object.keys(init).forEach(function(name){copy[name]=init[name];});
        var headers=init.headers;
        if(headers&&typeof headers==="object"&&!Array.isArray(headers)){
          var nextHeaders={};
          Object.keys(headers).forEach(function(name){
            var value=headers[name];
            nextHeaders[name]=typeof value==="string"?value.split(oldHost).join(newHost):value;
          });
          copy.headers=nextHeaders;
        }
        return copy;
      }
      function failoverMatch(hostname){
        var keys=Object.keys(fetchState.failovers);
        for(var i=0;i<keys.length;i++){
          var prefix=keys[i];
          if(hostname.indexOf(prefix+".")===0)return prefix;
        }
        return null;
      }
      function orderedSuffixes(rule){
        var output=[];
        if(rule.selected)output.push(rule.selected);
        rule.suffixes.forEach(function(suffix){if(output.indexOf(suffix)===-1)output.push(suffix);});
        return output;
      }

      g.fetch=async function(input,init){
        var raw;
        try{raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);}catch(_error){raw=String(input);}
        var url;
        try{url=new URL(raw);}catch(_error){return fetchState.native(input,init);}

        var replacement=fetchState.rules[String(url.hostname).toLowerCase()];
        if(replacement)url.hostname=replacement;

        var prefix=failoverMatch(String(url.hostname).toLowerCase());
        if(!prefix){
          return fetchState.native(requestWithUrl(input,url.toString()),init);
        }

        var rule=fetchState.failovers[prefix],suffixes=orderedSuffixes(rule);
        var lastResponse=null,lastError=null,originalHost=String(url.hostname);
        for(var i=0;i<suffixes.length;i++){
          var suffix=suffixes[i],candidate;
          try{
            candidate=new URL(url.toString());
            candidate.hostname=prefix+"."+suffix;
            var response=await fetchState.native(
              requestWithUrl(input,candidate.toString()),
              rewriteInitHost(init,originalHost,String(candidate.hostname))
            );
            lastResponse=response;
            if(response&&response.ok){rule.selected=suffix;return response;}
          }catch(error){
            lastError=error;
          }
        }
        if(lastResponse)return lastResponse;
        throw lastError||new Error("Nuvio Desktop domain failover exhausted for "+prefix);
      };
    }

    Object.keys(config.domainReplacements||{}).forEach(function(source){
      fetchState.rules[String(source).toLowerCase()]=String(config.domainReplacements[source]).toLowerCase();
    });
    if(config.domainFailover&&Array.isArray(config.domainFailover.hostPrefixes)&&Array.isArray(config.domainFailover.suffixes)){
      config.domainFailover.hostPrefixes.forEach(function(prefix){
        prefix=String(prefix||"").toLowerCase();
        if(!prefix)return;
        var rule=fetchState.failovers[prefix]||{suffixes:[],selected:null};
        config.domainFailover.suffixes.forEach(function(suffix){
          suffix=String(suffix||"").toLowerCase();
          if(suffix&&rule.suffixes.indexOf(suffix)===-1)rule.suffixes.push(suffix);
        });
        fetchState.failovers[prefix]=rule;
      });
    }
  }

  // QuickJS Desktop has no browser timers. Provider HTTP calls already have
  // native client timeouts, so a non-firing fallback is safer than aborting
  // every request immediately or throwing ReferenceError.
  if(typeof g.setTimeout!=="function"){
    g.setTimeout=function(callback,delay){
      if((Number(delay)||0)<=0&&typeof callback==="function"&&typeof Promise!=="undefined"){
        Promise.resolve().then(callback).catch(function(){});
      }
      return 0;
    };
  }
  if(typeof g.clearTimeout!=="function")g.clearTimeout=function(){};
  if(typeof g.setInterval!=="function")g.setInterval=function(){return 0;};
  if(typeof g.clearInterval!=="function")g.clearInterval=function(){};

  function positive(value,fallback){
    var number=Number(value);
    return Number.isFinite(number)&&number>0?Math.floor(number):fallback;
  }
  function isSeries(type){
    var value=String(type||"").toLowerCase();
    return value==="tv"||value==="series"||value==="show";
  }
  function textOf(stream){
    if(!stream||typeof stream!=="object")return "";
    return [stream.name,stream.title,stream.description,stream.size,stream.url]
      .filter(function(value){return value!=null})
      .join(" ");
  }
  function episodeMatch(stream,season,episode){
    var text=textOf(stream);
    if(!text)return false;
    var s=String(season),e=String(episode);
    var patterns=[
      new RegExp("S0*"+s+"\\s*E0*"+e,"i"),
      new RegExp("\\b0*"+s+"x0*"+e+"\\b","i"),
      new RegExp("saison\\s*0*"+s+"[^0-9]{0,16}(?:episode|ep)\\s*0*"+e,"i"),
      new RegExp("season\\s*0*"+s+"[^0-9]{0,16}(?:episode|ep)\\s*0*"+e,"i")
    ];
    for(var i=0;i<patterns.length;i++)if(patterns[i].test(text))return true;
    return false;
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioDesktopCompat)return false;
    var original=container[key];
    var wrapped=async function(){
      var args=Array.prototype.slice.call(arguments);
      var series=isSeries(args[1]);
      if(series&&config.normalizeMissingEpisodes){
        args[2]=positive(args[2],config.fallbackSeason);
        args[3]=positive(args[3],config.fallbackEpisode);
      }
      var result=await original.apply(this,args);
      if(!series||!Array.isArray(result))return result;
      var output=result;
      if(config.filterEpisodeLabels){
        var exact=result.filter(function(stream){return episodeMatch(stream,args[2],args[3])});
        if(exact.length)output=exact;
      }
      if(config.maxSeriesStreams>0&&output.length>config.maxSeriesStreams){
        output=output.slice(0,config.maxSeriesStreams);
      }
      return output;
    };
    wrapped.__nuvioDesktopCompat=true;
    wrapped.__nuvioOriginal=original;
    container[key]=wrapped;
    return true;
  }

  var installed=false;
  try{
    if(typeof module!=="undefined"&&module.exports){
      installed=install(module.exports,"getStreams")||installed;
    }
  }catch(_error){}
  try{
    if(typeof g.getStreams==="function"){
      if(installed&&typeof module!=="undefined"&&module.exports&&module.exports.getStreams){
        g.getStreams=module.exports.getStreams;
      }else{
        install(g,"getStreams");
      }
    }
  }catch(_error){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER", payload).replace("MARKER_PLACEHOLDER", marker)
    return text.rstrip() + "\n" + wrapper.lstrip()
