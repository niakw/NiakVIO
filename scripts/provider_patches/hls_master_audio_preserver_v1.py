#!/usr/bin/env python3
"""Preserve HLS master audio and append a capability-aware media safety guard.

Native QuickJS clients expose a synchronous ``__native_fetch`` bridge. Their JS
``AbortSignal`` cannot reliably interrupt an HTTP call already executing in the
host, so doing extra playback probes from provider JS can turn a nominal 6.5 s
probe into a 30-60 s stall. The guard therefore performs only deterministic,
network-free rejection on native runtimes and reserves remote preflight for
runtimes whose regular fetch can actually be bounded by AbortSignal.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

AUDIO_MARKER = "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1"
SAFETY_MARKER = "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1"

GUARD = re.compile(
    r"if\s*\(\s*!\s*/#EXT-X-STREAM-INF/i\.test\((?P<var>[A-Za-z_$][A-Za-z0-9_$]*)\)\s*\)\s*return"
)

SAFETY_WRAPPER = r"""
/* SAFETY_MARKER_PLACEHOLDER */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function slot(v){
    if(Array.isArray(v))return {key:null,list:v};
    if(v&&typeof v==="object"){
      for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}
    }
    return null;
  }
  function rebuild(v,x,list){
    if(x.key===null)return list;
    var o=Object.assign({},v);o[x.key]=list;return o;
  }
  function req(a){
    var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{
      tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]
    };
    q.tmdbId=s(q.tmdbId||q.id||first).replace(/^tmdb:/i,"").split(":")[0];
    q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();
    q.season=Number(q.season||a[2]||0)||0;
    q.episode=Number(q.episode||a[3]||0)||0;
    return q;
  }
  function nativeHost(){
    try{return typeof g.__native_fetch==="function"}catch(_e){return false}
  }
  function isTv(){
    try{
      var ua=s(g.navigator&&g.navigator.userAgent);
      if(/NuvioTV|Android TV/i.test(ua))return true;
      if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;
      if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;
      var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}
      if(/followRedirects/.test(src))return false;
      var signalAware=/options\.signal|var\s+signal\s*=/.test(src);
      var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);
      return signalAware&&fourArgNative;
    }catch(_e){return false}
  }
  function obviousNonMedia(row){
    var u=s(row&&row.url);
    if(!u)return "missing_url";
    if(!/^https?:\/\//i.test(u))return "invalid_url";
    var lower=u.toLowerCase();
    if(/(?:youtube\.com|youtube-nocookie\.com)\/(?:embed|watch)(?:\/|\?|$)/i.test(lower))return "video_page_url";
    if(/\/embed(?:\/|\?|#|$)/i.test(lower))return "embed_page_url";
    if(/\.(?:html?|php)(?:[?#]|$)/i.test(lower))return "html_page_url";
    if(/^https?:\/\/[^/]+\/\/www\./i.test(u))return "malformed_nested_url";
    return "";
  }
  function headers(row,range){
    var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};
    Object.keys(src).forEach(function(k){out[k]=s(src[k])});
    try{
      var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;
      if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])});
    }catch(_e){}
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";
    return out;
  }
  function timeoutSignal(ms){
    try{
      if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms);
    }catch(_e){}
    return void 0;
  }
  async function responseText(r){
    if(!r)return "";
    try{if(typeof r.text==="function")return s(await r.text())}catch(_e){}
    try{
      if(typeof r.arrayBuffer==="function"){
        var ab=await r.arrayBuffer();
        if(ab){
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(new Uint8Array(ab)));
          if(typeof Buffer!=="undefined")return s(Buffer.from(ab).toString("utf8"));
        }
      }
    }catch(_e){}
    try{
      if(r.body&&typeof r.body.getReader==="function"){
        var reader=r.body.getReader(),chunks=[],total=0;
        while(total<262144){
          var part=await reader.read();
          if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}
          if(!part||part.done)break;
          if(total>0)break;
        }
        try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}
        if(total){
          var merged=new Uint8Array(total),offset=0;
          for(var i=0;i<chunks.length;i++){
            var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);
            merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break;
          }
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(merged));
          if(typeof Buffer!=="undefined")return s(Buffer.from(merged).toString("utf8"));
        }
      }
    }catch(_e){}
    return "";
  }
  async function fetchText(url,row,range){
    try{
      var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:headers(row,range),signal:timeoutSignal(c.timeoutMs)});
      if(!r)return {state:"unknown",reason:"no_response"};
      var st=Number(r.status||0),ct=s(r.headers&&r.headers.get?r.headers.get("content-type"):"").toLowerCase();
      if(st===401||st===403||st===404||st===410||st>=500)return {state:"dead",status:st,contentType:ct};
      if(!r.ok)return {state:"unknown",status:st,contentType:ct};
      var text=await responseText(r);
      return {state:"ok",status:st,url:s(r.url||url),contentType:ct,text:text};
    }catch(e){
      return {state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"};
    }
  }
  function playlistKind(text){
    var body=s(text).replace(/^\uFEFF/,"");
    if(!/^#EXTM3U(?:\s|$)/i.test(body))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(body))return "master";
    if(/#EXTINF\s*:/i.test(body))return "media";
    return "unknown";
  }
  function firstVariant(text,base){
    var lines=s(text).split(/\r?\n/);
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var v=s(lines[j]);if(!v||v.charAt(0)==="#")continue;
        try{return new URL(v,base).toString()}catch(_e){return ""}
      }
    }
    return "";
  }
  function durationSeconds(text){
    var total=0,count=0,re=/#EXTINF\s*:\s*([0-9]+(?:\.[0-9]+)?)/gi,m;
    while((m=re.exec(s(text)))!==null){var n=Number(m[1]);if(Number.isFinite(n)&&n>0){total+=n;count++}}
    if(count<2||total<60)return null;
    return total;
  }
  async function inspectHls(row,url){
    var r=await fetchText(url,row,false);
    if(r.state!=="ok")return r;
    var kind=playlistKind(r.text);
    if(kind==="invalid")return {state:"dead",reason:"not_hls",status:r.status};
    if(kind==="media")return {state:"ok",duration:durationSeconds(r.text),url:r.url||url};
    if(kind==="master"){
      var child=firstVariant(r.text,r.url||url);
      if(!child)return {state:"dead",reason:"master_without_variant"};
      var cr=await fetchText(child,row,false);
      if(cr.state!=="ok")return cr;
      var ck=playlistKind(cr.text);
      if(ck!=="media"&&ck!=="master")return {state:"dead",reason:"invalid_child"};
      return {state:"ok",duration:durationSeconds(cr.text),url:r.url||url};
    }
    return {state:"ok",duration:null,url:r.url||url};
  }
  function mediaKind(row){
    var u=s(row&&row.url).toLowerCase(),t=s(row&&(row.type||row.format)).toLowerCase();
    if(/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(u)||/hls|mpegurl|m3u8/.test(t))return "hls";
    if(/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(u)||/mp4|matroska|webm|video\//.test(t))return "direct";
    return "other";
  }
  async function expectedSeconds(q){
    if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;
    var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie";
    var url;
    if(kind==="tv"&&q.season>0&&q.episode>0){
      url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;
    }else{
      url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;
    }
    try{
      var r=await g.fetch(url,{headers:{Accept:"application/json"},signal:timeoutSignal(c.tmdbTimeoutMs)});
      if(!r||!r.ok)return null;
      var d=await r.json(),minutes=Number(d&&d.runtime||0);
      if(!minutes&&kind==="tv"&&Array.isArray(d&&d.episode_run_time)&&d.episode_run_time.length)minutes=Number(d.episode_run_time[0]||0);
      return minutes>=5?minutes*60:null;
    }catch(_e){return null}
  }
  async function directPlayable(row,url){
    var r=await fetchText(url,row,true);
    if(r.state!=="ok")return r;
    if(/text\/html|application\/xhtml/i.test(r.contentType)||/^<!doctype html|^<html/i.test(r.text||""))return {state:"dead",reason:"html_payload"};
    return {state:"ok"};
  }
  async function check(row,expected,tv,nativeRuntime){
    if(!row||typeof row!=="object")return {keep:false,reason:"invalid_row"};
    var obvious=obviousNonMedia(row);
    if(obvious)return {keep:false,reason:obvious};
    /* Native QuickJS fetch is a blocking host call. JS AbortSignal is not a
       trustworthy deadline there, so never add a second media request from the
       safety layer. Provider-specific identity checks still run before this. */
    if(nativeRuntime)return {keep:true,reason:tv?"native_tv_no_extra_probe":"native_client_no_extra_probe"};
    var kind=mediaKind(row),result;
    if(kind==="hls")result=await inspectHls(row,s(row.url));
    else if(kind==="direct")result=await directPlayable(row,s(row.url));
    else return {keep:true};
    if(result.state==="dead")return {keep:false,reason:result.reason||("http_"+result.status)};
    if(result.state==="unknown"){
      if(c.strictPlayback||tv)return {keep:false,reason:result.reason||"unverified_media"};
      return {keep:true};
    }
    if(kind==="hls"&&expected&&result.duration){
      var ratio=result.duration/expected;
      if(ratio<c.minDurationRatio||ratio>c.maxDurationRatio)return {keep:false,reason:"duration_identity_mismatch",ratio:ratio};
    }
    return {keep:true};
  }
  function install(o,k){
    if(!o||typeof o[k]!=="function"||o[k].__nuvioRuntimeMediaSafetyV1)return false;
    var native=o[k];
    var wrap=async function(){
      var v=await native.apply(this,arguments),x=slot(v);
      if(!x||!x.list.length)return v;
      var q=req(arguments),tv=isTv(),nativeRuntime=nativeHost();
      var expected=nativeRuntime?null:await expectedSeconds(q);
      var head=x.list.slice(0,c.maxRows),tail=x.list.slice(c.maxRows);
      var checks=await Promise.all(head.map(function(row){return check(row,expected,tv,nativeRuntime)}));
      var kept=head.filter(function(_row,i){return checks[i]&&checks[i].keep}).concat(tail);
      return rebuild(v,x,kept);
    };
    wrap.__nuvioRuntimeMediaSafetyV1=true;o[k]=wrap;return true;
  }
  var ok=false;
  try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
"""


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
    provider_id = str(context.get("provider_id") or "").strip().casefold()

    output = text
    if AUDIO_MARKER not in output:
        changed = 0

        def replacement(match: re.Match[str]) -> str:
            nonlocal changed
            changed += 1
            variable = match.group("var")
            return (
                f"if(!/#EXT-X-STREAM-INF/i.test({variable})||"
                f"/#EXT-X-MEDIA:[^\\r\\n]*TYPE=AUDIO/i.test({variable}))return"
            )

        output = GUARD.sub(replacement, output)
        if changed:
            output = output.rstrip() + f"\n/* {AUDIO_MARKER} */\n"

    if SAFETY_MARKER in output:
        return output

    cfg = {
        "providerId": provider_id,
        "timeoutMs": 6500,
        "tmdbTimeoutMs": 4500,
        "maxRows": 4,
        "minDurationRatio": 0.55,
        "maxDurationRatio": 1.8,
        "durationIdentity": provider_id == "netmirror",
        "strictPlayback": provider_id == "moviebox",
        "tmdbKey": "1865f43a0549ca50d341dd9ab8b29f49",
        "implementationRevision": "field-safety-v3-native-aware",
    }
    payload = json.dumps(cfg, separators=(",", ":"))
    marker = f"{SAFETY_MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    wrapper = SAFETY_WRAPPER.replace("SAFETY_MARKER_PLACEHOLDER", marker).replace(
        "CONFIG_PLACEHOLDER", payload
    )
    return output.rstrip() + "\n" + wrapper.lstrip()
