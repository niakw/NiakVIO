#!/usr/bin/env python3
"""Shared NiakVIO presentation for every reconstructed provider.

Providers expose playback material and factual hints only. This Core layer extracts
technical truth, enriches safe media context from TMDB when available, and builds one
canonical visible presentation for every provider.

Official Nuvio plugin readers do not preserve arbitrary provider result properties:
Mobile/Desktop rebuild their subtitle from quality + size + language, while NuvioTV
uses size as the plugin stream description and appends quality to labels. V12 therefore
preserves normalized ``quality`` for official Nuvio labels/sorting and mirrors the
remaining canonical multiline details into ``size``. ``language`` is transported inside
that envelope to avoid duplicate client formatting. This is a client-compatibility
projection, not a provider-specific presentation fork.

The same canonical text contains stable matcher tokens for Nuvio StreamBadge rules.
When badge rules are not imported/enabled in Nuvio, the emoji-grouped text remains the
universal visual fallback. Unknown technical provenance is never invented.
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
REVISION = "all-providers-client-projected-quality-preserved-badge-emoji-tmdb-v12"


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
    payload = {
        "providerId": str(context.get("provider_id") or "").strip().casefold(),
        "tmdbKey": str(cfg.get("tmdb_key") or TMDB_KEY),
        "tmdbTimeoutMs": max(350, min(int(cfg.get("tmdb_timeout_ms", 1200)), 2500)),
        "implementationRevision": REVISION,
        "clientProjection": "quality-preserved;size-multiline-envelope;language-suppressed",
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
function first(){for(var i=0;i<arguments.length;i++)if(meaningful(arguments[i]))return s(arguments[i]);return""}
function uniq(a){var o=[];(a||[]).forEach(function(v){v=s(v);if(v&&o.indexOf(v)<0)o.push(v)});return o}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var f=a[0],q=f&&typeof f==="object"&&!Array.isArray(f)?Object.assign({},f):{tmdbId:f,mediaType:a[1],season:a[2],episode:a[3]};q.tmdbId=s(q.tmdbId||q.tmdb_id||q.id||f).replace(/^tmdb:/i,"").split(":")[0];q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function urlText(r){var v=r&&r.url;if(v&&typeof v==="object")v=v.url||v.href||v.src;return first(v,r&&r.streamUrl,r&&r.stream,r&&r.link,r&&r.file)}
function blob(r){var bh=r&&r.behaviorHints,ph=bh&&bh.proxyHeaders;return [r&&r.name,r&&r.title,r&&r.size,r&&r.description,r&&r.quality,r&&r.resolution,r&&r.qualityLabel,r&&r.language,r&&r.lang,r&&r.audioLanguage,r&&r.codec,r&&r.videoCodec,r&&r.video_codec,r&&r.audio,r&&r.audioCodec,r&&r.audio_codec,r&&r.sourceType,r&&r.source_type,r&&r.releaseType,r&&r.release_type,r&&r.format,r&&r.hdr,r&&r.videoTech,r&&r.bitDepth,r&&r.subtitles,r&&r.sourceLabel,r&&r.source_name,r&&r.sourceName,r&&r.label,r&&r.filename,r&&r.fileName,r&&r.releaseName,r&&r.release_name,bh&&bh.filename,ph&&ph.filename].map(s).join(" ")}
function quality(r){var direct=first(r&&r.quality,r&&r.resolution,r&&r.qualityLabel),v=direct||blob(r),u=v.toUpperCase();if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":direct}
function language(r){var direct=first(r&&r.language,r&&r.lang,r&&r.audioLanguage),u=(direct||blob(r)).toUpperCase();if(/\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(u))return"Multi";if(/\bDUAL(?:[- ]?AUDIO)?\b/.test(u))return"Multi";if(/\bVOSTFR\b/.test(u))return"VOSTFR";if(/\bVFQ\b/.test(u))return"VFQ";if(/\bVFF\b/.test(u))return"VFF";if(/\bVF\b/.test(u))return"VF";if(/\bVO\b/.test(u))return"VO";return direct}
function codec(r){var direct=first(r&&r.codec,r&&r.videoCodec,r&&r.video_codec),u=(direct||blob(r)).toUpperCase();if(/\b(?:HEVC|H[ ._-]?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H[ ._-]?264|X264)\b/.test(u))return"AVC";return direct}
function audioFacts(r){var direct=first(r&&r.audio,r&&r.audioCodec,r&&r.audio_codec),u=(direct+" "+blob(r)).toUpperCase(),tech=[],codec="",ch="",cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0|1\.0)\b/);if(cm)ch=cm[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))tech.push("Dolby Atmos");if(/\bDTS[: ._-]?X\b/.test(u))tech.push("DTS:X");if(/\bTRUE[ ._-]?HD\b/.test(u))codec="TrueHD";else if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))codec="E-AC3";else if(/\bAC-?3\b/.test(u))codec="AC3";else if(/\bDTS[- ]?HD\b/.test(u))codec="DTS-HD";else if(/\bDTS\b/.test(u))codec="DTS";else if(/\bAAC\b/.test(u))codec="AAC";else if(/\bFLAC\b/.test(u))codec="FLAC";else if(/\bOPUS\b/.test(u))codec="Opus";else if(direct&&!tech.length)codec=direct;return{tech:uniq(tech),codec:codec,channels:ch}}
function duration(r){var raw=(r&&(r.duration??r.durationMinutes??r.duration_minutes??r.runtime));if(typeof raw==="number"&&Number.isFinite(raw)&&raw>0)return raw>600?Math.round(raw/60):Math.round(raw);var d=s(raw),hm=d.match(/(?:(\d+)\s*h)?\s*(?:(\d+)\s*(?:min|m))?/i);if(hm&&(hm[1]||hm[2]))return Number(hm[1]||0)*60+Number(hm[2]||0);var x=blob(r).match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function source(r){var directSource=first(r&&r.sourceType,r&&r.source_type),directRelease=first(r&&r.releaseType,r&&r.release_type),u=(directSource+" "+directRelease+" "+blob(r)).toUpperCase(),sourceType="",releaseType="";if(/\b(?:ULTRA[ ._-]?HD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BLU[ ._-]?RAY|UHD[ ._-]?BD)\b/.test(u))sourceType="ULTRA HD BLU-RAY";else if(/\b(?:BLU[- ]?RAY|BLURAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))sourceType="BLU-RAY";else if(/\bWEB[- .]?DL\b/.test(u))sourceType="WEB-DL";else if(/\bWEB[- .]?RIP\b/.test(u))sourceType="WEBRIP";else if(/\bHDTV\b/.test(u))sourceType="HDTV";else if(/\bDVD[- .]?RIP\b/.test(u))sourceType="DVD RIP";else if(/\bCAM\b|\bTELESYNC\b/.test(u))sourceType="CAM";if(/\bREMUX\b/.test(u))releaseType="REMUX";return{sourceType:sourceType||directSource,releaseType:releaseType||directRelease}}
function formatType(r){var v=first(r&&r.format,r&&r.container),u=v.toUpperCase();if(/(?:M3U8|HLS)/.test(u))return"HLS";if(/(?:MPD|DASH)/.test(u))return"DASH";if(/\bMP4\b/.test(u))return"MP4";if(/\bMKV\b|MATROSKA/.test(u))return"MKV";if(/\bWEBM\b/.test(u))return"WEBM";var url=urlText(r).split(/[?#]/)[0].toLowerCase();if(/\.m3u8$/.test(url))return"HLS";if(/\.mpd$/.test(url))return"DASH";if(/\.mp4$|\.m4v$/.test(url))return"MP4";if(/\.mkv$/.test(url))return"MKV";if(/\.webm$/.test(url))return"WEBM";return v}
function videoFacts(r){var u=blob(r).toUpperCase(),tech=[],bit="";if(/\b(?:DOLBY VISION|DOVI)\b/.test(u))tech.push("Dolby Vision");if(/\bHDR10\+\b|\bHDR10 PLUS\b/.test(u))tech.push("HDR10+");else if(/\bHDR10\b/.test(u))tech.push("HDR10");else if(/\bHDR\b/.test(u))tech.push("HDR");if(/\bIMAX[ ._-]?ENHANCED\b/.test(u))tech.push("IMAX Enhanced");else if(/\bIMAX\b/.test(u))tech.push("IMAX");if(/\b10[ ._-]?BIT\b|\bHI10P\b/.test(u))bit="10bit";else if(/\b8[ ._-]?BIT\b/.test(u))bit="8bit";return{tech:uniq(tech),bitDepth:bit}}
function subtitleFacts(r){var u=blob(r).toUpperCase(),out=[];if(/\bVOSTFR\b/.test(u))out.push("VOSTFR");if(/\bSUB[ ._-]?FR\b/.test(u))out.push("SUB FR");if(/\bSUB[ ._-]?EN\b/.test(u))out.push("SUB EN");if(/\bFORCED\b/.test(u))out.push("FORCED");if(/\bSDH\b/.test(u))out.push("SDH");return uniq(out)}
function age(r){var v=first(r&&r.ageRating,r&&r.age_rating,r&&r.certification);return v}
function providerName(r){var id=s(c.providerId).replace(/[-_]+/g," ");if(id)return id.replace(/\b\w/g,function(x){return x.toUpperCase()});var raw=first(r&&r.provider);return raw&&raw.length<=48?raw:"Source"}
function fileSize(r){var values=[r&&r.fileSize,r&&r.filesize,r&&r.size];for(var i=0;i<values.length;i++){var v=s(values[i]),m=v.match(/\b\d+(?:[.,]\d+)?\s*(?:KB|MB|GB|TB)\b/i);if(m)return m[0].replace(/\s+/g," ").trim()}return""}
function badgeIds(f){var ids=[],q={"2160p":"4k-ultra-hd","1080p":"1080p-full-hd","720p":"720p-hd","480p":"480p-sd"}[f.quality];if(q)ids.push(q);var src={"ULTRA HD BLU-RAY":"uhd-blu-ray","BLU-RAY":"blu-ray-disc","WEB-DL":"webdl","WEBRIP":"webrip","HDTV":"hdtv","DVD RIP":"dvd-rip"}[f.sourceType];if(src)ids.push(src);if(f.releaseType==="REMUX")ids.push("remux");f.videoTech.forEach(function(v){var id={"Dolby Vision":"dolby-vision","HDR10+":"hdr10-plus","HDR10":"hdr10","HDR":"hdr","IMAX Enhanced":"imax-enhanced","IMAX":"imax"}[v];if(id)ids.push(id)});var co={"HEVC":"hevc","AVC":"avc","AV1":"av1","VP9":"vp9"}[f.codec];if(co)ids.push(co);if(f.bitDepth)ids.push(f.bitDepth);(f.audioTech||[]).forEach(function(v){var id={"Dolby Atmos":"dolby-atmos","DTS:X":"dts-x"}[v];if(id)ids.push(id)});var ac={"TrueHD":"truehd","E-AC3":"dolby-digital-plus","AC3":"dolby-digital","DTS-HD":"dts-hd-master-audio","AAC":"aac","FLAC":"flac"}[f.audioCodec];if(ac)ids.push(ac);if(f.audioChannels==="7.1")ids.push("7.1");else if(f.audioChannels==="5.1")ids.push("5.1");var lg={"Multi":"multi","Dual Audio":"multi","VFF":"vff","VF":"vf","VFQ":"vfq","VO":"vo","VOSTFR":"vostfr"}[f.language];if(lg)ids.push(lg);f.subtitles.forEach(function(v){var id={"VOSTFR":"vostfr","SUB FR":"sub-fr","SUB EN":"sub-en","FORCED":"forced","SDH":"sdh-cc"}[v];if(id)ids.push(id)});return uniq(ids)}
function badgeLabels(f){var out=[];if(f.quality)out.push(f.quality==="2160p"?"4K":f.quality);if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);out=out.concat(f.audioTech||[]);if(f.audioCodec)out.push(f.audioCodec);if(f.audioChannels)out.push(f.audioChannels);if(f.language)out.push(f.language);out=out.concat(f.subtitles);if(f.duration)out.push(humanDuration(f.duration));if(f.ageRating)out.push(f.ageRating);return uniq(out)}
function humanDuration(v){v=Number(v)||0;if(v<=0)return"";var h=Math.floor(v/60),m=v%60;return h?h+"h"+String(m).padStart(2,"0"):v+"min"}
function brief(v){var x=s(v).replace(/\s+/g," ");return x.length>180?x.slice(0,177).replace(/\s+\S*$/,"")+"…":x}
function technicalLines(f,fs,includeQuality){var lines=[],video=[],audio=[],lang=[],misc=[];if(includeQuality&&f.quality)video.push(f.quality);var src=f.sourceType+(f.releaseType?" "+f.releaseType:"");if(src)video.push(src);if(f.codec)video.push(f.codec+(f.bitDepth?" "+f.bitDepth:""));else if(f.bitDepth)video.push(f.bitDepth);video=video.concat(f.videoTech||[]);if(f.format)video.push(f.format);if(video.length)lines.push("🎞️ "+uniq(video).join(" • "));audio=audio.concat(f.audioTech||[]);if(f.audioCodec)audio.push(f.audioCodec);if(f.audioChannels)audio.push(f.audioChannels);if(audio.length)lines.push("🔊 "+uniq(audio).join(" • "));if(f.language)lang.push(f.language);(f.subtitles||[]).forEach(function(v){if(v&&lang.indexOf(v)<0)lang.push(v)});if(lang.length)lines.push("🌐 "+lang.join(" • "));if(f.duration)misc.push("⏱ "+humanDuration(f.duration));if(fs)misc.push("💾 "+fs);if(f.ageRating)misc.push("🔞 "+f.ageRating);if(misc.length)lines.push(misc.join(" • "));return lines}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function safeSignal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
function certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}
async function tmdbJson(url){if(!g||typeof g.fetch!=="function")return null;var nativeBridge=nativeFetchBridge(),sig=nativeBridge?null:safeSignal();if(!nativeBridge&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){if(!/^\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",append=kind==="movie"?"release_dates":"content_ratings",base="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId),d=await tmdbJson(base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response="+append);if(!d)return null;var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);var genres=Array.isArray(d.genres)?d.genres.map(function(x){return s(x&&x.name)}).filter(Boolean):[];var meta={title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind),overview:s(d.overview),genres:genres,episodeTitle:"",episodeOverview:""};if(kind==="tv"&&q.season>0&&q.episode>0){var ep=await tmdbJson(base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR");if(ep){var er=Number(ep.runtime||0);if(er>0)meta.runtime=Math.round(er);meta.episodeTitle=s(ep.name);meta.episodeOverview=s(ep.overview)}}return meta}
function mediaLine(meta,q){var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0)){parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));if(meta&&meta.episodeTitle)parts.push(meta.episodeTitle)}return parts.join(" • ")}
function compact(meta,q){var title=s((meta&&meta.title)||q.title),parts=[];if(title)parts.push(title);if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0))parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));return parts.join(" • ")}
function present(r,meta,q){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),au=audioFacts(r),so=source(r),vf=videoFacts(r),fs=fileSize(r),f={quality:quality(r),language:language(r),codec:codec(r),audioTech:au.tech,audioCodec:au.codec,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||"",fileSize:fs};f.subtitles=f.subtitles.filter(function(v){return v!==f.language});if(f.quality)out.quality=f.quality;else if("quality" in out)delete out.quality;if("language" in out)delete out.language;if(f.codec)out.codec=f.codec;var audioCombined=uniq((f.audioTech||[]).concat([f.audioCodec,f.audioChannels].filter(Boolean))).join(" ");if(audioCombined)out.audio=audioCombined;if(f.duration)out.duration=f.duration;if(f.sourceType)out.sourceType=f.sourceType;if(f.releaseType)out.releaseType=f.releaseType;if(f.format)out.format=f.format;if(f.ageRating)out.ageRating=f.ageRating;if(fs)out.fileSize=fs;out.badgeIds=badgeIds(f);out.displayBadges=badgeLabels(f);out.presentationFacts=f;var provider=providerName(r),media=mediaLine(meta,q),small=compact(meta,q),genres=meta&&Array.isArray(meta.genres)&&meta.genres.length?meta.genres.slice(0,3).join(", "):"",mediaText=media?(((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"📺 ":"🎬 ")+media+(genres?" • "+genres:"")):"",canonical=[],compat=[];if(mediaText){canonical.push(mediaText);compat.push(mediaText)}canonical=canonical.concat(technicalLines(f,fs,true));compat=compat.concat(technicalLines(f,fs,false));if(!canonical.length&&meta&&meta.overview)canonical.push("ℹ️ "+brief(meta.overview));if(!compat.length&&meta&&meta.overview)compat.push("ℹ️ "+brief(meta.overview));if(!canonical.length)canonical.push("🎬 "+provider);if(!compat.length)compat.push("🎬 "+provider);var visible=canonical.join("\n"),envelope=compat.join("\n");out.title=small?provider+" • "+small:provider;out.name=provider;out.description=visible;out.size=envelope;out.nuvioPresentation=visible;out.nuvioCompatibilityEnvelope=envelope;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamPresentationV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await tmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(r){return present(r,meta,q)}))};wrap.__nuvioGlobalStreamPresentationV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + wrapper.lstrip()
