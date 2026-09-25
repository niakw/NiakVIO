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
    """Locate the whole owned Bloc boundary, falling back only for legacy JS."""
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
    probe_first_segment_native = bool(cfg.get("probe_first_segment_native", True))
    native_probe_max_rows = max(1, min(int(cfg.get("native_probe_max_rows", 8)), 16))
    native_probe_timeout_ms = max(900, min(int(cfg.get("native_probe_timeout_ms", 2500)), 5000))
    minimum_vod_duration_seconds = max(30, min(int(cfg.get("minimum_vod_duration_seconds", 90)), 600))
    inspect_master_facts = bool(cfg.get("inspect_master_facts", True))
    drop_unprobed_hls_after_budget = bool(cfg.get("drop_unprobed_hls_after_budget", True))
    short_static_media_seconds = max(5, min(int(cfg.get("short_static_media_seconds", 30)), 60))
    network_sample_bytes = max(16384, min(int(cfg.get("network_sample_bytes", 65536)), 262144))
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
                "minimumVodDurationSeconds": minimum_vod_duration_seconds,
                "dropUnprobedHlsAfterBudget": drop_unprobed_hls_after_budget,
                "shortStaticMediaSeconds": short_static_media_seconds,
                "networkSampleBytes": network_sample_bytes,
                "implementationRevision": "native-vod-duration-proof-v10",
            }
        )
    if inspect_master_facts:
        payload_config.update(
            {
                "inspectMasterFacts": True,
                "implementationRevision": "native-master-facts-network-v13",
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
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"})){var cap=typeof range==="number"?Math.max(188,Math.floor(range)):4096;out.Range="bytes=0-"+String(cap-1)}
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
    if(!bytes||!bytes.length)return {state:"unknown",reason:"segment_bytes_unavailable"};
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
    var encrypted=playlistEncrypted(body),init=mapUri(body,playlistUrl),targets=mediaUris(body,playlistUrl,2),initProof=null;
    if(init){
      var initResult=await fetchBounded(init,stream,referer,4096,config.nativeProbeTimeoutMs||config.timeoutMs);
      if(initResult.state==="invalid")return initResult;if(initResult.state!=="ok")return {state:"unknown",reason:initResult.reason||"init_fetch_unknown"};
      var initBytes=await responseBytes(initResult,4096);initProof=segmentProof(initBytes,initResult.contentType,initResult.url||init,true,encrypted);
      if(initProof.state==="invalid")return initProof;
    }
    if(!targets.length)return initProof||{state:"unknown",reason:"segment_uri_missing"};
    var sampleCap=Math.max(16384,Number(config.networkSampleBytes||65536)||65536),success=0,totalBytes=0,totalElapsed=0,firstProof=null,attempts=Math.min(2,targets.length);
    for(var i=0;i<attempts;i++){
      var started=(typeof Date!=="undefined"&&Date.now)?Date.now():0;
      var result=await fetchBounded(targets[i],stream,referer,sampleCap,config.nativeProbeTimeoutMs||config.timeoutMs);
      if(result.state==="invalid"){if(i===0)return result;continue}
      if(result.state!=="ok"){if(i===0)return {state:"unknown",reason:result.reason||"segment_fetch_unknown"};continue}
      var bytes=await responseBytes(result,sampleCap),ended=(typeof Date!=="undefined"&&Date.now)?Date.now():started,elapsed=Math.max(1,Number(ended-started)||1);
      var proof=segmentProof(bytes,result.contentType,result.url||targets[i],!!init,encrypted);
      if(i===0)firstProof=proof;
      if(proof.state==="invalid"){if(i===0)return proof;continue}
      if(proof.state==="valid"){success+=1;totalBytes+=Number(bytes&&bytes.length||0)||0;totalElapsed+=elapsed}
    }
    var base=firstProof||initProof||{state:"unknown",reason:"segment_container_unknown"};
    if(base.state==="valid"){
      var ratio=attempts?success/attempts:1,sampleMbps=totalBytes>0&&totalElapsed>0?totalBytes*8/totalElapsed/1000:null;
      base.networkEvidence={success:true,latencyMs:success?Math.round(totalElapsed/success):null,sampleBytes:totalBytes,sampleMbps:sampleMbps,sampleConfidence:totalBytes>=131072?.75:totalBytes>=65536?.65:totalBytes>=32768?.55:.4,segmentSuccessRatio:ratio,sampleKind:"hls-segment-prefix",source:"hls-first-segment-probe-v13"};
    }
    return base;
  }
  async function nativeFirstSegmentProof(stream){
    var referer=headerValue(stream,"referer"),root=await fetchBounded(String(stream.url||""),stream,referer,false,config.nativeProbeTimeoutMs||config.timeoutMs);
    if(root.state==="invalid")return root;if(root.state!=="ok")return {state:"unknown",reason:root.reason||"playlist_fetch_unknown"};
    var body=await responseText(root),kind=playlistKind(body),base=root.url||String(stream.url||""),facts=null;
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",reason:"playlist_"+kind};
    if(kind==="master"){
      if(config.inspectMasterFacts)facts=masterFacts(body);
      var variants=variantUris(body,base);if(!variants.length)return {state:"invalid",reason:"master_without_variants"};
      var child=await fetchBounded(variants[0],stream,referer,false,config.nativeProbeTimeoutMs||config.timeoutMs);
      if(child.state==="invalid")return child;if(child.state!=="ok")return {state:"unknown",reason:child.reason||"variant_fetch_unknown"};
      body=await responseText(child);kind=playlistKind(body);base=child.url||variants[0];
      if(kind==="invalid"||kind==="header_only")return {state:"invalid",reason:"variant_"+kind};
      if(kind==="master")return {state:"unknown",reason:"nested_master"};
    }
    var tiny=shortMediaDuration(body);if(tiny)return {state:"invalid",reason:"vod_duration_too_short",durationSeconds:tiny};
    var proof=await proveMediaPlaylist(body,base,stream,referer);if(facts)proof.facts=facts;return proof;
  }
  function segmentDuration(body){
    var text=clean(body),re=/#EXTINF\s*:\s*([0-9]+(?:\.[0-9]+)?)/gi,m,total=0,count=0;
    while((m=re.exec(text))!==null){var value=Number(m[1]);if(Number.isFinite(value)&&value>0){total+=value;count++}}
    return {total:total,count:count};
  }
  function finiteVodDurationSeconds(body){
    var text=clean(body);if(!/#EXT-X-ENDLIST(?:\s|$)/i.test(text)&&!/#EXT-X-PLAYLIST-TYPE\s*:\s*VOD\b/i.test(text))return 0;
    var stats=segmentDuration(text);return stats.count?stats.total:0;
  }
  function shortFiniteVod(body){var d=finiteVodDurationSeconds(body),floor=Number(config.minimumVodDurationSeconds||90)||90;return d>0&&d<floor?d:0}
  function shortStaticMedia(body){
    var text=clean(body);if(!text||/#EXT-X-ENDLIST(?:\s|$)/i.test(text)||/#EXT-X-PLAYLIST-TYPE\s*:\s*(?:VOD|EVENT)\b/i.test(text))return 0;
    // MEDIA-SEQUENCE alone is not sufficient live proof for NiakVIO's VOD catalogue:
    // short offline/maintenance placeholders commonly expose it. Preserve only
    // strong live/LL-HLS timing/control evidence.
    if(/#EXT-X-(?:PROGRAM-DATE-TIME|SERVER-CONTROL|PART|SKIP)\s*:/i.test(text))return 0;
    var stats=segmentDuration(text),cap=Number(config.shortStaticMediaSeconds||30)||30;
    return stats.count>0&&stats.count<=3&&stats.total>0&&stats.total<cap?stats.total:0;
  }
  function shortMediaDuration(body){return shortFiniteVod(body)||shortStaticMedia(body)}
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
  function masterQuality(height){var h=Number(height||0);if(h>=4000)return"4320p";if(h>=2000)return"2160p";if(h>=1350)return"1440p";if(h>=900)return"1080p";if(h>=650)return"720p";if(h>=550)return"576p";if(h>=450)return"480p";if(h>=300)return"360p";return""}
  function hlsAttr(line,name){var key=String(name||""),q=new RegExp("(?:^|[:,])\\s*"+key+"\\s*=\\s*\\\"([^\\\"]*)\\\"","i").exec(String(line||""));if(q)return clean(q[1]);var b=new RegExp("(?:^|[:,])\\s*"+key+"\\s*=\\s*([^,\\s]+)","i").exec(String(line||""));return clean(b&&b[1])}
  function hlsLang(value){var raw=clean(value).toLowerCase().replace(/_/g,"-"),first=raw.split("-")[0],a={eng:"en",english:"en",fra:"fr",fre:"fr",french:"fr",hin:"hi",hindi:"hi",jpn:"ja",japanese:"ja",tam:"ta",tamil:"ta",tel:"te",telugu:"te",ben:"bn",bengali:"bn",mal:"ml",malayalam:"ml",kan:"kn",kannada:"kn",pan:"pa",punjabi:"pa",guj:"gu",gujarati:"gu",mar:"mr",marathi:"mr",urd:"ur",urdu:"ur",kor:"ko",korean:"ko",spa:"es",spanish:"es",deu:"de",ger:"de",german:"de",ita:"it",italian:"it",por:"pt",portuguese:"pt",ara:"ar",arabic:"ar",tur:"tr",turkish:"tr",rus:"ru",russian:"ru",zho:"zh",chi:"zh",chinese:"zh",bul:"bg",bulgarian:"bg",fin:"fi",finnish:"fi",ell:"el",gre:"el",greek:"el",hun:"hu",hungarian:"hu",ind:"id",indonesian:"id",fas:"fa",per:"fa",persian:"fa",heb:"he",hebrew:"he",kur:"ku",kurdish:"ku",uzb:"uz",uzbek:"uz",pol:"pl",polish:"pl",ron:"ro",rum:"ro",romanian:"ro",slk:"sk",slo:"sk",slovak:"sk",swe:"sv",swedish:"sv",ces:"cs",cze:"cs",czech:"cs",vie:"vi",vietnamese:"vi"};if(a[raw])return a[raw];if(a[first])return a[first];return /^[a-z]{2,3}$/.test(first)?first:""}
  function codecFacts(value){var parts=clean(value).split(",").map(function(v){return clean(v).toLowerCase()}).filter(Boolean),video="",audio="",hdr="";for(var i=0;i<parts.length;i++){var p=parts[i];if(/^(?:dvhe|dvh1)/.test(p)){video="HEVC";hdr="Dolby Vision"}else if(!video&&/^(?:hvc1|hev1)/.test(p))video="HEVC";else if(!video&&/^(?:avc1|avc3)/.test(p))video="AVC";else if(!video&&/^av01/.test(p))video="AV1";else if(!video&&/^vp09/.test(p))video="VP9";if(!audio&&/^mp4a/.test(p))audio="AAC";else if(!audio&&/^ec-3/.test(p))audio="E-AC3";else if(!audio&&/^ac-3/.test(p))audio="AC3";else if(!audio&&/^opus/.test(p))audio="Opus";else if(!audio&&/^flac/.test(p))audio="FLAC";else if(!audio&&/^alac/.test(p))audio="ALAC"}return{video:video,audio:audio,hdr:hdr}}
  function channelLabel(value){var v=clean(value).split("/")[0];if(v==="1")return"1.0";if(v==="2")return"2.0";if(v==="6")return"5.1";if(v==="8")return"7.1";return/^(?:1\.0|2\.0|2\.1|5\.1|7\.1)$/.test(v)?v:""}
  function bandwidthLabel(value){var n=Number(value||0);if(!Number.isFinite(n)||n<=0)return"";if(n>=1000000){var mb=Math.round(n/100000)/10;return String(mb).replace(/\.0$/,"")+" Mbps max"}var kb=Math.round(n/1000);return kb?kb+" kbps max":""}
  function frameLabel(value){var n=Number(String(value||"").replace(",","."));if(!Number.isFinite(n)||n<=0)return"";var rounded=Math.round(n*1000)/1000;return String(rounded).replace(/\.0+$/,"")+" fps"}
  function rangeLabel(value){var v=clean(value).toUpperCase();return v==="HLG"?"HLG":v==="PQ"?"HDR":v==="SDR"?"SDR":""}
  function masterFacts(body){
    var lines=clean(body).split(/\r?\n/),best={width:0,height:0,bandwidth:0,codecs:"",frameRate:"",videoRange:""},audioTracks=[],subtitleTracks=[],audioSeen={},subSeen={};
    for(var i=0;i<lines.length;i++){
      var line=lines[i];
      if(/^#EXT-X-STREAM-INF\s*:/i.test(line)){
        var rm=/\bRESOLUTION\s*=\s*(\d{2,5})\s*[xX]\s*(\d{2,5})/i.exec(line),width=Number(rm&&rm[1]||0),height=Number(rm&&rm[2]||0);
        var bandwidth=Number(hlsAttr(line,"AVERAGE-BANDWIDTH")||hlsAttr(line,"BANDWIDTH")||0)||0;
        if(height>best.height||(height===best.height&&bandwidth>best.bandwidth))best={width:width,height:height,bandwidth:bandwidth,codecs:hlsAttr(line,"CODECS"),frameRate:hlsAttr(line,"FRAME-RATE"),videoRange:hlsAttr(line,"VIDEO-RANGE")};
        continue;
      }
      if(!/^#EXT-X-MEDIA\s*:/i.test(line))continue;
      var type=clean(hlsAttr(line,"TYPE")).toUpperCase(),code=hlsLang(hlsAttr(line,"LANGUAGE")),name=hlsAttr(line,"NAME"),channels=channelLabel(hlsAttr(line,"CHANNELS"));
      if(!code)code=hlsLang(name);
      if(type==="AUDIO"&&code&&!audioSeen[code+"|"+channels]){audioSeen[code+"|"+channels]=1;audioTracks.push({language:code,name:name||code.toUpperCase(),channels:channels})}
      if(type==="SUBTITLES"&&code&&!subSeen[code]){subSeen[code]=1;subtitleTracks.push({language:code,name:name||code.toUpperCase()})}
    }
    var codecs=codecFacts(best.codecs),hdr=codecs.hdr||rangeLabel(best.videoRange),channelValues=audioTracks.map(function(t){return t.channels}).filter(Boolean),audioChannels=channelValues.length&&channelValues.every(function(v){return v===channelValues[0]})?channelValues[0]:"";
    return{width:best.width,height:best.height,resolution:best.width&&best.height?best.width+"x"+best.height:"",quality:masterQuality(best.height),bandwidth:best.bandwidth,bitrate:bandwidthLabel(best.bandwidth),codec:codecs.video,audioCodec:codecs.audio,frameRate:frameLabel(best.frameRate),hdr:hdr,audioChannels:audioChannels,audioTracks:audioTracks,subtitleTracks:subtitleTracks,rawCodecs:best.codecs};
  }
  function weakFact(value){return !clean(value)||/^(?:unknown|inconnu(?:e)?|n\/?a|none|null|undefined|auto|-+)$/i.test(clean(value))}
  function enrichMasterFacts(stream,facts){
    if(!stream||!facts)return stream;
    var row=Object.assign({},stream),tracks=Array.isArray(facts.audioTracks)?facts.audioTracks:[],subs=Array.isArray(facts.subtitleTracks)?facts.subtitleTracks:[];
    if(facts.quality){if(!weakFact(row.quality)&&!clean(row.sourceQuality))row.sourceQuality=clean(row.quality);if(!weakFact(row.resolution)&&!clean(row.sourceResolution))row.sourceResolution=clean(row.resolution);row.quality=facts.quality;row.hlsMasterQuality=facts.quality}
    if(facts.width)row.width=Number(facts.width)||row.width;if(facts.height)row.height=Number(facts.height)||row.height;if(facts.resolution)row.resolution=facts.resolution;
    if(facts.bitrate&&weakFact(row.bitrate)){row.bitrate=facts.bitrate;row.hlsMasterBandwidth=Number(facts.bandwidth)||0}
    if(facts.codec&&weakFact(row.codec)){row.codec=facts.codec;row.hlsMasterCodecs=facts.rawCodecs||""}
    if(facts.audioCodec&&weakFact(row.audioCodec))row.audioCodec=facts.audioCodec;
    if(facts.audioChannels&&weakFact(row.audioChannels))row.audioChannels=facts.audioChannels;
    if(facts.frameRate&&weakFact(row.frameRate))row.frameRate=facts.frameRate;
    if(facts.hdr&&weakFact(row.hdr))row.hdr=facts.hdr;
    if(tracks.length){row.audioTracks=tracks.map(function(t){return{language:t.language,name:t.name,channels:t.channels||""}});row.hlsMasterAudioTracks=row.audioTracks;if(tracks.length===1){var actual=tracks[0].language;if(!weakFact(row.language)&&clean(row.language).toLowerCase()!==actual&&!clean(row.sourceLanguage))row.sourceLanguage=clean(row.language);row.language=actual}}
    // Integrated HLS subtitle renditions belong to the master playlist. Keep
    // them as technical metadata only; do not inject language-only objects into
    // row.subtitles/extCaptions, whose Nuvio/SubSense contract requires a URL.
    if(subs.length){row.subtitleTracks=subs.map(function(t){return{language:t.language,name:t.name}});row.hlsMasterSubtitleTracks=row.subtitleTracks}
    return row;
  }
  async function validateChild(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);if(result.state!=="ok")return result.state;
    var body=await responseText(result),kind=playlistKind(body);if(kind==="media"&&shortMediaDuration(body))return"invalid";return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function inspectHls(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);
    if(result.state!=="ok")return {state:result.state,reason:result.reason||"fetch_failed",result:result};
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return {state:"direct",format:ct.indexOf("webm")>=0?"webm":"mp4",url:result.url,result:result};
    var body=await responseText(result),kind=playlistKind(body);
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",kind:kind,body:body,result:result};
    if(kind==="media"){var tiny=shortMediaDuration(body);if(tiny)return {state:"invalid",kind:"vod_duration_too_short",durationSeconds:tiny,body:body,result:result};return {state:"valid",kind:kind,url:result.url,body:body,result:result}}

    var facts=config.inspectMasterFacts?masterFacts(body):null,variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);
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
    return {state:"valid",kind:"master",url:result.url,body:body,result:result,facts:facts};
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
    if(inspection.state==="valid")return config.inspectMasterFacts&&inspection.facts?enrichMasterFacts(stream,inspection.facts):stream;
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
        if(remaining<=0)return hlsHint(stream)&&config.dropUnprobedHlsAfterBudget?null:stream;
        if(!hlsHint(stream)){
          if(!config.probeAllUrls)return stream;
          remaining-=1;
          return await validateOrRecover(stream);
        }
        remaining-=1;
        var proof=await nativeFirstSegmentProof(stream);
        if(proof.state==="invalid"||(proof.state==="unknown"&&config.failClosedUnknown)){
          return null;
        }
        var output=config.inspectMasterFacts&&proof.facts?enrichMasterFacts(stream,proof.facts):stream;if(proof.networkEvidence&&output&&typeof output==="object"){output=Object.assign({},output);output.__nuvioStreamNetworkEvidenceV1=proof.networkEvidence}return output;
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
    # Clean v3 placement is compositor-owned. The HLS Bloc can only replace its
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
