"""Reject StreamZo rows whose catalogue source contradicts the requested work.

Recovered StreamZo rows keep their catalogue/detail page in Referer.  A loose
search can otherwise map e.g. Korean `Revenant` (2023) to French `Les Revenants`
(2015) and then relabel the returned media with the requested title.  This guard
checks same-origin detail-page slugs against TMDB/request title tokens and year.
Embed/player referers are intentionally exempt because they do not encode title.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_STREAMZO_SOURCE_IDENTITY_V2"


def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    base_url = str(cfg.get("base_url") or "https://streamzo.fr").rstrip("/")
    timeout_ms = max(1500, min(int(cfg.get("timeout_ms", 6500)), 10000))
    payload = {"baseUrl": base_url, "timeoutMs": timeout_ms}
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in source:
        return source

    shim = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,et:1,and:1,serie:1,series:1,tv:1,film:1,movie:1,streaming:1,watch:1,backtrack:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function req(a){var o=a[0]&&typeof a[0]==="object"?a[0]:{};return {id:s(o.tmdbId||o.id||a[0]),type:s(o.mediaType||o.type||a[1]||"movie").toLowerCase(),title:s(o.title||o.name||o.label),year:Number(o.year)||0}}
async function meta(q){var out={title:q.title,year:q.year};if(out.title&&out.year)return out;if(!q.id)return out;var kind=q.type==="tv"||q.type==="series"||q.type==="anime"?"tv":"movie";try{var r=await g.fetch("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.id)+"?api_key="+TMDB_KEY+"&language=fr-FR",{headers:{Accept:"application/json"}});if(r&&r.ok){var d=await r.json();out.title=s(d.title||d.name)||out.title;var date=s(d.release_date||d.first_air_date);out.year=Number(date.slice(0,4))||out.year}}catch(_e){}return out}
function referer(row){try{return s(row&&row.headers&&row.headers.Referer||row&&row.headers&&row.headers.referer||row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request&&row.behaviorHints.proxyHeaders.request.Referer||row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request&&row.behaviorHints.proxyHeaders.request.referer)}catch(_e){return ""}}
function sourcePage(ref){try{var u=new URL(ref,c.baseUrl+"/");var b=new URL(c.baseUrl+"/");if(u.hostname!==b.hostname)return null;var p=s(u.pathname);if(!p||p==="/"||/^\/(?:embed|api|player|watch|search)(?:\/|$)/i.test(p))return null;return u}catch(_e){return null}}
function matches(u,m){if(!u)return true;var text=norm(decodeURIComponent(s(u.pathname))),want=tokens(m.title);if(!want.length)return false;var have=tokens(text);if(!want.every(function(x){return have.indexOf(x)>=0}))return false;if(m.year){var years=text.match(/\b(?:19|20)\d{2}\b/g)||[];if(years.length&&years.indexOf(String(m.year))<0)return false}return true}
function slot(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioStreamzoIdentityV2)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var m=await meta(q);if(!m.title)return v;var kept=x.list.filter(function(row){return matches(sourcePage(referer(row)),m)});return rebuild(v,x,kept)};wrap.__nuvioStreamzoIdentityV2=true;wrap.__nuvioStreamzoIdentityOriginal=native;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return source.rstrip() + "\n" + shim.lstrip()
