#!/usr/bin/env python3
"""Materialize the shared NiakVIO stream finalization in isolated provider bundles.

Every provider is responsible only for factual playback output (URL/headers and any
stream facts it really knows). This Core layer is applied to every reconstructed
provider bundle. It normalizes available facts, enriches missing media context from
TMDB when possible, and builds one coherent Nuvio title/description contract.

Provider-specific adapters may expose facts hidden in legacy labels, but they never
own final presentation. TMDB is optional and must never change/drop playback material.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

MARKER = "NUVIO_GLOBAL_STREAM_PRESENTATION_V1"
TMDB_KEY = "1865f43a0549ca50d341dd9ab8b29f49"
IDENTITY_PATH = Path(__file__).with_name("global_stream_identity_v1.py")


def _apply_identity(text: str, context: dict[str, Any]) -> str:
    spec = importlib.util.spec_from_file_location("nuvio_global_stream_identity_v1", IDENTITY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {IDENTITY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply(text, context=context)


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
    # Identity must run before presentation on every provider. It rejects only
    # positive mismatch evidence; generic rows remain untouched.
    text = _apply_identity(text, context)
    provider_id = str(context.get("provider_id") or "").strip().casefold()
    cfg = dict(options or {})
    payload = {
        "providerId": provider_id,
        "tmdbKey": str(cfg.get("tmdb_key") or TMDB_KEY),
        "tmdbTimeoutMs": max(350, min(int(cfg.get("tmdb_timeout_ms", 1200)), 2500)),
        "implementationRevision": "all-providers-tmdb-media-episode-display-v6",
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if f"/* {marker} */" in text:
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
function audio(row){var v=meaningful(row&&row.audio)?s(row.audio):blob(row),u=v.toUpperCase(),ch="",cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(cm)ch=" "+cm[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))return"ATMOS"+ch;if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))return"E-AC3"+ch;if(/\bAC-?3\b/.test(u))return"AC3"+ch;if(/\bDTS(?:-HD)?\b/.test(u))return(/\bDTS-HD\b/.test(u)?"DTS-HD":"DTS")+ch;if(/\bAAC\b/.test(u))return"AAC"+ch;return meaningful(row&&row.audio)?s(row.audio):""}
function duration(row){var raw=row&&row.duration;if(typeof raw==="number"&&Number.isFinite(raw)&&raw>0)return raw>600?Math.round(raw/60):Math.round(raw);var direct=s(raw),m=direct.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var x=blob(row).match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function sourceType(row){var v=meaningful(row&&row.sourceType)?s(row.sourceType):blob(row),u=v.toUpperCase();if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX|REMUX)\b/.test(u))return"BLU-RAY";if(/\bWEB[- .]?DL\b/.test(u))return"WEB-DL";if(/\bWEB[- .]?RIP\b/.test(u))return"WEBRIP";return meaningful(row&&row.sourceType)?s(row.sourceType):""}
function age(row){var v=row&&(row.ageRating||row.certification);return meaningful(v)?s(v):""}
function providerName(row){var n=s(row&&row.name).split(/[|\n]/)[0].trim();if(n&&n.length<=40&&!/^(?:4k|2160p|1080p|720p|vf|vff|vfq|vostfr)$/i.test(n))return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\b\w/g,function(x){return x.toUpperCase()}):"Source"}
function legacyLabel(v){var x=s(v);return x.length>140||/\r|\n/.test(x)||(/🔥|🎯|🎧/.test(x)&&x.length>70)}
function qualityBadge(v){if(v==="2160p")return"【4K】";return v?"【"+v.toUpperCase()+"】":""}
function two(v){return v<10?"0"+v:String(v)}
function fmtDuration(minutes){var n=Number(minutes||0);if(!n)return"";var h=Math.floor(n/60),m=n%60;return h?(h+"h"+(m?two(m):"")):n+"min"}
function unique(list){var out=[];list.forEach(function(v){if(v&&out.indexOf(v)<0)out.push(v)});return out}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function safeSignal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
function certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}
async function tmdbJson(url){if(!g||typeof g.fetch!=="function")return null;var nativeBridge=nativeFetchBridge(),sig=nativeBridge?null:safeSignal();if(!nativeBridge&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){if(!/^\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",append=kind==="movie"?"release_dates":"content_ratings",base="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId),mainUrl=base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response="+append,d=await tmdbJson(mainUrl);if(!d)return null;var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);var meta={title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind),episodeTitle:"",season:q.season||0,episode:q.episode||0};if(kind==="tv"&&q.season>0&&q.episode>0){var episodeUrl=base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR",ep=await tmdbJson(episodeUrl);if(ep){var epRuntime=Number(ep.runtime||0);if(epRuntime>0)meta.runtime=Math.round(epRuntime);meta.episodeTitle=s(ep.name);var epDate=s(ep.air_date),epYear=Number((epDate.match(/(?:19|20)\d{2}/)||[])[0]||0)||0;if(!meta.year&&epYear)meta.year=epYear}}return meta}
function mediaLine(meta,q){var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));var episodic=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0);if(episodic){var se="S"+two(q.season||0)+"E"+two(q.episode||0);parts.push(se);var epTitle=s(meta&&meta.episodeTitle);if(epTitle)parts.push(epTitle)}return parts.join(" • ")}
function present(row,meta,q){if(!row||typeof row!=="object")return row;var out=Object.assign({},row),ql=quality(row),lang=language(row),co=codec(row),au=audio(row),du=duration(row)||(meta&&meta.runtime)||0,src=sourceType(row),ag=age(row)||(meta&&meta.age)||"";if(ql)out.quality=ql;if(lang)out.language=lang;if(co)out.codec=co;if(au)out.audio=au;if(du)out.duration=du;if(src)out.sourceType=src;if(ag)out.ageRating=ag;var badges=unique([qualityBadge(ql),src?"【"+src+"】":"",lang?"🌐 "+lang:"",co?"🎞 "+co:"",au?"🔊 "+au:"",du?"⏱ "+fmtDuration(du):"",ag?"🔞 "+ag:""]);out.displayBadges=badges;var media=mediaLine(meta,q),lines=[];if(badges.length)lines.push(badges.join(" "));if(media)lines.push(media);if(!lines.length)lines.push("🎬 "+providerName(row));out.description=lines.join("\n");out.title=providerName(row);out.name=providerName(row);out.size=badges.length?badges.slice(0,4).join(" "):(media||providerName(row));return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamPresentationV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await tmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(row){return present(row,meta,q)}))};wrap.__nuvioGlobalStreamPresentationV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + wrapper.lstrip()