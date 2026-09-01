#!/usr/bin/env python3
"""Append Nuvio Desktop/Mobile runtime compatibility helpers to provider bundles.

This patch is deliberately domain-agnostic. Provider URLs are authoritative and
must be used exactly as emitted by the provider; runtime compatibility may fill
missing timers or normalize request/episode semantics, but must never invent
alternate provider domains or static TLD failovers.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from provider_patch_blocks import replace_managed_fix, strip_legacy_iife, strip_managed_fix

MARKER_PREFIX = "NUVIO_DESKTOP_RUNTIME_COMPAT_V1"
MANAGED_FIX_ID = "CORE.DESKTOP_RUNTIME_COMPAT.V1"
PATCH_REVISION = 5


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    options = dict(options or {})
    forbidden = {"domain_replacements", "domain_failover"} & set(options)
    if forbidden:
        raise ValueError(
            "Desktop runtime compatibility is domain-agnostic; remove options: "
            + ", ".join(sorted(forbidden))
        )

    config = {
        "patchRevision": PATCH_REVISION,
        "normalizeMissingEpisodes": bool(options.get("normalize_missing_episodes", False)),
        "fallbackSeason": max(1, int(options.get("fallback_season", 1))),
        "fallbackEpisode": max(1, int(options.get("fallback_episode", 1))),
        "filterEpisodeLabels": bool(options.get("filter_episode_labels", False)),
        "maxSeriesStreams": max(0, min(int(options.get("max_series_streams", 0)), 100)),
    }
    payload = json.dumps(config, separators=(",", ":"))
    marker = f"{MARKER_PREFIX}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"

    text = strip_managed_fix(text, MANAGED_FIX_ID)
    legacy = re.findall(r"/\\* " + re.escape(MARKER_PREFIX) + r":[0-9a-f]{12} \\*/", text)
    if len(legacy) > 1:
        raise ValueError("duplicate legacy desktop runtime compatibility blocks")
    if legacy:
        text = strip_legacy_iife(text, legacy[0])

    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,config){
  "use strict";
  if(!g)return;

  // Runtime portability only. Never rewrite provider URLs/domains here.
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
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper.lstrip(),
        data=config,
    )
