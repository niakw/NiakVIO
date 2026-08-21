#!/usr/bin/env python3
"""Materialize the shared NiakVIO stream presentation in isolated provider bundles.

Providers remain responsible for factual stream output (URL, headers, language,
quality, codec, audio, duration and explicit source type).  This final Core layer
normalizes those facts and builds one presentation contract for Nuvio clients.
TMDB is a bounded, optional factual fallback for title/year/runtime/age rating;
a TMDB failure never removes a stream and never changes playback URL/headers.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_GLOBAL_STREAM_PRESENTATION_V1"
TMDB_KEY = "1865f43a0549ca50d341dd9ab8b29f49"


def _strip_existing(text: str) -> str:
    start = text.find(f"/* {MARKER}:")
    if start < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global stream presentation wrapper")
    return (text[:start] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
    provider_id = str(context.get("provider_id") or "").strip().casefold()
    cfg = dict(options or {})
    payload = {
        "providerId": provider_id,
        "tmdbKey": str(cfg.get("tmdb_key") or TMDB_KEY),
        "tmdbTimeoutMs": max(350, min(int(cfg.get("tmdb_timeout_ms", 1200)), 2500)),
        "implementationRevision": "facts-first-shared-display-v1",
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    current = text.find(f"/* {marker} */")
    if current >= 0 and not text[current + len(marker) :].strip():
        return text
    text = _strip_existing(text)

    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|none|-+)$/i.test(x)}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]};q.tmdbId=s(q.tmdbId||q.id||first).replace(/^tmdb:/i,"").split(":")[0];q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function blob(row){return [row&&row.name,row&&row.title,row&&row.size,row&&row.description,row&&row.quality,row&&row.language,row&&row.codec,row&&row.audio,row&&row.sourceType].map(s).join(" ")}
function quality(row){var v=meaningful(row&&row.quality)?s(row.quality):blob(row),u=v.toUpperCase();if(/(?:\b4K\b|\b2160P?\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":""}
function language(row){var v=meaningful(row&&row.language)?s(row.language):blob(row),u=v.toUpperCase();if(/\bDUAL(?:[- ]?AUDIO)?\b/.test(u))return"Dual Audio";if(/\bVOSTFR\b/.test(u))return"VOSTFR";if(/\bVFQ\b/.test(u))return"VFQ";if(/\bVFF\b/.test(u))return"VFF";if(/\bVF\b/.test(u))return"VF";if(/\bVO\b/.test(u))return"VO";return meaningful(row&&row.language)?s(row.language):""}
function codec(row){var v=meaningful(row&&row.codec)?s(row.codec):blob(row),u=v.toUpperCase();if(/\b(?:HEVC|H\.?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H\.?264|X264)\b/.test(u))return"H.264";return meaningful(row&&row.codec)?s(row.codec):""}
function audio(row){var v=meaningful(row&&row.audio)?s(row.audio):blob(row),u=v.toUpperCase(),ch="";var cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(cm)ch=" "+cm[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))return"ATMOS"+ch;if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))return"E-AC3"+ch;if(/\bAC-?3\b/.test(u))return"AC3"+ch;if(/\bDTS(?:-HD)?\b/.test(u)){var dm=u.match(/\bDTS-HD\b/);return(dm?"DTS-HD":"DTS")+ch}if(/\bAAC\b/.test(u))return"AAC"+ch;return meaningful(row&&row.audio)?s(row.audio):""}
function duration(row){var raw=row&&row.duration;if(typeof raw==="number"&&Number.isFinite(raw)&&raw>0)return raw>600?Math.round(raw/60):Math.round(raw);var direct=s(raw),m=direct.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var b=blob(row),x=b.match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function sourceType(row){var v=meaningful(row&&row.sourceType)?s(row.sourceType):blob(row),u=v.toUpperCase();if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX|REMUX)\b/.test(u))return"BLU-RAY";if(/\bWEB[- .]?DL\b/.test(u))return"WEB-DL";if(/\bWEB[- .]?RIP\b/.test(u))return"WEBRIP";return meaningful(row&&row.sourceType)?s(row.sourceType):""}
function age(row){var v=row&&(row.ageRating||row.certification);return meaningful(v)?s(v):""}
function providerName(row){var n=s(row&&row.name).split(/[|\n]/)[0].trim();if(n&&n.length<=40&&!/^(?:4k|2160p|1080p|720p|vf|vff|vfq|vostfr)$/i.test(n))return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\b\w/g,function(x){return x.toUpperCase()}):"Source"}
function qualityBadge(v){if(v==="2160p")return"【4K】";return v?"【"+v.toUpperCase()+"】":""}
function fmtDuration(minutes){var n=Number(minutes||0);if(!n)return"";var h=Math.floor(n/60),m=n%60;return h?(h+"h"+(m?String(m).padStart(2,"0"):"")):n+"min"}
function unique(list){var out=[];list.forEach(function(v){if(v&&out.indexOf(v)<0)out.push(v)});return out}
function safeSignal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
function certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}
async function tmdb(q){
  if(!/^\d+$/.test(q.tmdbId||"")||!g||typeof g.fetch!=="function")return null;
  var signal=safeSignal();if(!signal)return null;
  var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie";
  var append=kind==="movie"?"release_dates":"content_ratings";
  var url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response="+append;
  try{var r=await g.fetch(url,{headers:{Accept:"application/json"},signal:signal});if(!r||!r.ok)return null;var d=await r.json(),date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);return{title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind)}}catch(_e){return null}
}
function present(row,meta,q){
  if(!row||typeof row!=="object")return row;
  var out=Object.assign({},row),ql=quality(row),lang=language(row),co=codec(row),au=audio(row),du=duration(row)||(meta&&meta.runtime)||0,src=sourceType(row),ag=age(row)||(meta&&meta.age)||"";
  if(ql)out.quality=ql;if(lang)out.language=lang;if(co)out.codec=co;if(au)out.audio=au;if(du)out.duration=du;if(src)out.sourceType=src;if(ag)out.ageRating=ag;
  var badges=unique([qualityBadge(ql),src?"【"+src+"】":"",lang?"🌐 "+lang:"",co?"🎞 "+co:"",au?"🔊 "+au:"",du?"⏱ "+fmtDuration(du):"",ag?"🔞 "+ag:""]);
  out.displayBadges=badges;
  var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,lines=[];
  if(badges.length)lines.push(badges.join(" "));
  if(title||year)lines.push([title,year?String(year):""].filter(Boolean).join(" • "));
  if(!lines.length)lines.push("🎬 "+providerName(row));
  out.description=lines.join("\n");
  if(!meaningful(out.title))out.title=providerName(row);
  if(!meaningful(out.name))out.name=providerName(row);
  return out;
}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamPresentationV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),metaPromise=tmdb(q),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await metaPromise}catch(_e){}return rebuild(v,x,x.list.map(function(row){return present(row,meta,q)}))};wrap.__nuvioGlobalStreamPresentationV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + wrapper.lstrip()
