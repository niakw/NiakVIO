#!/usr/bin/env python3
"""Append a bounded, standards-based stream output validator.

The wrapper does not attempt to hide automation or bypass access controls. It
only rejects known wrong hosts, telemetry/assets, duplicate URLs, network
failures, HTML error pages returned as media, and malformed HLS manifests
before the player sees those entries.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER_PREFIX = "NUVIO_STREAM_OUTPUT_SANITIZER_V4"

DEFAULT_BLOCKED_HOSTS = {
    "googletagmanager.com",
    "google-analytics.com",
    "analytics.google.com",
    "static.cloudflareinsights.com",
    "cloudflareinsights.com",
    "connect.facebook.net",
    "doubleclick.net",
    "googlesyndication.com",
    "pagead2.googlesyndication.com",
    "api.themoviedb.org",
    "graphql.anilist.co",
    "kitsu.io",
    "arm.haglund.dev",
    "v3-cinemeta.strem.io",
    "npms.io",
    "lodash.com",
    "openjsf.org",
    "underscorejs.org",
}

DEFAULT_BLOCKED_PATHS = {
    "/gtag/js",
    "/analytics",
    "/collect",
    "/cdn-cgi/rum",
    "/beacon.min.js",
}


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    options = dict(options or {})
    blocked_hosts = sorted(
        DEFAULT_BLOCKED_HOSTS
        | {str(v).lower().strip().lstrip(".") for v in options.get("blocked_hosts", []) if str(v).strip()}
    )
    probe_direct = bool(options.get("probe_direct_media", False))
    probe_all = bool(options.get("probe_all_urls", False))
    max_probes = max(0, min(int(options.get("max_probes", 6)), 20))
    timeout_ms = max(1000, min(int(options.get("probe_timeout_ms", 4500)), 12000))
    min_vod_duration = max(0, min(int(options.get("min_vod_duration_seconds", 60)), 1800))
    blocked_paths = sorted(
        DEFAULT_BLOCKED_PATHS
        | {str(v).strip().lower() for v in options.get("blocked_path_patterns", []) if str(v).strip()}
    )
    payload = json.dumps(
        {
            "blockedHosts": blocked_hosts,
            "probeDirectMedia": probe_direct,
            "probeAllUrls": probe_all,
            "maxProbes": max_probes,
            "timeoutMs": timeout_ms,
            "minVodDurationSeconds": min_vod_duration,
            "blockedPathPatterns": blocked_paths,
        },
        separators=(",", ":"),
    )
    marker = f"{MARKER_PREFIX}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"
    if marker in text:
        return text
    legacy_index = text.find("/* NUVIO_STREAM_OUTPUT_SANITIZER_")
    if legacy_index >= 0:
        call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', legacy_index)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated stream output sanitizer wrapper")
        text = (text[:legacy_index] + text[end + 2 :]).rstrip()
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
    try{
      var parsed=new URL(String(raw)),path=parsed.pathname.toLowerCase();
      for(var j=0;j<config.blockedPathPatterns.length;j++){
        if(path.indexOf(config.blockedPathPatterns[j])>=0)return true;
      }
      if(/\.(?:js|mjs|css|json|xml|txt|html?|map|woff2?|ttf|otf|ico|jpe?g|png|gif|webp|svg)(?:$|[?#])/i.test(path))return true;
    }catch(_e){}
    return false;
  }
  function urlOf(stream){return stream&&typeof stream.url==="string"?stream.url.trim():""}
  function isDirect(stream,url){
    var hint=String((stream&&(stream.type||stream.format||stream.mimeType||stream.contentType))||"").toLowerCase();
    return /(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd)(?:[?#]|$)/i.test(url)||/(?:hls|mpegurl|dash|mp4|video\/)/.test(hint);
  }
  function rank(stream,url){
    if(isDirect(stream,url))return 0;
    try{
      var path=new URL(String(url)).pathname.toLowerCase();
      if(/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return 1;
    }catch(_e){}
    if(stream&&stream.headers&&typeof stream.headers==="object"&&Object.keys(stream.headers).length)return 2;
    return 3;
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
    var end=Math.min(bytes.length,16384),out="";
    for(var i=0;i<end;i++)out+=String.fromCharCode(bytes[i]);
    return out;
  }
  function validHls(text){
    var value=String(text||"").replace(/^\uFEFF/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
  async function probe(stream,url){
    if(typeof g.fetch!=="function")return true;
    var controller=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",headers:headersFor(stream),redirect:"follow",signal:controller.signal});
      if(!response||!response.ok||blocked(response.url||url))return false;
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      var bytes=await prefixBytes(response,controller),text=ascii(bytes);
      if(/(?:\.m3u8)(?:[?#]|$)/i.test(url)||/(?:mpegurl|vnd\.apple)/.test(contentType))return validHls(text);
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
        candidates.push({stream:stream,url:url,rank:rank(stream,url),index:i});
      }
      candidates.sort(function(a,b){return a.rank-b.rank||a.index-b.index});
      for(var c=0;c<candidates.length;c++){
        candidates[c].probe=(config.probeAllUrls||(config.probeDirectMedia&&isDirect(candidates[c].stream,candidates[c].url)))&&probeCount++<config.maxProbes;
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
