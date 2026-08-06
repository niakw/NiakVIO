#!/usr/bin/env python3
"""Append a Nuvio Desktop runtime compatibility wrapper to provider bundles.

The desktop QuickJS runtime currently does not expose browser timer globals,
while several provider recovery layers and the stream sanitizer use setTimeout
for cancellation.  The wrapper installs safe no-op timer fallbacks before any
getStreams call and can normalize missing TV episode arguments.  It can also
filter/cap oversized series results for providers that otherwise enumerate an
entire show when Nuvio Desktop omits season/episode.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER_PREFIX = "NUVIO_DESKTOP_RUNTIME_COMPAT_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    options = dict(options or {})
    config = {
        "normalizeMissingEpisodes": bool(options.get("normalize_missing_episodes", False)),
        "fallbackSeason": max(1, int(options.get("fallback_season", 1))),
        "fallbackEpisode": max(1, int(options.get("fallback_episode", 1))),
        "filterEpisodeLabels": bool(options.get("filter_episode_labels", False)),
        "maxSeriesStreams": max(0, min(int(options.get("max_series_streams", 0)), 100)),
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

  // QuickJS Desktop has no browser timers.  Provider HTTP calls already have
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
