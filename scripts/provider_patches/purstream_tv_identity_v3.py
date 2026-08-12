"""Reject Purstream episodic HLS whose real duration contradicts its metadata.

Purstream can return a technically valid HLS with the requested title/episode in
its display metadata while the media itself belongs to another work.  For TV,
series and anime requests, rows that advertise a duration are therefore checked
against the media playlist #EXTINF total.  A large mismatch is fail-closed.
Movies and rows without an advertised duration are left unchanged.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_PURSTREAM_TV_IDENTITY_V3"


def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    tolerance = max(0.15, min(float(cfg.get("duration_tolerance", 0.35)), 0.50))
    timeout_ms = max(2000, min(int(cfg.get("timeout_ms", 7000)), 12000))
    max_probes = max(1, min(int(cfg.get("max_probes", 3)), 5))
    payload = {
        "durationTolerance": tolerance,
        "timeoutMs": timeout_ms,
        "maxProbes": max_probes,
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in source:
        return source

    shim = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function txt(v){return String(v==null?"":v)}
function req(a){var o=a[0]&&typeof a[0]==="object"?a[0]:{};return {type:txt(o.mediaType||o.type||a[1]||"movie").toLowerCase(),season:Number(o.season??a[2]??0)||0,episode:Number(o.episode??a[3]??0)||0}}
function episodic(t){return t==="tv"||t==="series"||t==="anime"}
function expected(row){var blob=[row&&row.name,row&&row.title,row&&row.size,row&&row.description].map(txt).join(" "),re=/\b(\d{1,3})\s*min(?:ute)?s?\b/ig,m,best=0;while((m=re.exec(blob))!==null)best=Math.max(best,Number(m[1])||0);return best?best*60:0}
function hls(row){return /\.m3u8(?:[?#]|$)/i.test(txt(row&&row.url))||txt(row&&row.type).toLowerCase()==="hls"||txt(row&&row.format).toLowerCase()==="m3u8"}
function headers(row){var h={};try{Object.assign(h,row&&row.headers||{},row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request||{})}catch(_e){}if(!h.Accept)h.Accept="*/*";if(!h["User-Agent"])h["User-Agent"]="Mozilla/5.0 (Linux; Android 14; Android TV) NuvioTV";return h}
async function get(url,h){var ctrl=typeof AbortController!=="undefined"?new AbortController():null,timer=null;try{if(ctrl)timer=setTimeout(function(){try{ctrl.abort()}catch(_e){}},c.timeoutMs);var r=await g.fetch(url,{method:"GET",headers:h,redirect:"follow",signal:ctrl?ctrl.signal:void 0});if(!r||!r.ok)return null;var body=await r.text();return {body:txt(body).replace(/^\uFEFF/,"").trimStart(),url:txt(r.url||url)}}catch(_e){return null}finally{if(timer)clearTimeout(timer)}}
function child(master,base){var lines=txt(master).split(/\r?\n/);for(var i=0;i<lines.length;i++){if(!/^#EXT-X-STREAM-INF:/i.test(lines[i].trim()))continue;for(var j=i+1;j<lines.length;j++){var v=lines[j].trim();if(!v)continue;if(v[0]==="#")continue;try{return new URL(v,base).toString()}catch(_e){return ""}}}return ""}
function duration(media){var total=0,count=0,re=/^#EXTINF:([0-9.]+)/i;txt(media).split(/\r?\n/).forEach(function(line){var m=re.exec(line.trim());if(m){total+=Number(m[1])||0;count++}});return count?total:0}
async function prove(row,seconds){var first=await get(txt(row.url),headers(row));if(!first||!/^#EXTM3U/i.test(first.body))return false;var media=first,variant=child(first.body,first.url);if(variant){media=await get(variant,headers(row));if(!media||!/^#EXTM3U/i.test(media.body))return false}var actual=duration(media.body);if(!actual)return false;var ratio=actual/seconds;return ratio>=(1-c.durationTolerance)&&ratio<=(1+c.durationTolerance)}
function rows(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
function rebuild(v,slot,list){if(slot.key===null)return list;var out=Object.assign({},v);out[slot.key]=list;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioPurstreamTvIdentityV3)return false;var native=o[k];var wrap=async function(){var r=req(arguments),v=await native.apply(this,arguments);if(!episodic(r.type))return v;var slot=rows(v);if(!slot)return v;var kept=[],probes=0;for(var i=0;i<slot.list.length;i++){var row=slot.list[i],seconds=expected(row);if(seconds&&hls(row)){if(probes>=c.maxProbes)continue;probes++;if(await prove(row,seconds))kept.push(row);continue}kept.push(row)}return rebuild(v,slot,kept)};wrap.__nuvioPurstreamTvIdentityV3=true;wrap.__nuvioPurstreamTvIdentityOriginal=native;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return source.rstrip() + "\n" + shim.lstrip()
