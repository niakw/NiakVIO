#!/usr/bin/env python3
"""Shared NiakVIO stream presentation for every reconstructed provider.

Provider rows contribute technical facts only. Core enriches safe media context from
TMDB, keeps quality in the stream title, and owns the final four-line description:
media identity, duration/age, language, then remaining technical facts. Playback URL,
headers and opaque provider attributes are copied through untouched.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

MARKER = "NUVIO_GLOBAL_STREAM_PRESENTATION_V1"
TMDB_KEY = "1865f43a0549ca50d341dd9ab8b29f49"
FACTS_PATH = Path(__file__).with_name("global_stream_facts_v1.py")
IDENTITY_PATH = Path(__file__).with_name("global_stream_identity_v1.py")
PROVIDER_CATALOG_PATH = Path(__file__).resolve().parents[2] / "provider_catalog.json"
REVISION = "all-providers-title-quality-ordered-description-native-tmdb-fail-open-v15-jvm-json-utf8"


def _apply_module(path: Path, module_name: str, text: str, context: dict[str, Any]) -> str:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply(text, context=context)


def _apply_facts(text: str, context: dict[str, Any]) -> str:
    return _apply_module(FACTS_PATH, "nuvio_global_stream_facts_v1", text, context)


def _apply_identity(text: str, context: dict[str, Any]) -> str:
    return _apply_module(IDENTITY_PATH, "nuvio_global_stream_identity_v1", text, context)


def _provider_language_profile(provider_id: str) -> dict[str, str]:
    normalized = str(provider_id or "").strip().casefold()
    if not normalized:
        return {"mode": "vo", "fallback": "VO"}
    try:
        payload = json.loads(PROVIDER_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"mode": "vo", "fallback": "VO"}
    for entry in payload.get("providers") or []:
        if not isinstance(entry, dict):
            continue
        scraper = entry.get("scraper") if isinstance(entry.get("scraper"), dict) else {}
        ids = {
            str(entry.get("canonicalId") or "").strip().casefold(),
            str(scraper.get("id") or "").strip().casefold(),
        }
        if normalized not in ids:
            continue
        languages = {
            str(value or "").strip().casefold()
            for value in (scraper.get("contentLanguage") or [])
            if str(value or "").strip()
        }
        projections = entry.get("projections") if isinstance(entry.get("projections"), dict) else {}
        vf = projections.get("vf") is True or "fr" in languages
        return {"mode": "vf" if vf else "vo", "fallback": "VF" if vf else "VO"}
    return {"mode": "vo", "fallback": "VO"}


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
    text = _apply_facts(text, context)
    text = _apply_identity(text, context)
    cfg = dict(options or {})
    provider_id = str(context.get("provider_id") or "").strip().casefold()
    language_profile = _provider_language_profile(provider_id)
    payload = {
        "providerId": provider_id,
        "providerLanguageMode": language_profile["mode"],
        "languageFallback": language_profile["fallback"],
        "tmdbKey": str(cfg.get("tmdb_key") or TMDB_KEY),
        "tmdbTimeoutMs": max(350, min(int(cfg.get("tmdb_timeout_ms", 1200)), 2500)),
        "implementationRevision": REVISION,
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
function uniq(a){var o=[];(a||[]).forEach(function(v){if(v&&o.indexOf(v)<0)o.push(v)});return o}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function streamPayload(v){var x=slot(v);if(x&&x.list&&x.list.length){var r=x.list[0];return !!(r&&typeof r==="object"&&(typeof r.url==="string"||r.url&&typeof r.url==="object"))}return false}
function asciiJson(v){var out="",n;for(var i=0;i<v.length;i++){n=v.charCodeAt(i);out+=n>127?"\\u"+("0000"+n.toString(16)).slice(-4):v.charAt(i)}return out}
function installJvmSafeStreamStringify(){try{var j=g&&g.JSON?g.JSON:(typeof JSON!=="undefined"?JSON:null);if(!j||typeof j.stringify!=="function"||j.stringify.__nuvioJvmSafeStreamStringify)return;var native=j.stringify;var wrapped=function(value,replacer,space){var raw=native.call(j,value,replacer,space);return typeof raw==="string"&&streamPayload(value)?asciiJson(raw):raw};wrapped.__nuvioJvmSafeStreamStringify=true;wrapped.__nuvioOriginal=native;j.stringify=wrapped}catch(_e){}}
function req(a){var f=a[0],q=f&&typeof f==="object"&&!Array.isArray(f)?Object.assign({},f):{tmdbId:f,mediaType:a[1],season:a[2],episode:a[3]};q.tmdbId=s(q.tmdbId||q.id||f).replace(/^tmdb:/i,"").split(":")[0];q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function blob(r){return [r&&r.name,r&&r.title,r&&r.size,r&&r.description,r&&r.quality,r&&r.language,r&&r.codec,r&&r.audio,r&&r.sourceType,r&&r.releaseType,r&&r.format,r&&r.hdr,r&&r.videoTech,r&&r.bitDepth,r&&r.subtitles,r&&r.sourceLabel,r&&r.filename,r&&r.edition,r&&r.releaseGroup,r&&r.release_group,r&&r.bitrate,r&&r.container,r&&r.encode,r&&r.indexer,r&&r.network].map(s).join(" ")}
function quality(r){var v=meaningful(r&&r.quality)?s(r.quality):blob(r),u=v.toUpperCase();if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":""}
function language(r){var explicit=meaningful(r&&r.language)?s(r.language):"",all=blob(r),u=explicit.toUpperCase(),a=all.toUpperCase(),vfMode=s(c.providerLanguageMode).toLowerCase()==="vf";function isMulti(x){return /\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(x)||/\bDUAL(?:[- ]?AUDIO)?\b/.test(x)}function isVost(x){return /\bVOSTFR\b/.test(x)||/\bVOST[ ._-]?FR\b/.test(x)||/\bVO[ ._-]?ST[ ._-]?FR\b/.test(x)}function isVfq(x){return /\bVFQ\b/.test(x)||/\bFR[ ._-]?CA\b/.test(x)||/\bFRENCH[ ._-]?(?:CANADA|CANADIAN|QUEBEC)\b/.test(x)||/\b(?:QUEBEC|QU[ÉE]B[ÉE]COIS)\b/.test(x)}function isVf(x){return /\b(?:VF|VFF|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR[ ._-]?FR)\b/.test(x)}function isVo(x){return /\bVO\b/.test(x)||/\bORIGINAL(?:[ ._-]?(?:AUDIO|LANG(?:UAGE)?))?\b/.test(x)||/\b(?:EN|ENG|ENGLISH)\b/.test(x)}var hasVost=isVost(a),hasVf=isVf(a)||isVfq(a);if(isMulti(u)||isMulti(a)||(hasVost&&hasVf))return vfMode?"MULTI (VF/VO)":"MULTI";if(isVost(u))return"VOSTFR";if(isVfq(u))return"VFQ";if(isVf(u))return"VF";if(isVo(u))return"VO";if(!u){if(hasVost)return"VOSTFR";if(hasVf)return"VF";if(isVo(a))return"VO"}return s(c.languageFallback)||(vfMode?"VF":"VO")}
function codec(r){var v=meaningful(r&&r.codec)?s(r.codec):blob(r),u=v.toUpperCase();if(/\b(?:HEVC|H[ ._-]?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H[ ._-]?264|X264)\b/.test(u))return"AVC";return meaningful(r&&r.codec)?s(r.codec):""}
function audioFacts(r){var u=(s(r&&r.audio)+" "+blob(r)).toUpperCase(),tech=[],codec="",ch="",cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0|1\.0)\b/);if(cm)ch=cm[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))tech.push("Dolby Atmos");if(/\bDTS[: ._-]?X\b/.test(u))tech.push("DTS:X");if(/\bTRUE[ ._-]?HD\b/.test(u))codec="TrueHD";else if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))codec="E-AC3";else if(/\bAC-?3\b/.test(u))codec="AC3";else if(/\bDTS[- ]?HD\b/.test(u))codec="DTS-HD";else if(/\bDTS\b/.test(u))codec="DTS";else if(/\bAAC\b/.test(u))codec="AAC";else if(/\bFLAC\b/.test(u))codec="FLAC";else if(/\bOPUS\b/.test(u))codec="Opus";else if(meaningful(r&&r.audio)&&!tech.length)codec=s(r.audio);return{tech:uniq(tech),codec:codec,channels:ch}}
function duration(r){var raw=r&&r.duration;if(typeof raw==="number"&&Number.isFinite(raw)&&raw>0)return raw>600?Math.round(raw/60):Math.round(raw);var d=s(raw),h=d.match(/(\d{1,2})\s*h(?:eures?)?\s*(\d{1,2})?/i);if(h)return Number(h[1])*60+Number(h[2]||0);var m=d.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var x=blob(r).match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function source(r){var raw=(s(r&&r.sourceType)+" "+s(r&&r.releaseType)+" "+blob(r)),u=raw.toUpperCase(),sourceType="",releaseType="";if(/\b(?:ULTRA[ ._-]?HD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BD)\b/.test(u))sourceType="ULTRA HD BLU-RAY";else if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))sourceType="BLU-RAY";else if(/\bWEB[- .]?DL\b/.test(u))sourceType="WEB-DL";else if(/\bWEB[- .]?RIP\b/.test(u))sourceType="WEBRIP";else if(/\bHDTV\b/.test(u))sourceType="HDTV";else if(/\bDVD[- .]?RIP\b/.test(u))sourceType="DVD RIP";if(/\bREMUX\b/.test(u))releaseType="REMUX";return{sourceType:sourceType||(meaningful(r&&r.sourceType)?s(r.sourceType):""),releaseType:releaseType||(meaningful(r&&r.releaseType)?s(r.releaseType):"")}}
function formatType(r){var v=meaningful(r&&r.format)?s(r.format):"",u=v.toUpperCase();if(/(?:M3U8|HLS)/.test(u))return"HLS";if(/(?:MPD|DASH)/.test(u))return"DASH";if(/\bMP4\b/.test(u))return"MP4";if(/\bMKV\b/.test(u))return"MKV";var url=s(r&&r.url).split(/[?#]/)[0].toLowerCase();if(/\.m3u8$/.test(url))return"HLS";if(/\.mpd$/.test(url))return"DASH";if(/\.mp4$/.test(url))return"MP4";if(/\.mkv$/.test(url))return"MKV";return v}
function videoFacts(r){var u=blob(r).toUpperCase(),tech=[],bit="";if(/\b(?:DOLBY VISION|DOVI)\b/.test(u))tech.push("Dolby Vision");if(/\bHDR10\+\b|\bHDR10 PLUS\b/.test(u))tech.push("HDR10+");else if(/\bHDR10\b/.test(u))tech.push("HDR10");else if(/\bHDR\b/.test(u))tech.push("HDR");if(/\bIMAX[ ._-]?ENHANCED\b/.test(u))tech.push("IMAX Enhanced");else if(/\bIMAX\b/.test(u))tech.push("IMAX");if(/\b10[ ._-]?BIT\b|\bHI10P\b/.test(u))bit="10bit";else if(/\b8[ ._-]?BIT\b/.test(u))bit="8bit";return{tech:uniq(tech),bitDepth:bit}}
function subtitleFacts(r){var u=blob(r).toUpperCase(),out=[];if(/\bVOSTFR\b/.test(u))out.push("VOSTFR");if(/\bSUB[ ._-]?FR\b/.test(u))out.push("SUB FR");if(/\bSUB[ ._-]?EN\b/.test(u))out.push("SUB EN");if(/\bFORCED\b/.test(u))out.push("FORCED");if(/\bSDH\b/.test(u))out.push("SDH");return uniq(out)}
function age(r){var v=r&&(r.ageRating||r.certification||r.contentRating);return meaningful(v)?s(v):""}
function providerName(r){var raw=meaningful(r&&r.name)?s(r.name):"",n=raw.split(/[|\n]/)[0].trim(),u=n.toUpperCase(),looksTechnical=/(?:\b4K\b|\b(?:2160|1440|1080|720|576|480)P?\b|\b(?:VF|VFF|VFQ|VOSTFR|VO|MULTI|DUAL[ -]?AUDIO)\b|\b(?:HEVC|AVC|H[ ._-]?26[45]|X26[45]|AV1|VP9)\b|\b(?:WEB[ ._-]?DL|WEB[ ._-]?RIP|BLU[ ._-]?RAY|REMUX|HDR|DOLBY|DTS)\b)/.test(u);if(n&&n.length<=40&&!looksTechnical)return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\b\w/g,function(x){return x.toUpperCase()}):"Source"}
function fileSize(r){var v=s(r&&r.size);if(!meaningful(v))return"";var m=v.match(/\b\d+(?:[.,]\d+)?\s*(?:KB|MB|GB|TB)\b/i);return m?m[0]:""}
function qualityLabel(v){return v==="2160p"?"4K":s(v)}
function badgeIds(f){var ids=[];var q={"2160p":"4k-ultra-hd","1080p":"1080p-full-hd","720p":"720p-hd","480p":"480p-sd"}[f.quality];if(q)ids.push(q);var src={"ULTRA HD BLU-RAY":"uhd-blu-ray","BLU-RAY":"blu-ray-disc","WEB-DL":"webdl","WEBRIP":"webrip","HDTV":"hdtv","DVD RIP":"dvd-rip"}[f.sourceType];if(src)ids.push(src);if(f.releaseType==="REMUX")ids.push("remux");f.videoTech.forEach(function(v){var id={"Dolby Vision":"dolby-vision","HDR10+":"hdr10-plus","HDR10":"hdr10","IMAX Enhanced":"imax-enhanced","IMAX":"imax"}[v];if(id)ids.push(id)});var co={"HEVC":"hevc","AVC":"avc"}[f.codec];if(co)ids.push(co);if(f.bitDepth)ids.push(f.bitDepth);(f.audioTech||[]).forEach(function(v){var id={"Dolby Atmos":"dolby-atmos","DTS:X":"dts-x"}[v];if(id)ids.push(id)});var ac={"TrueHD":"truehd","E-AC3":"dolby-digital-plus","AC3":"dolby-digital","DTS-HD":"dts-hd-master-audio"}[f.audioCodec];if(ac)ids.push(ac);if(f.audioChannels==="7.1")ids.push("7.1");else if(f.audioChannels==="5.1")ids.push("5.1");var lg={"MULTI (VF/VO)":"multi","MULTI":"multi","VF":"vf","VFQ":"vfq","VO":"vo","VOSTFR":"vostfr"}[f.language];if(lg)ids.push(lg);(f.subtitles||[]).forEach(function(v){var id={"VOSTFR":"vostfr","SUB FR":"sub-fr","SUB EN":"sub-en","FORCED":"forced","SDH":"sdh-cc"}[v];if(id)ids.push(id)});return uniq(ids)}
function badgeLabels(f){var out=[];if(f.quality)out.push(qualityLabel(f.quality));if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);out=out.concat(f.audioTech||[]);if(f.audioCodec)out.push(f.audioCodec);if(f.audioChannels)out.push(f.audioChannels);if(f.language)out.push(f.language);if(f.duration)out.push(humanDuration(f.duration));if(f.ageRating)out.push(f.ageRating);return uniq(out)}
function humanDuration(v){v=Number(v)||0;if(v<=0)return"";var h=Math.floor(v/60),m=v%60;return h?h+"h"+String(m).padStart(2,"0"):v+"min"}
function technicalLine(f,fs){var groups=[],video=[],audio=[],misc=[],src=f.sourceType+(f.releaseType?" "+f.releaseType:"");if(src)video.push(src);if(f.edition)video.push(f.edition);if(f.codec)video.push(f.codec+(f.bitDepth?" "+f.bitDepth:""));else if(f.bitDepth)video.push(f.bitDepth);video=video.concat(f.videoTech||[]);if(f.format)video.push(f.format);if(video.length)groups.push("🎞️ "+uniq(video).join(" • "));audio=audio.concat(f.audioTech||[]);if(f.audioCodec)audio.push(f.audioCodec);if(f.audioChannels)audio.push(f.audioChannels);if(audio.length)groups.push("🔊 "+uniq(audio).join(" • "));if(fs)misc.push("💾 "+fs);if(f.bitrate)misc.push("📶 "+f.bitrate);if(f.releaseGroup)misc.push("🏷️ "+f.releaseGroup);if(misc.length)groups.push(misc.join(" • "));return groups.join("  |  ")}
function durationAgeLine(f){var out=[];if(f.duration)out.push("⏱ "+humanDuration(f.duration));if(f.ageRating)out.push("🔞 "+f.ageRating);return out.join(" • ")}
function languageLine(f){if(!f.language)return"";var prefix=(f.language==="VF"||f.language==="VFQ"||f.language==="MULTI (VF/VO)")?"🇫🇷 ":(f.language==="VOSTFR"?"🌐🇫🇷 ":"🌐 ");var subs=(f.subtitles||[]).filter(function(v){return v&&v!=="VOSTFR"});return prefix+f.language+(subs.length?" • 💬 "+subs.join(" • "):"")}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function runtimeTmdbAllowed(){try{return !nativeFetchBridge()||!!s(g&&g.TMDB_API_KEY)}catch(_e){return !nativeFetchBridge()}}
function safeSignal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
function certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}
async function tmdbJson(url){if(!g||typeof g.fetch!=="function"||!runtimeTmdbAllowed())return null;var nativeBridge=nativeFetchBridge(),sig=nativeBridge?null:safeSignal();if(!nativeBridge&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){if(!/^\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",append=kind==="movie"?"release_dates":"content_ratings",base="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId),d=await tmdbJson(base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response="+append);if(!d)return null;var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);var meta={title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind)};if(kind==="tv"&&q.season>0&&q.episode>0){var ep=await tmdbJson(base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR");if(ep){var er=Number(ep.runtime||0);if(er>0)meta.runtime=Math.round(er)}}return meta}
function mediaLine(meta,q){var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0))parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));return parts.join(" • ")}
function tvDescriptionTunnel(){try{return !!(g&&meaningful(g.TMDB_API_KEY)&&meaningful(g.SCRAPER_ID))}catch(_e){return false}}
function present(r,meta,q){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),au=audioFacts(r),so=source(r),vf=videoFacts(r),f={quality:quality(r),language:language(r),codec:codec(r),audioTech:au.tech,audioCodec:au.codec,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||"",edition:meaningful(r&&r.edition)?s(r.edition):"",releaseGroup:meaningful(r&&(r.releaseGroup||r.release_group))?s(r.releaseGroup||r.release_group):"",bitrate:meaningful(r&&r.bitrate)?s(r.bitrate):""};if(f.quality)out.quality=f.quality;if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;var audioCombined=uniq((f.audioTech||[]).concat([f.audioCodec,f.audioChannels].filter(Boolean))).join(" ");if(audioCombined)out.audio=audioCombined;if(f.duration)out.duration=f.duration;if(f.sourceType)out.sourceType=f.sourceType;if(f.releaseType)out.releaseType=f.releaseType;if(f.format)out.format=f.format;if(f.ageRating)out.ageRating=f.ageRating;out.badgeIds=badgeIds(f);out.displayBadges=badgeLabels(f);out.presentationFacts=f;var provider=providerName(r),media=mediaLine(meta,q),fs=fileSize(r),technical=technicalLine(f,fs),timing=durationAgeLine(f),lang=languageLine(f),lines=[];if(media)lines.push(((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"📺 ":"🎬 ")+media);if(timing)lines.push(timing);if(lang)lines.push(lang);if(technical)lines.push(technical);out.title=provider+(f.quality?" - "+qualityLabel(f.quality):"");out.name=provider;out.description=lines.join("\n");if(tvDescriptionTunnel()&&out.description)out.size=out.description;else if(fs)out.size=fs;else if("size" in out)delete out.size;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamPresentationV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await tmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(r){return present(r,meta,q)}))};wrap.__nuvioGlobalStreamPresentationV1=true;o[k]=wrap;return true}
installJvmSafeStreamStringify();
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + wrapper.lstrip()
