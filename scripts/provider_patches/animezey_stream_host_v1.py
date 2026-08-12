"""Rewrite only stale AnimeZey download-stream hosts after native extraction."""
from __future__ import annotations
import json
MARKER="NUVIO_ANIMEZEY_STREAM_HOST_V1"
def apply(source: str, options: dict | None=None, **_kwargs) -> str:
    if MARKER in source:return source
    cfg=dict(options or {})
    old=str(cfg.get("from_host") or "animezey16082023.animezey16082023.workers.dev").strip().lower()
    new=str(cfg.get("to_host") or "1.animezeydl.workers.dev").strip().lower()
    if not old or not new:raise ValueError("animezey_stream_host_v1 requires from_host and to_host")
    payload=json.dumps({"fromHost":old,"toHost":new},separators=(",",":"))
    shim=r'''
/* NUVIO_ANIMEZEY_STREAM_HOST_V1 */
;(function(g,c){"use strict";
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,s,list){if(s.key===null)return list;var o=Object.assign({},v);o[s.key]=list;return o}
function rewrite(raw){var value=String(raw==null?"":raw).trim();if(!/^https?:\/\//i.test(value))return value;try{var u=new URL(value);if(u.hostname.toLowerCase()!==c.fromHost)return value;u.hostname=c.toHost;return u.toString()}catch(_e){return value}}
function row(r){if(!r||typeof r!=="object")return r;var u=String(r.url||""),n=rewrite(u);return n===u?r:Object.assign({},r,{url:n})}
function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioAnimeZeyStreamHostV1)return false;var native=t.getStreams;var w=async function(){var v=await native.apply(this,arguments),s=slot(v);return s?rebuild(v,s,s.list.map(row)):v};w.__nuvioAnimeZeyStreamHostV1=true;t.getStreams=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports)}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else{var b={getStreams:g.getStreams};install(b);g.getStreams=b.getStreams}}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER",payload)
    return source.rstrip()+"\n"+shim.lstrip()+"\n"
