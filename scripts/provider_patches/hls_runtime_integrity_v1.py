#!/usr/bin/env python3
"""Append bounded HLS structural validation to provider stream output.

The guard is intentionally playback-oriented rather than an activation switch:
it never disables a provider globally. It only removes an individual HLS result
when the fetched payload conclusively proves that it is not a usable playlist
(HTML/JSON masquerading as m3u8, header-only playlist, dead child playlist,
etc.). Network/CORS/time-out uncertainty preserves the stream instead of
turning transient reachability into a false negative.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_HLS_RUNTIME_INTEGRITY_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    timeout_ms = max(1500, min(int(cfg.get("timeout_ms", 6500)), 12000))
    max_children = max(1, min(int(cfg.get("max_children", 2)), 4))
    payload = json.dumps(
        {"timeoutMs": timeout_ms, "maxChildren": max_children},
        separators=(",", ":"),
    )
    marker = f"{MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    old = text.find(f"/* {MARKER}:")
    if old >= 0:
        call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', old)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated HLS runtime integrity wrapper")
        text = (text[:old] + text[end + 2 :]).rstrip()

    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,config){
  "use strict";
  function clean(v){return String(v==null?"":v).replace(/^\uFEFF/,"").replace(/^ï»¿/,"").trim()}
  function hlsHint(stream){
    if(!stream||typeof stream!=="object")return false;
    var u=String(stream.url||"").toLowerCase(),t=String(stream.type||stream.format||"").toLowerCase();
    return /\.m3u8(?:[?#]|$)/i.test(u)||u.indexOf("/hls/")>=0||u.indexOf("/hls2/")>=0||t==="hls"||t==="m3u8"||t.indexOf("mpegurl")>=0;
  }
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function requestHeaders(stream){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var out={};Object.keys(src).forEach(function(k){out[k]=String(src[k])});
    if(!out.Accept)out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,text/plain,*/*";
    return out;
  }
  async function fetchText(url,stream){
    if(!g||typeof g.fetch!=="function")return {state:"unknown",reason:"fetch_unavailable"};
    var controller=typeof AbortController!=="undefined"?new AbortController():null;
    var timer=setTimeout(function(){try{if(controller)controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var body=clean(await response.text());
      return {state:"ok",body:body,url:String(response.url||url),contentType:String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"")};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{clearTimeout(timer);try{if(controller)controller.abort()}catch(_e){}}
  }
  function playlistKind(body){
    var text=clean(body);if(!/^#EXTM3U(?:\s|$)/i.test(text))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(text))return "master";
    if(/#EXTINF\s*:/i.test(text)||/#EXT-X-PART\s*:/i.test(text)||/#EXT-X-MAP\s*:/i.test(text)){
      var lines=text.split(/\r?\n/).map(function(v){return v.trim()}).filter(Boolean);
      if(lines.some(function(v){return v.charAt(0)!=="#"}))return "media";
    }
    return "header_only";
  }
  function variantUris(body,base){
    var lines=clean(body).split(/\r?\n/),out=[];
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var candidate=clean(lines[j]);if(!candidate)continue;if(candidate.charAt(0)==="#")continue;
        var u=absolute(candidate,base);if(u&&out.indexOf(u)<0)out.push(u);break;
      }
      if(out.length>=config.maxChildren)break;
    }
    return out;
  }
  function audioUris(body,base){
    var out=[],lines=clean(body).split(/\r?\n/);
    lines.forEach(function(line){
      if(!/^#EXT-X-MEDIA\s*:/i.test(line)||!/TYPE\s*=\s*AUDIO/i.test(line))return;
      var m=line.match(/URI\s*=\s*"([^"]+)"/i)||line.match(/URI\s*=\s*([^,\s]+)/i);
      var u=m&&absolute(m[1],base);if(u&&out.indexOf(u)<0)out.push(u);
    });
    return out.slice(0,config.maxChildren);
  }
  async function validateChild(url,stream){
    var result=await fetchText(url,stream);if(result.state!=="ok")return result.state;
    var kind=playlistKind(result.body);return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function validateHls(stream){
    var result=await fetchText(String(stream.url||""),stream);
    if(result.state!=="ok")return result.state;
    var kind=playlistKind(result.body);
    if(kind==="invalid"||kind==="header_only")return "invalid";
    if(kind==="media")return "valid";

    var variants=variantUris(result.body,result.url||stream.url),audio=audioUris(result.body,result.url||stream.url);
    if(!variants.length)return "invalid";
    var variantState="invalid";
    for(var i=0;i<variants.length;i++){
      var s=await validateChild(variants[i],stream);if(s==="valid"){variantState="valid";break}if(s==="unknown")variantState="unknown";
    }
    if(variantState!=="valid")return variantState;
    if(audio.length){
      var audioState="invalid";
      for(var j=0;j<audio.length;j++){
        var a=await validateChild(audio[j],stream);if(a==="valid"){audioState="valid";break}if(a==="unknown")audioState="unknown";
      }
      if(audioState!=="valid")return audioState;
    }
    return "valid";
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!hlsHint(stream))return stream;
      var state=await validateHls(stream);
      if(state==="invalid"){
        try{console.warn("[Nuvio HLS integrity] rejected malformed playlist",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
        return null;
      }
      return stream;
    }));
    var filtered=checks.filter(Boolean);
    if(Array.isArray(value))return filtered;
    var copy=Object.assign({},value);copy.streams=filtered;return copy;
  }
  function wrap(target,key){
    if(!target||typeof target[key]!=="function"||target[key].__nuvioHlsIntegrityV1)return false;
    var native=target[key];
    var wrapped=async function(){return filterRows(await native.apply(this,arguments))};
    try{Object.defineProperty(wrapped,"__nuvioHlsIntegrityV1",{value:true})}catch(_e){wrapped.__nuvioHlsIntegrityV1=true}
    target[key]=wrapped;return true;
  }
  function install(){
    var done=false;
    try{done=wrap(g,"getStreams")||done}catch(_e){}
    try{if(typeof module!=="undefined"&&module&&module.exports){done=wrap(module.exports,"getStreams")||done;done=wrap(module.exports,"streams")||done}}catch(_e){}
    try{if(typeof exports!=="undefined")done=wrap(exports,"getStreams")||done}catch(_e){}
    return done;
  }
  install();
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", payload)
    return text.rstrip() + "\n" + wrapper
