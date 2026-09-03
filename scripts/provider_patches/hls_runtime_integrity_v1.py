#!/usr/bin/env python3
"""Append bounded HLS validation and recovery to provider stream output.

The guard is playback-oriented rather than an activation switch. A malformed
HLS row is not treated as a dead provider: Niakvio first tries to normalize the
response, follow public player/embed context and recover a real HLS/DASH/direct
media source while preserving ordinary request headers. Only a conclusively
invalid row with no bounded recovery path is removed.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from provider_patch_blocks import begin_marker, has_managed_fix, owned_span, render_managed_fix, replace_managed_fix, strip_managed_fix

MARKER = "NUVIO_HLS_RUNTIME_INTEGRITY_V1"
MANAGED_FIX_ID = "CORE.HLS_RUNTIME_INTEGRITY.V1"


def _layer_position(text: str, managed_id: str, legacy_marker: str) -> int:
    """Locate the whole owned Lego boundary, falling back only for legacy JS."""
    span = owned_span(text, managed_id)
    if span is not None:
        return span[0]
    return text.find(legacy_marker)


POST_HLS_MARKERS = (
    "/* NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1 */",
    begin_marker("CORE.RUNTIME_COMPAT.V1"),
    begin_marker("CORE.STREAM_FACTS.V1"),
    begin_marker("CORE.STREAM_IDENTITY.V1"),
    begin_marker("CORE.STREAM_PRESENTATION.V1"),
    begin_marker("CORE.PROVIDER_BRANDING.V1"),
    begin_marker("CORE.STREAM_SANITIZER.V6"),
    begin_marker("CORE.MEDIA_TYPE_RESOLUTION.V1"),
)


def _owned_hls_slot_is_stale(text: str) -> bool:
    """Detect only provable HLS order drift without guessing provider semantics."""
    span = owned_span(text, MANAGED_FIX_ID)
    if span is None:
        return False
    start, end = span
    positions = [text.find(marker) for marker in POST_HLS_MARKERS]
    positions = [position for position in positions if position >= 0]
    if any(position < start for position in positions):
        return True
    after = [position for position in positions if position >= end]
    boundary = min(after) if after else len(text)
    return bool(text[end:boundary].strip())


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    timeout_ms = max(1500, min(int(cfg.get("timeout_ms", 6500)), 12000))
    max_children = max(1, min(int(cfg.get("max_children", 2)), 4))
    max_recovery_pages = max(1, min(int(cfg.get("max_recovery_pages", 4)), 8))
    max_recovery_candidates = max(2, min(int(cfg.get("max_recovery_candidates", 12)), 24))
    probe_all_urls = bool(cfg.get("probe_all_urls", False))
    fail_closed_unknown = bool(cfg.get("fail_closed_unknown", False))
    probe_first_segment_native = bool(cfg.get("probe_first_segment_native", False))
    native_probe_max_rows = max(1, min(int(cfg.get("native_probe_max_rows", 3)), 8))
    native_probe_timeout_ms = max(900, min(int(cfg.get("native_probe_timeout_ms", 2500)), 5000))
    payload_config = {
        "timeoutMs": timeout_ms,
        "maxChildren": max_children,
        "maxRecoveryPages": max_recovery_pages,
        "maxRecoveryCandidates": max_recovery_candidates,
        "implementationRevision": "recovery-first-v5-native-budget-owned",
    }
    # Preserve byte-for-byte idempotence for the repository-wide default. Only
    # providers which explicitly require a strict final-output gate receive the
    # payload with its two additional flags.
    if probe_all_urls or fail_closed_unknown:
        payload_config.update(
            {
                "probeAllUrls": probe_all_urls,
                "failClosedUnknown": fail_closed_unknown,
                "implementationRevision": "final-output-order-v6-native-budget-owned",
            }
        )
    if probe_first_segment_native:
        payload_config.update(
            {
                "probeFirstSegmentNative": True,
                "nativeProbeMaxRows": native_probe_max_rows,
                "nativeProbeTimeoutMs": native_probe_timeout_ms,
                "implementationRevision": "native-first-segment-container-proof-v7",
            }
        )
    payload = json.dumps(payload_config, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    is_v3 = (
        text.count("/* BEGIN NIAKVIO_PROVIDER */") == 1
        and text.count("/* END NIAKVIO_PROVIDER */") == 1
        and "NIAKVIO_PROVIDER_BASE_OWNED_V3" in text
    )
    owned = has_managed_fix(text, MANAGED_FIX_ID)
    relocate_owned = owned and _owned_hls_slot_is_stale(text)

    # One-time migration from the pre-managed HLS wrapper. Managed revisions are
    # replaced in place and never moved relative to recovery/safety/Core layers.
    if not owned:
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
  function nativeHlsHost(){try{return typeof g.__native_fetch==="function"}catch(_e){return false}}
  function clean(v){return String(v==null?"":v).replace(/^\uFEFF/,"").replace(/^ï»¿/,"").trim()}
  function hlsHint(stream){
    if(!stream||typeof stream!=="object")return false;
    var u=String(stream.url||"").toLowerCase(),t=String(stream.type||stream.format||"").toLowerCase();
    return /\.m3u8(?:[?#]|$)/i.test(u)||u.indexOf("/hls/")>=0||u.indexOf("/hls2/")>=0||t==="hls"||t==="m3u8"||t.indexOf("mpegurl")>=0;
  }
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function headerValue(stream,name){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var wanted=String(name||"").toLowerCase(),keys=Object.keys(src);
    for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===wanted)return clean(src[keys[i]]);
    return "";
  }
  function requestHeaders(stream,referer,range){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var out={};Object.keys(src).forEach(function(k){out[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(out).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(out[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(out).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete out[k]});
        out.Referer=referer;try{out.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-4095";
    if(!out.Accept)out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,text/plain,*/*";
    return out;
  }
  async function fetchBounded(url,stream,referer,range,timeoutOverride){
    if(!g||typeof g.fetch!=="function")return {state:"unknown",reason:"fetch_unavailable"};
    var controller=typeof AbortController!=="undefined"?new AbortController():null;
    var timer=null,timeoutMs=Number(timeoutOverride||config.timeoutMs)||config.timeoutMs;
    if(controller&&typeof setTimeout==="function")timer=setTimeout(function(){try{controller.abort()}catch(_e){}},timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream,referer,range),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      return {state:"ok",response:response,url:String(response.url||url),contentType:contentType};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{if(timer!==null&&typeof clearTimeout==="function")try{clearTimeout(timer)}catch(_e){}}
  }
  async function responseText(result){
    var response=result&&result.response;if(!response)return "";
    try{if(typeof response.text==="function")return clean(await response.text())}catch(_e){}
    try{if(typeof response.arrayBuffer==="function"){var ab=await response.arrayBuffer();return clean(new TextDecoder("utf-8").decode(ab))}}catch(_e){}
    try{if(response.body&&typeof response.body.getReader==="function"){var reader=response.body.getReader(),chunks=[],total=0;while(total<131072){var part=await reader.read();if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}if(!part||part.done)break}try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}var merged=new Uint8Array(total),offset=0;for(var i=0;i<chunks.length;i++){var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break}return clean(new TextDecoder("utf-8").decode(merged))}}catch(_e){}
    return "";
  }
  async function responseBytes(result,cap){
    var response=result&&result.response,limit=Math.max(188,Number(cap||4096)||4096);if(!response)return new Uint8Array(0);
    try{
      if(response.body&&typeof response.body.getReader==="function"){
        var reader=response.body.getReader(),chunks=[],total=0;
        while(total<limit){var part=await reader.read();if(part&&part.value){var take=Math.min(part.value.byteLength||part.value.length||0,limit-total);chunks.push(part.value.subarray?part.value.subarray(0,take):part.value);total+=take}if(!part||part.done||total>=limit)break}
        try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}
        var merged=new Uint8Array(total),offset=0;for(var i=0;i<chunks.length;i++){var value=chunks[i],len=value.byteLength||value.length||0;merged.set(value,offset);offset+=len}return merged;
      }
    }catch(_e){}
    try{if(typeof response.arrayBuffer==="function"){var ab=await response.arrayBuffer(),bytes=new Uint8Array(ab);return bytes.length>limit?bytes.slice(0,limit):bytes}}catch(_e){}
    return new Uint8Array(0);
  }
  function asciiPrefix(bytes,cap){var out="",n=Math.min(bytes&&bytes.length||0,Number(cap||96)||96);for(var i=0;i<n;i++){var b=bytes[i];out+=b>=32&&b<=126?String.fromCharCode(b):" "}return out.trim().toLowerCase()}
  function hasTsSync(bytes){var n=bytes&&bytes.length||0;if(n<188)return n>0&&bytes[0]===0x47;var max=Math.min(187,n-1);for(var o=0;o<=max;o++){if(bytes[o]!==0x47)continue;if(o+188<n&&bytes[o+188]!==0x47)continue;if(o+376<n&&bytes[o+376]!==0x47)continue;return true}return false}
  function hasMp4Box(bytes){if(!bytes||bytes.length<8)return false;for(var o=0;o+8<=bytes.length&&o<64;o+=4){var a=String.fromCharCode(bytes[o+4]||0,bytes[o+5]||0,bytes[o+6]||0,bytes[o+7]||0);if(a==="ftyp"||a==="styp"||a==="moof"||a==="moov")return true}return false}
  function nonMediaPayload(bytes,contentType){var ct=String(contentType||"").toLowerCase(),p=asciiPrefix(bytes,160);if(/text\/html|application\/(?:json|problem\+json)|text\/plain|application\/xhtml\+xml/.test(ct))return true;return /^<!doctype\s+html|^<html\b|^<\?xml\b|^\{|^\[/.test(p)}
  function mapUri(body,base){var m=clean(body).match(/#EXT-X-MAP\s*:[^\n\r]*\bURI\s*=\s*"([^"]+)"/i)||clean(body).match(/#EXT-X-MAP\s*:[^\n\r]*\bURI\s*=\s*([^,\s]+)/i);return m?absolute(m[1],base):""}
  function firstMediaUri(body,base){var lines=clean(body).split(/\r?\n/);for(var i=0;i<lines.length;i++){var v=clean(lines[i]);if(!v||v.charAt(0)==="#")continue;var u=absolute(v,base);if(u)return u}return ""}
  function playlistEncrypted(body){var lines=clean(body).match(/#EXT-X-KEY\s*:[^\n\r]*/gi)||[];for(var i=0;i<lines.length;i++){var m=lines[i].match(/METHOD\s*=\s*([^,\s]+)/i),method=clean(m&&m[1]).toUpperCase();if(method&&method!=="NONE")return true}return false}
  function segmentProof(bytes,contentType,url,hasMap,encrypted){
    if(nonMediaPayload(bytes,contentType))return {state:"invalid",reason:"segment_non_media_payload"};
    if(encrypted)return {state:"unknown",reason:"encrypted_segment"};
    var u=String(url||"").toLowerCase(),ct=String(contentType||"").toLowerCase();
    var ts=/\.ts(?:[?#]|$)/i.test(u)||/video\/(?:mp2t|mpegts)|application\/(?:mp2t|mpegts)/i.test(ct);
    if(ts)return hasTsSync(bytes)?{state:"valid",kind:"mpegts"}:{state:"invalid",reason:"ts_sync_missing"};
    var fragmented=hasMap||/\.(?:m4s|mp4)(?:[?#]|$)/i.test(u)||/video\/mp4|application\/mp4/i.test(ct);
    if(fragmented)return hasMp4Box(bytes)?{state:"valid",kind:"fmp4"}:{state:"invalid",reason:"fmp4_signature_missing"};
    return {state:"unknown",reason:"segment_container_unknown"};
  }
  async function proveMediaPlaylist(body,playlistUrl,stream,referer){
    var encrypted=playlistEncrypted(body),init=mapUri(body,playlistUrl),target=init||firstMediaUri(body,playlistUrl);
    if(!target)return {state:"unknown",reason:"segment_uri_missing"};
    var result=await fetchBounded(target,stream,referer,true,config.nativeProbeTimeoutMs||config.timeoutMs);
    if(result.state==="invalid")return result;if(result.state!=="ok")return {state:"unknown",reason:result.reason||"segment_fetch_unknown"};
    var bytes=await responseBytes(result,4096),proof=segmentProof(bytes,result.contentType,result.url||target,!!init,encrypted);
    if(init&&proof.state==="valid"&&proof.kind==="fmp4")return proof;
    return proof;
  }
  async function nativeFirstSegmentProof(stream){
    var referer=headerValue(stream,"referer"),root=await fetchBounded(String(stream.url||""),stream,referer,false,config.nativeProbeTimeoutMs||config.timeoutMs);
    if(root.state==="invalid")return root;if(root.state!=="ok")return {state:"unknown",reason:root.reason||"playlist_fetch_unknown"};
    var body=await responseText(root),kind=playlistKind(body),base=root.url||String(stream.url||"");
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",reason:"playlist_"+kind};
    if(kind==="master"){
      var variants=variantUris(body,base);if(!variants.length)return {state:"invalid",reason:"master_without_variants"};
      var child=await fetchBounded(variants[0],stream,referer,false,config.nativeProbeTimeoutMs||config.timeoutMs);
      if(child.state==="invalid")return child;if(child.state!=="ok")return {state:"unknown",reason:child.reason||"variant_fetch_unknown"};
      body=await responseText(child);kind=playlistKind(body);base=child.url||variants[0];
      if(kind==="invalid"||kind==="header_only")return {state:"invalid",reason:"variant_"+kind};
      if(kind==="master")return {state:"unknown",reason:"nested_master"};
    }
    return proveMediaPlaylist(body,base,stream,referer);
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
  async function validateChild(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);if(result.state!=="ok")return result.state;
    var body=await responseText(result),kind=playlistKind(body);return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function inspectHls(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);
    if(result.state!=="ok")return {state:result.state,reason:result.reason||"fetch_failed",result:result};
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return {state:"direct",format:ct.indexOf("webm")>=0?"webm":"mp4",url:result.url,result:result};
    var body=await responseText(result),kind=playlistKind(body);
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",kind:kind,body:body,result:result};
    if(kind==="media")return {state:"valid",kind:kind,url:result.url,body:body,result:result};

    var variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);
    if(!variants.length)return {state:"invalid",kind:"master_without_variants",body:body,result:result};
    var variantState="invalid";
    for(var i=0;i<variants.length;i++){
      var s=await validateChild(variants[i],stream,result.url||referer);if(s==="valid"){variantState="valid";break}if(s==="unknown")variantState="unknown";
    }
    if(variantState!=="valid")return {state:variantState,kind:"master_child_"+variantState,body:body,result:result};
    if(audio.length){
      var audioState="invalid";
      for(var j=0;j<audio.length;j++){
        var a=await validateChild(audio[j],stream,result.url||referer);if(a==="valid"){audioState="valid";break}if(a==="unknown")audioState="unknown";
      }
      if(audioState!=="valid")return {state:audioState,kind:"audio_child_"+audioState,body:body,result:result};
    }
    return {state:"valid",kind:"master",url:result.url,body:body,result:result};
  }
  function normalizedText(text){
    return clean(text).replace(/\\u002[fF]/g,"/").replace(/\\\//g,"/").replace(/&amp;/g,"&");
  }
  function candidateUrls(text,base){
    var body=normalizedText(text),out=[],seen={};
    function add(raw){
      var value=clean(raw).replace(/^['"]|['"]$/g,"");if(!value||/^javascript:|^data:/i.test(value))return;
      var u=absolute(value,base);if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u);
    }
    var patterns=[
      /(?:src|href|data-src|data-url|data-file|data-player|data-embed|file|source|url|playlist|hls|stream|embedUrl|embed_url)\s*[:=]\s*["']([^"']+)["']/gi,
      /(https?:\/\/[^"'<>\s\\]+)/gi,
      /["']([^"']+\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#][^"']*)?)["']/gi
    ],m;
    for(var i=0;i<patterns.length&&out.length<config.maxRecoveryCandidates;i++){
      patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null&&out.length<config.maxRecoveryCandidates)add(m[1]);
    }
    return out;
  }
  function mediaHint(url){return /\.m3u8(?:[?#]|$)|\/hls2?\//i.test(url)?"hls":/\.mpd(?:[?#]|$)/i.test(url)?"dash":/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(url)?"direct":"page"}
  function cloneRecovered(stream,url,format,referer){
    var row=Object.assign({},stream,{url:url}),headers={};
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};Object.keys(src).forEach(function(k){headers[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(headers).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(headers[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(headers).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete headers[k]});
        headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(Object.keys(headers).length)row.headers=headers;
    if(format==="hls"){row.type="hls";if("format" in row)row.format="m3u8"}
    else if(format==="dash"){row.type="dash";if("format" in row)row.format="mpd"}
    else if(format){row.type=format;if("format" in row)row.format=format}
    return row;
  }
  async function probeDirect(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,true);if(result.state!=="ok")return null;
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return cloneRecovered(stream,result.url,ct.indexOf("webm")>=0?"webm":"mp4",referer);
    if(/(?:application\/dash\+xml|application\/xml|text\/xml)/i.test(ct)||/\.mpd(?:[?#]|$)/i.test(result.url)){
      var dash=await responseText(result);if(/<MPD(?:\s|>)/i.test(dash))return cloneRecovered(stream,result.url,"dash",referer);
    }
    if(/mpegurl/i.test(ct)||/\.m3u8(?:[?#]|$)/i.test(result.url)){
      var hls=await inspectHls(result.url,stream,referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||result.url,"hls",referer);
    }
    return null;
  }
  async function recover(stream,inspection){
    var queue=[],seen={},pages=0;
    function enqueue(url,referer){var u=absolute(url,referer||String(stream.url||""));if(!/^https?:\/\//i.test(u)||seen[u]||u===String(stream.url||""))return;seen[u]=1;queue.push({url:u,referer:referer||""})}
    var base=inspection&&inspection.result&&inspection.result.url||String(stream.url||"");
    candidateUrls(inspection&&inspection.body||"",base).forEach(function(u){enqueue(u,base)});
    var outerReferer=headerValue(stream,"referer");
    [stream&&stream.playerUrl,stream&&stream.embedUrl,stream&&stream.pageUrl,stream&&stream.sourceUrl,stream&&stream.referrer,stream&&stream.referer].forEach(function(u){if(u)enqueue(u,outerReferer||base)});
    if(outerReferer)enqueue(outerReferer,"");
    while(queue.length&&pages<config.maxRecoveryPages){
      var item=queue.shift(),kind=mediaHint(item.url);
      if(kind==="hls"){
        var hls=await inspectHls(item.url,stream,item.referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||item.url,"hls",item.referer);if(hls.state==="direct")return cloneRecovered(stream,hls.url||item.url,hls.format||"mp4",item.referer);
        candidateUrls(hls.body||"",hls.result&&hls.result.url||item.url).forEach(function(u){enqueue(u,hls.result&&hls.result.url||item.url)});continue;
      }
      if(kind==="direct"||kind==="dash"){
        var direct=await probeDirect(item.url,stream,item.referer);if(direct)return direct;continue;
      }
      pages++;
      var page=await fetchBounded(item.url,stream,item.referer,false);if(page.state!=="ok")continue;
      var ct=page.contentType||"";
      if(/^video\//i.test(ct))return cloneRecovered(stream,page.url,page.contentType.indexOf("webm")>=0?"webm":"mp4",item.referer);
      var body=await responseText(page);
      if(/^#EXTM3U(?:\s|$)/i.test(body)){
        var pageHls=await inspectHls(page.url,stream,item.referer);if(pageHls.state==="valid")return cloneRecovered(stream,pageHls.url||page.url,"hls",item.referer);
      }
      if(/<MPD(?:\s|>)/i.test(body))return cloneRecovered(stream,page.url,"dash",item.referer);
      candidateUrls(body,page.url||item.url).forEach(function(u){enqueue(u,page.url||item.url)});
    }
    return null;
  }
  async function validateOrRecover(stream){
    var inspection=await inspectHls(String(stream.url||""),stream,headerValue(stream,"referer"));
    if(inspection.state==="valid")return stream;
    if(inspection.state==="unknown"&&!config.failClosedUnknown)return stream;
    if(inspection.state==="direct")return cloneRecovered(stream,inspection.url||String(stream.url||""),inspection.format||"mp4",headerValue(stream,"referer"));
    var recovered=await recover(stream,inspection);if(recovered)return recovered;
    return null;
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(nativeHlsHost()){
      if(!config.probeFirstSegmentNative||!rows||!rows.length)return value;
      var remaining=Math.max(1,Number(config.nativeProbeMaxRows||1)||1);
      var checks=await Promise.all(rows.map(async function(stream){
        if(!hlsHint(stream)||remaining<=0)return stream;
        remaining-=1;
        var proof=await nativeFirstSegmentProof(stream);
        if(proof.state==="invalid"){
          try{console.warn("[Nuvio HLS integrity] rejected invalid first media container",proof.reason||"invalid",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
          return null;
        }
        return stream;
      }));
      var nativeFiltered=checks.filter(Boolean);
      if(Array.isArray(value))return nativeFiltered;
      var nativeCopy=Object.assign({},value);nativeCopy.streams=nativeFiltered;return nativeCopy;
    }
    if(!rows||!rows.length)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!config.probeAllUrls&&!hlsHint(stream))return stream;
      var output=await validateOrRecover(stream);
      if(!output){
        try{console.warn("[Nuvio HLS integrity] rejected malformed playlist after bounded recovery",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
      }
      return output;
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
    # Clean v3 placement is compositor-owned. The HLS Lego can only replace its
    # own STARTFIX/CLOSEFIX rectangle; it is never allowed to move itself.
    if is_v3:
        return replace_managed_fix(
            text,
            MANAGED_FIX_ID,
            wrapper,
            data=payload_config,
        )

    # Legacy-only migration may still repair historical flattened ordering.
    if owned and not relocate_owned:
        return replace_managed_fix(
            text,
            MANAGED_FIX_ID,
            wrapper,
            data=payload_config,
        )
    if relocate_owned:
        text = strip_managed_fix(text, MANAGED_FIX_ID)

    post_layers = [
        position
        for position in (
            text.find("/* NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1 */"),
            _layer_position(text, "CORE.RUNTIME_COMPAT.V1", "/* NUVIO_GLOBAL_RUNTIME_COMPAT_V1 */"),
            _layer_position(text, "CORE.STREAM_FACTS.V1", "/* NUVIO_GLOBAL_STREAM_FACTS_V1:"),
            _layer_position(text, "CORE.STREAM_IDENTITY.V1", "/* NUVIO_GLOBAL_STREAM_IDENTITY_V1:"),
            _layer_position(text, "CORE.STREAM_PRESENTATION.V1", "/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:"),
        )
        if position >= 0
    ]
    recovery_layers = [
        position
        for position in (
            _layer_position(text, "CORE.MEDIA_ENRICHMENT.V1", "/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:"),
            _layer_position(text, "CORE.RUNTIME_MEDIA_SAFETY.V4", "/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:"),
        )
        if position >= 0
    ]
    managed = render_managed_fix(MANAGED_FIX_ID, wrapper, data=payload_config)
    if post_layers and (not recovery_layers or max(recovery_layers) < min(post_layers)):
        insertion = min(post_layers)
        return (
            text[:insertion].rstrip()
            + "\n"
            + managed.strip()
            + "\n"
            + text[insertion:].lstrip()
        ).rstrip() + "\n"
    return text.rstrip() + "\n" + managed.strip() + "\n"
