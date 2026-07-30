"""Targeted stream-output repair retained only after runtime improvement.

Unlike the former blanket guard, this wrapper is applied only to a provider
whose deep evidence shows returned streams failing their HTTP playback probe.
"""
from __future__ import annotations

import json
import re
from typing import Any

MARKER = "NUVIO_STREAM_OUTPUT_RECOVERY_V1"


def apply(source: str, *, options: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> str:
    options = dict(options or {})
    source = re.sub(r"\n?/\* NUVIO_STREAM_OUTPUT_RECOVERY_V1 \*/[\s\S]*$", "", source).rstrip()
    policy = json.dumps({
        "user_agent": options.get("user_agent") or "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36",
        "add_accept": options.get("add_accept", True),
        "add_range": options.get("add_range", True),
        "reject_extensions": options.get("reject_extensions") or [".avi", ".wmv", ".flv"],
    }, separators=(",", ":"))
    guard = r'''
/* NUVIO_STREAM_OUTPUT_RECOVERY_V1 */
;(function(g,policy){
  function str(v){return v==null?"":String(v)}
  function copyObject(source){var out={},k;if(source&&typeof source==="object")for(k in source)if(Object.prototype.hasOwnProperty.call(source,k))out[k]=source[k];return out}
  function has(headers,name){name=String(name).toLowerCase();for(var k in headers)if(Object.prototype.hasOwnProperty.call(headers,k)&&String(k).toLowerCase()===name)return true;return false}
  function badExtension(url){var clean=str(url).toLowerCase().split("?")[0].split("#")[0],list=policy.reject_extensions||[];for(var i=0;i<list.length;i++){var ext=str(list[i]).toLowerCase();if(ext&&clean.slice(-ext.length)===ext)return true}return false}
  function quality(s){var h=(str(s.quality)+" "+str(s.name)+" "+str(s.title)+" "+str(s.size)).toLowerCase(),m=/(2160|1440|1080|720|576|540|480|360)p?/.exec(h);if(m)return m[1]+"p";if(/(^|\W)(4k|uhd)(\W|$)/.test(h))return"2160p";return str(s.quality)||"HD"}
  function language(s){if(str(s.language).replace(/^\s+|\s+$/g,""))return s.language;var h=(str(s.name)+" "+str(s.title)+" "+str(s.size)).toUpperCase();if(/VOSTFR|VOST[ -]?FR|SUB(?:BED)?[ -]?FR/.test(h))return"VOSTFR";if(/DUAL[ -]?AUDIO|MULTI(?:LANG)?|VFF\s*[+\/]|VFQ\s*[+\/]/.test(h))return"MULTI";if(/\bVFQ\b/.test(h))return"VFQ";if(/\bVFF\b|\bVF\b|FRENCH/.test(h))return"VF";if(/\bVO\b|ENGLISH|ORIGINAL/.test(h))return"VO";return""}
  function normalize(result){var list=Object.prototype.toString.call(result)==="[object Array]"?result:[],out=[],seen={},i;for(i=0;i<list.length;i++){var s=list[i];if(!s||typeof s!=="object"||typeof s.url!=="string")continue;var url=s.url.replace(/^\s+|\s+$/g,"");if(!/^https?:\/\//i.test(url)||badExtension(url)||seen[url])continue;seen[url]=1;var n=copyObject(s),headers=copyObject(s.headers);n.url=url;n.quality=quality(n);var lang=language(n);if(lang)n.language=lang;if(!has(headers,"User-Agent"))headers["User-Agent"]=policy.user_agent;if(policy.add_accept&&!has(headers,"Accept"))headers.Accept="*/*";if(policy.add_range&&!has(headers,"Range"))headers.Range="bytes=0-";n.headers=headers;out.push(n)}return out}
  function wrap(fn){if(typeof fn!=="function"||fn.__nuvioStreamOutputRecoveryV1)return fn;var w=function(){var self=this,args=arguments;try{return Promise.resolve(fn.apply(self,args)).then(normalize)}catch(e){return Promise.reject(e)}};try{w.__nuvioStreamOutputRecoveryV1=true}catch(_e){}return w}
  try{if(typeof module!=="undefined"&&module&&module.exports){if(typeof module.exports==="function")module.exports=wrap(module.exports);else if(module.exports&&typeof module.exports.getStreams==="function")module.exports.getStreams=wrap(module.exports.getStreams)}}catch(_e){}
  try{if(g&&typeof g.getStreams==="function")g.getStreams=wrap(g.getStreams)}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,__POLICY__);
'''.replace("__POLICY__", policy)
    return source + "\n" + guard
