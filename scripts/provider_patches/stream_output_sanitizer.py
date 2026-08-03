#!/usr/bin/env python3
"""Append a bounded, standards-based stream output validator.

The wrapper does not attempt to hide automation or bypass access controls. It
only rejects known wrong hosts, duplicate URLs, network failures, HTML error
pages returned as media, and malformed HLS manifests before the player sees
those entries.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER_PREFIX = "NUVIO_STREAM_OUTPUT_SANITIZER_V2"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    options = dict(options or {})
    blocked_hosts = sorted({str(v).lower().strip().lstrip(".") for v in options.get("blocked_hosts", []) if str(v).strip()})
    probe_direct = bool(options.get("probe_direct_media", False))
    probe_all = bool(options.get("probe_all_urls", False))
    max_probes = max(0, min(int(options.get("max_probes", 6)), 20))
    timeout_ms = max(1000, min(int(options.get("probe_timeout_ms", 4500)), 12000))
    payload = json.dumps(
        {
            "blockedHosts": blocked_hosts,
            "probeDirectMedia": probe_direct,
            "probeAllUrls": probe_all,
            "maxProbes": max_probes,
            "timeoutMs": timeout_ms,
        },
        separators=(",", ":"),
    )
    marker = f"{MARKER_PREFIX}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"
    if marker in text:
        return text
    # The wrapper is always appended; replace older/config-different versions
    # rather than stacking multiple asynchronous validators.
    legacy_index = text.find("/* NUVIO_STREAM_OUTPUT_SANITIZER_")
    if legacy_index >= 0:
        text = text[:legacy_index].rstrip()
    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,config){
  "use strict";
  function hostOf(raw){try{return new URL(String(raw)).hostname.toLowerCase()}catch(_e){return ""}}
  function blocked(raw){
    var host=hostOf(raw);
    if(!host)return true;
    for(var i=0;i<config.blockedHosts.length;i++){
      var rule=config.blockedHosts[i];
      if(host===rule||host.endsWith("."+rule))return true;
    }
    return false;
  }
  function urlOf(stream){return stream&&typeof stream.url==="string"?stream.url.trim():""}
  function isDirect(stream,url){
    var hint=String((stream&&(stream.type||stream.format||stream.mimeType||stream.contentType))||"").toLowerCase();
    return /(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd)(?:[?#]|$)/i.test(url)||/(?:hls|mpegurl|dash|mp4|video\/)/.test(hint);
  }
  function headersFor(stream){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*;q=0.8","Range":"bytes=0-4095"};
    var source=stream&&stream.headers;
    if(source&&typeof source==="object"){
      try{Object.keys(source).forEach(function(key){if(source[key]!=null)output[key]=String(source[key])})}catch(_e){}
    }
    return output;
  }
  async function prefixBytes(response,controller){
    if(response.body&&typeof response.body.getReader==="function"){
      var reader=response.body.getReader();
      try{var chunk=await reader.read();return chunk&&chunk.value?chunk.value:new Uint8Array(0)}
      finally{try{await reader.cancel()}catch(_e){};try{controller.abort()}catch(_e){}}
    }
    var buffer=await response.arrayBuffer();
    try{controller.abort()}catch(_e){}
    return new Uint8Array(buffer.slice(0,4096));
  }
  function ascii(bytes){
    var end=Math.min(bytes.length,4096),out="";
    for(var i=0;i<end;i++)out+=String.fromCharCode(bytes[i]);
    return out;
  }
  async function probe(stream,url){
    if(typeof g.fetch!=="function")return true;
    var controller=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",headers:headersFor(stream),redirect:"follow",signal:controller.signal});
      if(!response||!response.ok||blocked(response.url||url))return false;
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      var bytes=await prefixBytes(response,controller),text=ascii(bytes),trimmed=text.replace(/^\uFEFF/,"").trimStart();
      if(/(?:\.m3u8)(?:[?#]|$)/i.test(url)||/(?:mpegurl|vnd\.apple)/.test(contentType))return trimmed.indexOf("#EXTM3U")===0;
      if(/(?:text\/html|application\/json|text\/plain)/.test(contentType)||/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(text))return false;
      if(/(?:\.mp4)(?:[?#]|$)/i.test(url)||/video\/mp4/.test(contentType))return /video\/mp4/.test(contentType)||(bytes.length>=8&&ascii(bytes.slice(4,8))==="ftyp");
      return bytes.length>0;
    }catch(_error){return false}
    finally{clearTimeout(timer);try{controller.abort()}catch(_e){}}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioSanitized)return false;
    var original=container[key];
    var wrapped=async function(){
      var result=await original.apply(this,arguments);
      if(!Array.isArray(result))return result;
      var seen=Object.create(null),candidates=[],probeCount=0;
      for(var i=0;i<result.length;i++){
        var stream=result[i],url=urlOf(stream);
        if(!url||blocked(url)||seen[url])continue;
        seen[url]=true;
        candidates.push({stream:stream,url:url,probe:(config.probeAllUrls||(config.probeDirectMedia&&isDirect(stream,url)))&&probeCount++<config.maxProbes});
      }
      var checked=await Promise.all(candidates.map(async function(item){
        if(!item.probe)return item.stream;
        return await probe(item.stream,item.url)?item.stream:null;
      }));
      return checked.filter(Boolean);
    };
    wrapped.__nuvioSanitized=true;
    wrapped.__nuvioOriginal=original;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){
    if(installed&&typeof module!=="undefined"&&module.exports&&module.exports.getStreams)g.getStreams=module.exports.getStreams;
    else install(g,"getStreams");
  }}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER", payload).replace("MARKER_PLACEHOLDER", marker)
    return text.rstrip() + "\n" + wrapper.lstrip()
