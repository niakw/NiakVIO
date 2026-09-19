#!/usr/bin/env python3
"""Movix clean-v3 direct API adapter.

Historical Movix JavaScript is knowledge-only. This Lego re-implements only
server-cache-backed Movix catalogue contracts that are non-blocking on a cold
cache: SwiftFlow then Wiflix. It never enters FStream's synchronous scrape path,
never performs TMDB metadata lookup and never falls back to discovery.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIX.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MOVIX_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function rows(v){return Array.isArray(v)?v:[]}
  function mediaNamespace(type){
    var value=s(type).toLowerCase();
    try{
      var ctx=g&&g.__nuvioMediaContext||{};
      if(ctx.tmdbNamespace==="movie"||ctx.tmdbNamespace==="tv")return ctx.tmdbNamespace;
    }catch(_e){}
    return value==="movie"?"movie":"tv";
  }
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null;
    var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||first).replace(/^tmdb:/i,"").split(":")[0];
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||args[1]||"movie").toLowerCase();
    return {
      tmdbId:id,
      namespace:mediaNamespace(type),
      season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,
      episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1
    };
  }
  function usable(v){return /^https?:\/\//i.test(s(v))}
  function requestBudget(){
    var max=Math.max(500,Number(c.requestTimeoutMs||6500)||6500);
    try{
      var deadline=Number(g&&g.__nuvioProviderDeadlineMs);
      if(Number.isFinite(deadline)&&deadline>0)max=Math.max(1,Math.min(max,deadline-Date.now()));
    }catch(_e){}
    return max;
  }
  async function timedFetch(url,init){
    var ms=requestBudget(),opts=Object.assign({},init||{}),timer=null;
    if(ms<=0)throw new Error("movix_timeout");
    try{
      if(!opts.signal&&typeof AbortSignal!=="undefined"&&AbortSignal.timeout)opts.signal=AbortSignal.timeout(ms);
    }catch(_e){}
    if(typeof setTimeout!=="function")return await g.fetch(url,opts);
    var timeout=new Promise(function(_resolve,reject){
      timer=setTimeout(function(){var e=new Error("movix_timeout");e.name="TimeoutError";reject(e)},ms);
    });
    try{return await Promise.race([g.fetch(url,opts),timeout])}
    finally{try{if(timer!=null&&typeof clearTimeout==="function")clearTimeout(timer)}catch(_e){}}
  }
  function addRows(value,label,out,seen){
    rows(value).forEach(function(row){
      var url=s(row&&typeof row==="object"?(row.url||row.src||row.embedUrl||row.embed_url):row);
      if(!usable(url)||seen[url])return;
      seen[url]=1;
      out.push({
        name:"Movix"+(label?" ["+label+"]":""),
        title:"Movix"+(label?" ["+label+"]":""),
        url:url,
        provider:"movix",
        referer:c.referer
      });
    });
  }
  function collectGroups(container,out,seen){
    if(!container||typeof container!=="object")return;
    for(var i=0;i<c.preferredGroups.length;i++){
      var key=c.preferredGroups[i];
      addRows(container[key],key,out,seen);
    }
    if(out.length)return;
    Object.keys(container).forEach(function(key){addRows(container[key],key,out,seen)});
  }
  function selectedEpisode(data,q){
    var root=data&&data.episodes;
    if(!root||typeof root!=="object")return null;
    var e=String(q.episode),season=String(q.season);
    return root[e]||root[Number(e)]||
      (root[season]&&root[season][e])||
      (root[season]&&root[season][Number(e)])||null;
  }
  function players(data,q){
    data=data&&typeof data==="object"&&(data.data&&typeof data.data==="object"?data.data:data)||{};
    var out=[],seen=Object.create(null);
    if(q.namespace==="tv"){
      var selected=selectedEpisode(data,q);
      if(!selected)return [];
      if(selected.languages&&typeof selected.languages==="object"){
        for(var i=0;i<c.preferredGroups.length;i++){
          var lang=c.preferredGroups[i];
          addRows(selected.languages[lang],lang,out,seen);
        }
        if(!out.length)Object.keys(selected.languages).forEach(function(lang){addRows(selected.languages[lang],lang,out,seen)});
      }
      for(var j=0;j<c.preferredGroups.length;j++){
        var key=c.preferredGroups[j];
        addRows(selected[key]||selected[key.toLowerCase()],key,out,seen);
      }
      addRows(selected.players,"Players",out,seen);
      addRows(selected.links,"Links",out,seen);
      if(Array.isArray(selected))addRows(selected,"Episode",out,seen);
      if(out.length)return out.slice(0,c.maxPlayers);
    }
    collectGroups(data.players||data.links,out,seen);
    return out.slice(0,c.maxPlayers);
  }
  function routePaths(q){
    var id=encodeURIComponent(q.tmdbId),season=encodeURIComponent(String(q.season)),episode=encodeURIComponent(String(q.episode));
    if(q.namespace==="movie")return [
      "/api/swiftflow/movie/"+id,
      "/api/wiflix/movie/"+id
    ];
    return [
      "/api/swiftflow/tv/"+id+"/season/"+season+"?episode="+episode,
      "/api/wiflix/tv/"+id+"/"+season
    ];
  }
  async function movixStreams(args){
    var q=requestArgs(args);
    if(!/^\d+$/.test(q.tmdbId))return [];
    var paths=routePaths(q);
    for(var i=0;i<paths.length;i++){
      try{
        var response=await timedFetch(c.apiBase+paths[i],{
          headers:{"Accept":"application/json,text/plain,*/*","Referer":c.referer},
          redirect:"follow"
        });
        if(!response||!response.ok)continue;
        var data=await response.json();
        if(!data||data.success===false||data.pending===true)continue;
        var out=players(data,q);
        if(out.length)return out;
      }catch(_e){}
    }
    return [];
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioMovixRuntimeV1)return false;
    var wrapped=async function(){try{return await movixStreams(arguments)}catch(_e){return []}};
    wrapped.__niakvioMovixRuntimeV1=true;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    payload={
        "apiBase":str(cfg.get("api_base") or "https://api.movix.fun").rstrip("/"),
        "referer":str(cfg.get("referer") or "https://movix.fun/"),
        "preferredGroups":list(cfg.get("preferred_groups") or ["VFF","VFQ","VF","Default","VOSTFR"]),
        "maxPlayers":max(1,min(int(cfg.get("max_players") or 10),20)),
        "requestTimeoutMs":max(800,min(int(cfg.get("request_timeout_ms") or 6500),12000)),
    }
    wrapper=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime":payload,
            "identity":"tmdb-id-direct-no-metadata",
            "legacyExecutableSeed":False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
