#!/usr/bin/env python3
"""Conservative cross-client identity guard for final provider stream rows.

This Core layer rejects only rows whose own human-readable title/description or
media filename provides positive evidence for a different work/episode. Generic
server/quality labels remain untouched. The same wrapper is materialized in every
provider bundle, so TV, Mobile and Desktop apply one identity contract.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_GLOBAL_STREAM_IDENTITY_V1"
TMDB_KEY = "1865f43a0549ca50d341dd9ab8b29f49"


def _strip_existing(text: str) -> str:
    start = text.find(f"/* {MARKER}:")
    if start < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global stream identity wrapper")
    return (text[:start] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
    cfg = dict(options or {})
    payload = {
        "providerId": str(context.get("provider_id") or "").strip().casefold(),
        "tmdbKey": str(cfg.get("tmdb_key") or TMDB_KEY),
        "tmdbTimeoutMs": max(350, min(int(cfg.get("tmdb_timeout_ms", 1200)), 2500)),
        "implementationRevision": "cross-client-positive-mismatch-v1",
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text
    text = _strip_existing(text)

    js = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){var x=s(v),k=norm(x);if(x&&k&&!seen[k]){seen[k]=1;out.push(x)}});return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]};var raw=s(q.tmdbId||q.tmdb_id||q.id||first).replace(/^tmdb:/i,"");q.tmdbId=(raw.match(/^\d+/)||[])[0]||"";q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function kind(q){return(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie"}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function signal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
async function tmdb(q){var titles=unique([q.title]),year=q.year;if(!/^\d+$/.test(q.tmdbId||"")||!g||typeof g.fetch!=="function")return{titles:titles,year:year};var nativeBridge=nativeFetchBridge(),sig=nativeBridge?null:signal();if(!nativeBridge&&!sig)return{titles:titles,year:year};var k=kind(q),url="https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR",init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return{titles:titles,year:year};var d=await r.json(),date=s(d.release_date||d.first_air_date);titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));year=year||Number((date.match(/(?:19|20)\d{2}/)||[])[0]||0)||0;return{titles:titles,year:year}}catch(_e){return{titles:titles,year:year}}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,episode:1,season:1,saison:1,stream:1,streaming:1,source:1,server:1,serveur:1,player:1,video:1,watch:1,play:1,direct:1,download:1,quality:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function identityLabel(row){var label=[row&&row.title,row&&row.description,row&&row.filename,row&&row.name].map(s).filter(Boolean).join(" "),base="";try{base=decodeURIComponent(new URL(s(row&&row.url)).pathname.split("/").filter(Boolean).pop()||"").replace(/\.(?:m3u8|mpd|mp4|mkv|webm|m4v|ts)$/i,"")}catch(_e){}var human=tokens(base).filter(function(x){return/^[a-z]{3,}$/i.test(x)});return label+(human.length>=2?" "+base:"")}
function episode(label){return/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label)}
function mismatch(row,q,m){var label=identityLabel(row);if(!label)return false;var se=episode(label);if(q.mediaType==="movie"&&se)return true;if(se&&(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true}var years=norm(label).match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&!years.some(function(y){return Math.abs(Number(y)-Number(m.year))<=1}))return true;var expected={};(m.titles||[]).forEach(function(t){tokens(t).forEach(function(x){expected[x]=1})});var expectedKeys=Object.keys(expected);if(!expectedKeys.length)return false;var tech={vcloud:1,hubcloud:1,file:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vfq:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var provider=tokens(c.providerId),words=tokens(label).filter(function(x){return!tech[x]&&provider.indexOf(x)<0&&!/^\d{3,4}p$/.test(x)});if(words.length<2)return false;for(var i=0;i<words.length;i++)if(expected[words[i]])return false;return true}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamIdentityV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var m=await tmdb(q);if(!m.titles.length)return v;var kept=x.list.filter(function(row){return !mismatch(row,q,m)});return rebuild(v,x,kept)};wrap.__nuvioGlobalStreamIdentityV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + js.lstrip()
