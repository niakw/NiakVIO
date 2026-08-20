#!/usr/bin/env python3
"""Upgrade the stream sanitizer with generic playback repair.

The base sanitizer validates fetched content instead of trusting suffixes. This
layer keeps the UTF-8 BOM fix and adds two transport repairs that apply to every
provider using the sanitizer:

* a structurally valid HLS playlist that is missing only the mandatory #EXTM3U
  line is rebuilt as HLS instead of being discarded; relative playlist URIs are
  absolutized before the repaired manifest is handed to the native reader;
* HTML/JSON resolver pages are treated as indirect player responses, not media.
  A bounded resolver follows explicit video/source/iframe/file URLs and preserves
  the parent Referer/Origin for the resolved media. Generic HTML/error pages that
  do not resolve to media are still rejected.

No authentication, token, DRM or access-control bypass is attempted. Explicit
provider headers are preserved, and legacy ``stream.headers`` are mirrored into
Stremio/Nuvio ``behaviorHints.proxyHeaders.request`` so native readers actually
receive them.

Reapplication is deliberately supported: durable provider overrides may change
probe policy later. The repair marker is separate from the historical V5 marker
so already-published V5 providers are upgraded on their next materialization.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BASE_PATH = ROOT / "stream_output_sanitizer.py"
MARKER = "NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5"
MARKER_COMMENT = f"/* {MARKER} */"
REPAIR_MARKER = "NUVIO_STREAM_OUTPUT_HLS_HTML_REPAIR_V7"
REPAIR_MARKER_COMMENT = f"/* {REPAIR_MARKER} */"


def _load_base_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v4", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


BASE_APPLY = _load_base_apply()


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise ValueError(f"stream sanitizer {label} hook count={count}")
    return text.replace(old, new, 1)


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    # Let V4 decide first. Its marker is content-addressed, so changed probe policy
    # still regenerates the underlying wrapper. The V7 repair marker, not the old
    # V5 marker, proves that all generic playback repairs are present.
    patched = BASE_APPLY(text, options=options, **kwargs)
    if patched == text and REPAIR_MARKER_COMMENT in text:
        return text

    patched = patched.replace(MARKER_COMMENT, "").replace(REPAIR_MARKER_COMMENT, "").rstrip()

    # UTF-8 BOM may arrive either as U+FEFF or as the mojibake byte sequence.
    source = 'replace(/^\\uFEFF/,"").trimStart()'
    target = 'replace(/^(?:\\uFEFF|\\u00EF\\u00BB\\u00BF)/,"").trimStart()'
    if target not in patched:
        if source not in patched:
            raise ValueError("stream sanitizer HLS normalization hook not found")
        patched = patched.replace(source, target, 1)

    old_headers = r'''  function headersFor(stream){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,*/*;q=0.8","Range":"bytes=0-4095"};
    var source=stream&&stream.headers;
    if(source&&typeof source==="object"){
      try{Object.keys(source).forEach(function(key){if(source[key]!=null)output[key]=String(source[key])})}catch(_e){}
    }
    return output;
  }
'''
    new_headers = r'''  function hasHeader(headers,name){
    if(!headers||typeof headers!=="object")return false;
    var wanted=String(name||"").toLowerCase(),keys=[];
    try{keys=Object.keys(headers)}catch(_e){}
    for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===wanted)return true;
    return false;
  }
  function proxyRequestHeaders(stream){
    try{
      var hints=stream&&stream.behaviorHints;
      var proxy=hints&&hints.proxyHeaders;
      return proxy&&proxy.request&&typeof proxy.request==="object"?proxy.request:null;
    }catch(_e){return null}
  }
  function ensureProxyRequest(stream){
    if(!stream||typeof stream!=="object")return null;
    if(!stream.behaviorHints||typeof stream.behaviorHints!=="object")stream.behaviorHints={};
    if(!stream.behaviorHints.proxyHeaders||typeof stream.behaviorHints.proxyHeaders!=="object")stream.behaviorHints.proxyHeaders={};
    if(!stream.behaviorHints.proxyHeaders.request||typeof stream.behaviorHints.proxyHeaders.request!=="object")stream.behaviorHints.proxyHeaders.request={};
    stream.behaviorHints.notWebReady=true;
    return stream.behaviorHints.proxyHeaders.request;
  }
  function setHeaderIfMissing(headers,key,value){
    if(!headers||value==null||String(value).trim()===""||hasHeader(headers,key))return;
    headers[key]=String(value);
  }
  function syncPlaybackHeaders(stream){
    if(!stream||typeof stream!=="object")return;
    var legacy=stream.headers&&typeof stream.headers==="object"?stream.headers:null;
    if(!legacy)return;
    var request=ensureProxyRequest(stream);
    try{Object.keys(legacy).forEach(function(key){if(legacy[key]!=null)setHeaderIfMissing(request,key,legacy[key])})}catch(_e){}
  }
  function ensurePlaybackHeaders(stream,referer){
    if(!stream||typeof stream!=="object"||!referer)return;
    var request=ensureProxyRequest(stream);
    if(!stream.headers||typeof stream.headers!=="object")stream.headers={};
    setHeaderIfMissing(request,"Referer",referer);
    setHeaderIfMissing(stream.headers,"Referer",referer);
    try{
      var origin=new URL(String(referer)).origin;
      setHeaderIfMissing(request,"Origin",origin);
      setHeaderIfMissing(stream.headers,"Origin",origin);
    }catch(_e){}
  }
  function headersFor(stream,referer){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,*/*;q=0.8","Range":"bytes=0-32767","User-Agent":"Mozilla/5.0"};
    var legacy=stream&&stream.headers;
    if(legacy&&typeof legacy==="object"){
      try{Object.keys(legacy).forEach(function(key){if(legacy[key]!=null)output[key]=String(legacy[key])})}catch(_e){}
    }
    var proxy=proxyRequestHeaders(stream);
    if(proxy){try{Object.keys(proxy).forEach(function(key){if(proxy[key]!=null)output[key]=String(proxy[key])})}catch(_e){}}
    if(referer){
      setHeaderIfMissing(output,"Referer",referer);
      try{setHeaderIfMissing(output,"Origin",new URL(String(referer)).origin)}catch(_e){}
    }
    return output;
  }
'''
    patched = _replace_once(patched, old_headers, new_headers, "header propagation")

    old_prefix = r'''  async function prefixBytes(response,controller){
    if(response.body&&typeof response.body.getReader==="function"){
      var reader=response.body.getReader();
      try{var chunk=await reader.read();return chunk&&chunk.value?chunk.value:new Uint8Array(0)}
      finally{try{await reader.cancel()}catch(_e){};try{controller.abort()}catch(_e){}}
    }
    var buffer=await response.arrayBuffer();
    try{controller.abort()}catch(_e){}
    return new Uint8Array(buffer.slice(0,4096));
  }
'''
    new_prefix = r'''  async function prefixBytes(response,controller){
    if(response.body&&typeof response.body.getReader==="function"){
      var reader=response.body.getReader(),chunks=[],total=0;
      try{
        while(total<32768){
          var chunk=await reader.read();
          if(!chunk||chunk.done)break;
          var value=chunk.value||new Uint8Array(0);
          if(!value.length)continue;
          if(total+value.length>32768)value=value.slice(0,32768-total);
          chunks.push(value);total+=value.length;
        }
        var output=new Uint8Array(total),offset=0;
        for(var i=0;i<chunks.length;i++){output.set(chunks[i],offset);offset+=chunks[i].length}
        return output;
      }finally{try{await reader.cancel()}catch(_e){};try{controller.abort()}catch(_e){}}
    }
    var buffer=await response.arrayBuffer();
    try{controller.abort()}catch(_e){}
    return new Uint8Array(buffer.slice(0,32768));
  }
'''
    patched = _replace_once(patched, old_prefix, new_prefix, "bounded response preview")
    patched = patched.replace(
        'var end=Math.min(bytes.length,16384),out="";',
        'var end=Math.min(bytes.length,32768),out="";',
        1,
    )

    valid_anchor = "  function validHls(text){\n"
    helpers = r'''  function absoluteMediaUri(raw,baseUrl){
    var value=String(raw||"").trim();
    if(!value||value.charAt(0)==="#")return value;
    if(/^(?:data:|blob:|skd:|urn:)/i.test(value))return value;
    try{return new URL(value,String(baseUrl||"")).toString()}catch(_e){return value}
  }
  function normalizeHlsText(text,baseUrl){
    var value=String(text||"").replace(/^(?:\uFEFF|\u00EF\u00BB\u00BF)/,"").trimStart();
    if(/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(value))return null;
    var hadHeader=value.indexOf("#EXTM3U")===0;
    if(!hadHeader){
      if(!/(?:^|\n)#EXT-(?:X-[A-Z0-9-]+|INF)\s*[:]/i.test(value))return null;
      value="#EXTM3U\n"+value;
    }
    if(!validHls(value))return null;
    var lines=value.split(/\r?\n/);
    for(var i=0;i<lines.length;i++){
      var line=String(lines[i]||"");
      if(line.charAt(0)==="#"){
        lines[i]=line.replace(/URI=(["'])([^"']+)\1/gi,function(_all,quote,uri){return "URI="+quote+absoluteMediaUri(uri,baseUrl)+quote});
      }else if(line.trim()){
        lines[i]=absoluteMediaUri(line.trim(),baseUrl);
      }
    }
    return {text:lines.join("\n"),repaired:!hadHeader};
  }
  function repairedHlsUrl(text){
    return "data:application/vnd.apple.mpegurl;charset=utf-8,"+encodeURIComponent(String(text||""));
  }
  function looksHtml(text,contentType){
    return /text\/html|application\/xhtml\+xml/i.test(String(contentType||""))||/^\s*(?:<!doctype|<html|<head|<body)/i.test(String(text||""));
  }
  function looksJson(text,contentType){
    return /application\/(?:json|[^;]+\+json)/i.test(String(contentType||""))||/^\s*[\[{]/.test(String(text||""));
  }
  function mediaCandidatesFromPayload(text,baseUrl){
    var value=String(text||"").replace(/\\\//g,"/").replace(/&amp;/gi,"&").replace(/\\u0026/gi,"&"),rows=[],seen=Object.create(null);
    function push(raw,allowOpaque){
      var candidate=String(raw||"").trim().replace(/^['"]|['"]$/g,"");
      if(!candidate||candidate.length>4096)return;
      candidate=absoluteMediaUri(candidate,baseUrl);
      if(!candidate||candidate===baseUrl||blocked(candidate)||seen[candidate])return;
      var path="";try{path=new URL(candidate).pathname.toLowerCase()}catch(_e){}
      var embedLike=/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path);
      if(!allowOpaque&&!directExtension(candidate)&&!embedLike)return;
      seen[candidate]=1;rows.push({url:candidate,direct:isDirect(null,candidate)?0:1});
    }
    var match,re=/<(?:video|source|iframe)\b[^>]*?\b(?:src|data-src)\s*=\s*["']([^"']+)["']/gi;
    while((match=re.exec(value))!==null)push(match[1],true);
    re=/(?:["']?(?:file|src|source|url)["']?\s*[:=]\s*)["']([^"']+)["']/gi;
    while((match=re.exec(value))!==null)push(match[1],true);
    re=/https?:\/\/[^\s"'<>\\]+/gi;
    while((match=re.exec(value))!==null)push(match[0],false);
    rows.sort(function(a,b){return a.direct-b.direct});
    return rows.slice(0,2).map(function(row){return row.url});
  }
'''
    if helpers not in patched:
        if valid_anchor not in patched:
            raise ValueError("stream sanitizer HLS helper anchor not found")
        patched = patched.replace(valid_anchor, helpers + valid_anchor, 1)

    patched = _replace_once(
        patched,
        "  async function probe(stream,url){\n",
        "  async function probeResolved(stream,url,depth,referer){\n",
        "recursive probe",
    )
    patched = patched.replace(
        'headers:headersFor(stream),redirect:"follow",signal:controller.signal',
        'headers:headersFor(stream,referer),redirect:"follow",signal:controller.signal',
        1,
    )

    old_hls = r'''      if(/(?:\.m3u8?)(?:[?#]|$)/i.test(url)||/(?:\.m3u8?)(?:[?#]|$)/i.test(finalUrl)||/(?:mpegurl|vnd\.apple)/.test(contentType)||/^\s*#EXTM3U/i.test(text)){
        if(!validHls(text))return false;
        markDirect(stream,finalUrl);
        return true;
      }
'''
    new_hls = r'''      if(/(?:\.m3u8?)(?:[?#]|$)/i.test(url)||/(?:\.m3u8?)(?:[?#]|$)/i.test(finalUrl)||/(?:mpegurl|vnd\.apple)/.test(contentType)||/^\s*#EXT(?:M3U|-(?:X-[A-Z0-9-]+|INF)\s*:)/i.test(text)){
        var hls=normalizeHlsText(text,finalUrl);
        if(!hls)return false;
        if(hls.repaired){
          stream.url=repairedHlsUrl(hls.text);
          if(!stream.type)stream.type="hls";
          if(!stream.mimeType)stream.mimeType="application/vnd.apple.mpegurl";
          stream.isDirect=true;
        }else markDirect(stream,finalUrl);
        syncPlaybackHeaders(stream);
        return true;
      }
'''
    patched = _replace_once(patched, old_hls, new_hls, "generic HLS repair")

    old_text_reject = r'''      if(/(?:text\/html|application\/json|text\/plain)/.test(contentType)||/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(text))return false;
'''
    new_text_reject = r'''      if(looksHtml(text,contentType)||looksJson(text,contentType)){
        var candidates=mediaCandidatesFromPayload(text,finalUrl);
        if(depth<2&&candidates.length){
          ensurePlaybackHeaders(stream,finalUrl);
          for(var candidateIndex=0;candidateIndex<candidates.length;candidateIndex++){
            if(await probeResolved(stream,candidates[candidateIndex],depth+1,finalUrl))return true;
          }
        }
        return false;
      }
'''
    patched = _replace_once(patched, old_text_reject, new_text_reject, "indirect player resolution")
    patched = patched.replace(
        "      return bytes.length>0;\n",
        '      if(/^text\\//i.test(contentType))return false;\n      return bytes.length>0;\n',
        1,
    )

    install_anchor = "  function install(container,key){\n"
    probe_wrapper = '  async function probe(stream,url){return await probeResolved(stream,url,0,"")}\n'
    if probe_wrapper not in patched:
        if install_anchor not in patched:
            raise ValueError("stream sanitizer install anchor not found")
        patched = patched.replace(install_anchor, probe_wrapper + install_anchor, 1)

    # Mirror legacy headers before ranking/probing so both the sanitizer and the
    # actual Nuvio reader use the same request contract.
    patched = patched.replace(
        "        var stream=result[i],url=urlOf(stream);\n",
        "        var stream=result[i];syncPlaybackHeaders(stream);var url=urlOf(stream);\n",
        1,
    )

    return patched.rstrip() + f"\n{MARKER_COMMENT}\n{REPAIR_MARKER_COMMENT}\n"
