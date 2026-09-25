#!/usr/bin/env python3
"""Core-owned global stream score, emitted only from proven media + network evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from provider_patch_blocks import has_managed_fix, replace_managed_fix

MARKER = "NUVIO_GLOBAL_STREAM_SCORE_V1"
MANAGED_FIX_ID = "CORE.STREAM_SCORE.V1"
REVISION = "evidence-gated-global-score-v1"


def _strip_existing(text: str) -> str:
    start = text.find(f"/* {MARKER}:")
    if start < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global stream score wrapper")
    return (text[:start] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    if not has_managed_fix(text, MANAGED_FIX_ID):
        text = _strip_existing(text)
    payload = {
        "schemaVersion": 1,
        "implementationRevision": REVISION,
        "minimumConfidence": 0.60,
        "weights": {
            "videoQuality": 45,
            "sourceProvenance": 10,
            "audioQuality": 10,
            "playbackNetwork": 30,
            "providerReliability": 5,
        },
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function n(v){var x=Number(v);return isFinite(x)&&x>=0?x:null}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function curve(v,p){if(v<=p[0][0])return p[0][1];if(v>=p[p.length-1][0])return p[p.length-1][1];for(var i=0;i<p.length-1;i++){var a=p[i],b=p[i+1];if(v>=a[0]&&v<=b[0]){var r=(v-a[0])/(b[0]-a[0]);return a[1]+(b[1]-a[1])*r}}return p[p.length-1][1]}
function height(f,r){var raw=n(r&&r.height);if(raw)return raw;var q=s((f&&f.quality)||(r&&r.quality)||(r&&r.resolution)).toLowerCase();if(/8k|4320/.test(q))return 4320;if(/4k|2160|uhd/.test(q))return 2160;var m=q.match(/(1440|1080|720|576|480|360|240)/);return m?Number(m[1]):null}
function codec(f,r){var x=s((f&&f.codec)||(r&&r.codec)||(r&&r.videoCodec)).toLowerCase();if(/av1/.test(x))return"av1";if(/hevc|h\.?265|x265/.test(x))return"hevc";if(/vp9/.test(x))return"vp9";if(/avc|h\.?264|x264/.test(x))return"avc";if(/mpeg.?2/.test(x))return"mpeg2";if(/vc.?1/.test(x))return"vc1";if(/mpeg.?4/.test(x))return"mpeg4";return""}
function bitrate(f,r){var raw=(f&&f.bitrate)||(r&&r.videoBitrate)||(r&&r.video_bitrate)||(r&&r.bitrate);if(raw==null||raw==="")return null;if(typeof raw==="number"){if(raw>100000)return raw/1000000;if(raw>1000)return raw/1000;return raw}var m=s(raw).replace(",",".").match(/([0-9]+(?:\.[0-9]+)?)\s*(gbps|mbps|kbps|bps)?/i);if(!m)return null;var v=Number(m[1]),u=String(m[2]||"").toLowerCase();if(u==="gbps")return v*1000;if(u==="kbps")return v/1000;if(u==="bps")return v/1000000;if(!u&&v>100000)return v/1000000;if(!u&&v>1000)return v/1000;return v}
function fps(f,r){var m=s((f&&f.frameRate)||(r&&r.frameRate)||(r&&r.fps)).replace(",",".").match(/([0-9]+(?:\.[0-9]+)?)/);return m?Number(m[1]):24}
function video(f,r){var parts=[],h=height(f,r),res={4320:100,2160:96,1440:90,1080:84,720:70,576:54,480:48,360:32,240:20};if(h)parts.push([.30,res[h]||(h>2160?96:h>1080?84:60)]);var co=codec(f,r),eff={av1:100,hevc:94,vp9:88,avc:78,vc1:58,mpeg2:48,mpeg4:45};if(co&&eff[co]!=null)parts.push([.20,eff[co]]);var br=bitrate(f,r);if(br&&h){var base={av1:2.8,hevc:3.5,vp9:4.2,avc:6,vc1:7,mpeg2:10,mpeg4:7.5}[co]||6,target=base*Math.pow(h/1080,2)*Math.max(.75,fps(f,r)/24);parts.push([.35,curve(br/Math.max(.1,target),[[0,0],[.4,25],[.6,50],[.8,72],[1,86],[1.3,94],[1.7,98],[2.2,100]])])}var tech=((f&&f.videoTech)||[]).join(" ").toLowerCase(),bd=parseInt(s((f&&f.bitDepth)||(r&&r.bitDepth)),10),dyn=null;if(/dolby\s*vision/.test(tech))dyn=98;else if(/hdr10\+/.test(tech))dyn=96;else if(/hdr10|\bhdr\b/.test(tech))dyn=92;else if(/hlg/.test(tech))dyn=90;else if(/\bsdr\b/.test(tech))dyn=65;else if(bd>=10)dyn=82;else if(bd===8)dyn=65;if(dyn!=null)parts.push([.15,dyn]);if(!parts.length)return null;var w=0,t=0;for(var i=0;i<parts.length;i++){w+=parts[i][0];t+=parts[i][0]*parts[i][1]}return{score:t/w,confidence:Math.min(1,w),bitrateMbps:br}}
function source(f,r){var x=(s((f&&f.sourceType)||(r&&r.sourceType))+" "+s((f&&f.releaseType)||(r&&r.releaseType))).toLowerCase();if(/uhd.*remux|ultra.*remux/.test(x))return 100;if(/blu.?ray.*remux|bd.*remux/.test(x))return 98;if(/uhd.*blu|ultra.*blu/.test(x))return 100;if(/blu.?ray|bdmv/.test(x))return 92;if(/web.?dl/.test(x))return 84;if(/hdtv/.test(x))return 65;if(/web.?rip/.test(x))return 58;if(/dvd.*rip/.test(x))return 35;if(/\bdvd\b/.test(x))return 35;if(/cam/.test(x))return 8;if(/telesync|\bts\b/.test(x))return 12;if(/telecine|\btc\b/.test(x))return 18;return null}
function audio(f,r){var x=s((f&&f.audioCodec)||(r&&r.audioCodec)||(r&&r.audio)).toLowerCase(),base=null;if(/truehd/.test(x))base=100;else if(/dts.?hd.*(?:ma|master)/.test(x))base=98;else if(/dts.?hd/.test(x))base=94;else if(/lpcm/.test(x))base=100;else if(/\bpcm\b/.test(x))base=98;else if(/flac/.test(x))base=96;else if(/e.?ac.?3|ddp|dd\+/.test(x))base=80;else if(/ac.?3/.test(x))base=68;else if(/opus/.test(x))base=76;else if(/\bdts\b/.test(x))base=72;else if(/aac/.test(x))base=65;else if(/mp3/.test(x))base=45;else if(/alac/.test(x))base=96;if(base==null)return null;var m=s((f&&f.audioChannels)||(r&&r.audioChannels)||(r&&r.channels)).match(/([0-9]+(?:\.[0-9]+)?)/),ch=m?Number(m[1]):2,cs=ch>=7.1?100:ch>=5.1?90:ch>=2?70:50;return .7*base+.3*cs}
function network(r,mediaBr){var e=r&&r.__nuvioStreamNetworkEvidenceV1;if(!e||e.success!==true)return null;var parts=[],detail={source:s(e.source||"terminal-media-probe")},through=n(e.sampleMbps),sampleConf=n(e.sampleConfidence);if(through!=null){detail.sampleMbps=Math.round(through*100)/100;if(mediaBr){var hr=through/Math.max(.1,mediaBr);detail.headroomRatio=Math.round(hr*1000)/1000;parts.push([.50,curve(hr,[[.5,5],[.8,20],[1,40],[1.25,60],[1.5,75],[2.5,90],[4,98],[6,100]]),sampleConf==null?.55:Math.min(1,sampleConf)])}}var latency=n(e.latencyMs);if(latency!=null){detail.latencyMs=Math.round(latency);parts.push([.20,curve(latency,[[0,100],[100,100],[250,95],[500,88],[1000,75],[2000,55],[4000,30],[8000,10],[12000,0]]),1])}var seg=n(e.segmentSuccessRatio);if(seg!=null){seg=Math.max(0,Math.min(1,seg));detail.segmentSuccessRatio=seg;parts.push([.20,seg*100,1])}var terminal=n(e.terminalProbeLatencyMs);if(terminal!=null)detail.terminalProbeLatencyMs=Math.round(terminal);parts.push([.10,100,1]);var w=0,t=0,conf=0;for(var i=0;i<parts.length;i++){w+=parts[i][0];t+=parts[i][0]*parts[i][1];conf+=parts[i][0]*parts[i][2]}return{score:t/w,confidence:Math.min(1,conf),detail:detail}}
function reliability(r){var p=(r&&r.providerReliability&&typeof r.providerReliability==="object")?r.providerReliability:{},ratio=n(p.successRatio!=null?p.successRatio:r&&r.providerSuccessRatio);if(ratio==null)return null;ratio=Math.max(0,Math.min(1,ratio));var samples=n(p.sampleCount!=null?p.sampleCount:r&&r.providerSampleCount)||0,age=n(p.evidenceAgeHours!=null?p.evidenceAgeHours:r&&r.providerEvidenceAgeHours)||0,fresh=age<=24?1:age<=72?.85:age<=168?.65:.4;return{score:ratio*100,confidence:Math.min(1,samples/20)*fresh}}
function grade(v){return v>=95?"S+":v>=90?"S":v>=85?"A+":v>=80?"A":v>=70?"B":v>=60?"C":v>=40?"D":"E"}
function badge(g){return{"S+":"stream-score-s-plus",S:"stream-score-s","A+":"stream-score-a-plus",A:"stream-score-a",B:"stream-score-b",C:"stream-score-c",D:"stream-score-d",E:"stream-score-e"}[g]||""}
function scoreRow(r){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),f=r.presentationFacts&&typeof r.presentationFacts==="object"?r.presentationFacts:{},parts=[],breakdown={},v=video(f,r);if(v){parts.push([45,v.score,v.confidence]);breakdown.videoQuality={weight:45,score:Math.round(v.score*10)/10,confidence:Math.round(v.confidence*1000)/1000}}var so=source(f,r);if(so!=null){parts.push([10,so,1]);breakdown.sourceProvenance={weight:10,score:so,confidence:1}}var au=audio(f,r);if(au!=null){parts.push([10,au,1]);breakdown.audioQuality={weight:10,score:Math.round(au*10)/10,confidence:1}}var net=network(r,v&&v.bitrateMbps);if(net){parts.push([30,net.score,net.confidence]);breakdown.playbackNetwork={weight:30,score:Math.round(net.score*10)/10,confidence:Math.round(net.confidence*1000)/1000}}var rel=reliability(r);if(rel){parts.push([5,rel.score,rel.confidence]);breakdown.providerReliability={weight:5,score:Math.round(rel.score*10)/10,confidence:Math.round(rel.confidence*1000)/1000}}try{delete out.__nuvioStreamNetworkEvidenceV1}catch(_e){}var clean=(out.badgeIds||[]).filter(function(x){return !/^stream-score-/.test(String(x||""))});if(!parts.length||!net){out.badgeIds=clean;out.streamScore={schemaVersion:1,status:"insufficient-evidence",score:null,grade:null,confidence:0,breakdown:breakdown};return out}var active=0,total=0,confidence=0;for(var i=0;i<parts.length;i++){active+=parts[i][0];total+=parts[i][0]*parts[i][1];confidence+=parts[i][0]*parts[i][2]}var raw=total/active,overall=Math.min(1,confidence/100),cap=null,hr=n(net.detail.headroomRatio);if(hr!=null&&hr<.9)cap=39;var measuredSeg=n(net.detail.segmentSuccessRatio);if(measuredSeg!=null&&measuredSeg<.8)cap=Math.min(cap==null?100:cap,39);var telemetry=r.playbackMetrics&&typeof r.playbackMetrics==="object"?r.playbackMetrics:{},stalls=n(telemetry.stallCount),stallSeconds=n(telemetry.stallSeconds)||0,seg=n(telemetry.segmentSuccessRatio);if(stalls!=null&&stalls>=3&&stallSeconds>=5)cap=Math.min(cap==null?100:cap,39);if(seg!=null&&seg<.8)cap=Math.min(cap==null?100:cap,39);if(cap!=null)raw=Math.min(raw,cap);var value=Math.round(Math.max(0,Math.min(100,raw))*10)/10,status=overall>=Number(c.minimumConfidence||.6)?"scored":"insufficient-evidence",g=status==="scored"?grade(value):null,id=g?badge(g):"";out.badgeIds=id?[id].concat(clean):clean;out.streamScore={schemaVersion:1,status:status,score:status==="scored"?value:null,grade:g,confidence:Math.round(overall*1000)/1000,breakdown:breakdown,networkEvidence:net.detail,hardCap:cap};return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamScoreV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;return rebuild(v,x,x.list.map(scoreRow))};wrap.__nuvioGlobalStreamScoreV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return replace_managed_fix(text, MANAGED_FIX_ID, wrapper, data=payload)


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
