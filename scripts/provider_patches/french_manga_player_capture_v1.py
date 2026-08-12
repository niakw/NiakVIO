"""Preserve player embed URLs visited by French-Manga before native fallback resolution."""
from __future__ import annotations
import json
from typing import Any

MARKER = "NUVIO_FRENCH_MANGA_PLAYER_CAPTURE_V1"

def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if MARKER in source:
        return source
    cfg=dict(options or {})
    payload=json.dumps({
        "providerName":str(cfg.get("provider_name") or "French-Manga"),
        "baseUrl":str(cfg.get("base_url") or "https://w16.french-manga.net").rstrip("/"),
    },ensure_ascii=False,separators=(",",":"))
    shim=r'''
/* NUVIO_FRENCH_MANGA_PLAYER_CAPTURE_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function urlOf(input){try{return typeof input==="string"?input:s(input&&input.url)}catch(_){return""}}
function host(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return""}}
function player(u){var h=host(u);if(!h)return false;if(/\/troll\/master\.m3u8(?:[?#]|$)/i.test(u))return false;if(/(?:^|\.)(?:vidzy\.(?:live|org|cc)|luluvdo\.com|lulustream\.com|vidmoly\.(?:me|biz)|lecteurvideo\.com|uqload\.(?:is|co|cx)|veev\.to|waaw\.to|megaup\.net|vidhsareup\.fun)$/i.test(h))return /(?:\/embed(?:[-./?]|$)|\/e\/|\/f\/|\/player|\/video\.php|download\.megaup)/i.test(u);return false}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,sl,list){if(sl.key===null)return list;var out=Object.assign({},v);out[sl.key]=list;return out}
function headersFor(u){var out={Referer:c.baseUrl+"/",Accept:"*/*"};try{out.Origin=new URL(c.baseUrl).origin}catch(_){}return out}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioFrenchMangaCaptureV1)return false;var native=obj[key];var wrap=async function(){var original=g.fetch,captured=[],seen={};if(typeof original!=="function")return native.apply(this,arguments);g.fetch=async function(input,init){var u=urlOf(input);if(player(u)&&!seen[u]){seen[u]=1;captured.push(u)}return original.apply(this,arguments)};var value;try{value=await native.apply(this,arguments)}finally{g.fetch=original}var sl=slot(value),rows=sl?sl.list.slice():[];for(var i=0;i<captured.length;i++)rows.push({name:c.providerName+" Player",title:c.providerName+" Player",url:captured[i],quality:"HD",headers:headersFor(captured[i]),isDirect:false});return sl?rebuild(value,sl,rows):rows};wrap.__nuvioFrenchMangaCaptureV1=true;obj[key]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER",payload)
    return source.rstrip()+"\n"+shim.lstrip()+"\n"
