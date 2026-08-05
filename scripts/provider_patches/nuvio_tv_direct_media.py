#!/usr/bin/env python3
"""Append a NuvioTV-compatible invocation and direct-media resolver wrapper."""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_TV_DIRECT_MEDIA_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "providerName": str(cfg.get("provider_name") or "Provider"),
        "maxDepth": max(1, min(int(cfg.get("max_depth", 4)), 5)),
        "maxCandidates": max(4, min(int(cfg.get("max_candidates", 20)), 40)),
        "timeoutMs": max(3000, min(int(cfg.get("timeout_ms", 12000)), 25000)),
        "blockedHosts": [str(value).lower().lstrip(".") for value in cfg.get("blocked_hosts", [])],
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function str(v){return String(v==null?"":v).trim()}
function clean(v){return str(v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}
function abs(v,b){try{return new URL(clean(v),b).toString()}catch(_){return ""}}
function host(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function origin(u){try{return new URL(u).origin}catch(_){return ""}}
function badHost(u){var h=host(u);if(!h)return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;return false}
function mediaExt(u){var x=str(u).toLowerCase();if(/\.m3u8(?:[?#]|$)|\/hls\/|\/hls2\/|master\.m3u8/i.test(x))return"hls";if(/\.mp4(?:[?#]|$)/i.test(x))return"mp4";if(/\.mkv(?:[?#]|$)/i.test(x))return"mkv";if(/\.webm(?:[?#]|$)/i.test(x))return"webm";if(/\.mpd(?:[?#]|$)/i.test(x))return"dash";return null}
function isHtmlType(t){return /(?:text\/html|application\/xhtml)/i.test(str(t))}
function mediaType(t){t=str(t).toLowerCase();if(/mpegurl/.test(t))return"hls";if(/dash\+xml/.test(t))return"dash";if(/^video\/mp4/.test(t))return"mp4";if(/^video\/webm/.test(t))return"webm";if(/^video\//.test(t)||/octet-stream|matroska/.test(t))return"file";return null}
function startsHls(v){return clean(v).replace(/^\ufeff/,"").trimStart().startsWith("#EXTM3U")}
function headers(base,ref,target){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){out[k]=str(base[k])});if(ref&&!out.Referer&&!out.referer)out.Referer=ref;var o=origin(ref||target);if(o&&!out.Origin&&!out.origin)out.Origin=o;if(!out.Accept)out.Accept="*/*";return out}
function timeoutSignal(ms){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(ms):undefined}catch(_){return undefined}}
async function fetchText(u,h){try{var r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeoutSignal(c.timeoutMs)});if(!r)return null;var type=r.headers&&r.headers.get?str(r.headers.get("content-type")):"";var body="";if(!mediaType(type)||/mpegurl|dash\+xml|json|text|javascript|html/i.test(type)){try{body=await r.text()}catch(_){body=""}}return{ok:!!r.ok,status:r.status,url:str(r.url||u),type:type,body:body,headers:r.headers}}catch(_){return null}}
function unescapeJs(v){try{return JSON.parse('"'+str(v).replace(/"/g,'\\"')+'"')}catch(_){return clean(v)}}
function unpackPacker(source){var out=[],re=/eval\(function\(p,a,c,k,e,[rd]\)\{[\s\S]*?\}\(\s*['"]((?:\\.|[^'"\\])*)['"]\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*['"]((?:\\.|[^'"\\])*)['"]\.split\(['"]\|['"]\)/g,m;while((m=re.exec(str(source)))!==null){try{var payload=unescapeJs(m[1]),radix=parseInt(m[2],10),count=parseInt(m[3],10),words=unescapeJs(m[4]).split("|");function key(n){return n.toString(radix)}for(var i=count-1;i>=0;i--){if(!words[i])continue;var rx=new RegExp("\\b"+key(i).replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"\\b","g");payload=payload.replace(rx,words[i])}out.push(payload)}catch(_){}}return out}
function decodeBase64(text){var out=[],re=/(?:atob|base64_decode)\(\s*['"]([A-Za-z0-9+/=]{16,})['"]\s*\)/gi,m;while((m=re.exec(str(text)))!==null){try{var value=typeof g.atob==="function"?g.atob(m[1]):"";if(value)out.push(value)}catch(_){}}return out}
function candidates(text,base){var values=[],seen={};function add(v){var u=abs(v,base);if(!u||badHost(u)||seen[u])return;seen[u]=1;values.push(u)}function scan(body){body=clean(body);var patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-link|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mp4|mkv|webm|mpd|embed|player|watch|stream|\/e\/|\/v\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++)while((m=patterns[i].exec(body))!==null)add(m[1])}scan(text);unpackPacker(text).forEach(scan);decodeBase64(text).forEach(scan);return values.slice(0,c.maxCandidates)}
function normalizeRows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){for(var i=0;i<["streams","results","data"].length;i++){var rows=value[["streams","results","data"][i]];if(Array.isArray(rows))return rows}}return[]}
function normalizeRow(row){if(!row||typeof row!=="object")return null;var u=str(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u)return null;var h=row.headers&&typeof row.headers==="object"?row.headers:{};return Object.assign({},row,{url:u,headers:h})}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||badHost(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var h=headers(baseHeaders,referer,u),ext=mediaExt(u),response=await fetchText(u,h);if(!response){if(ext&&ext!=="hls")return[{url:u,type:ext,headers:h,isDirect:true}];return[]}
var finalUrl=response.url||u,ct=mediaType(response.type);if(startsHls(response.body))return[{url:finalUrl,type:"hls",headers:h,isDirect:true}];if(ct&&ct!=="hls"&&!isHtmlType(response.type))return[{url:finalUrl,type:ct,headers:h,isDirect:true}];if(ext==="hls"&&!startsHls(response.body)){
  // A .m3u8-shaped URL returning HTML/JSON is not an HLS manifest.
}else if(ext&&!isHtmlType(response.type)&&!response.body)return[{url:finalUrl,type:ext,headers:h,isDirect:true}];
var body=response.body||"";if(!body||(!isHtmlType(response.type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=candidates(body,finalUrl),out=[];for(var i=0;i<next.length&&out.length<c.maxCandidates;i++){var resolved=await resolve(next[i],h,finalUrl,depth+1,seen);out=out.concat(resolved)}return unique(out)}
async function invoke(old,self,args){var settings=g.SCRAPER_SETTINGS&&typeof g.SCRAPER_SETTINGS==="object"?g.SCRAPER_SETTINGS:{};var attempts=[function(){return old.call(self,args[0],args[1],args[2],args[3])},function(){return old.call(self,args[0],args[1],args[2],args[3],settings)},function(){return old.call(self,{tmdbId:args[0],mediaType:args[1],season:args[2],episode:args[3],settings:settings})}];var best=[];for(var i=0;i<attempts.length;i++){try{var rows=normalizeRows(await attempts[i]());if(rows.length){best=rows;break}}catch(_){}}return best}
async function tvRows(old,self,args){var native=await invoke(old,self,args),out=[];for(var i=0;i<native.length;i++){var row=normalizeRow(native[i]);if(!row)continue;var ref=str(row.headers&& (row.headers.Referer||row.headers.referer)||row.referer||row.url);var resolved=await resolve(row.url,row.headers,ref,0,{});for(var j=0;j<resolved.length;j++){var media=resolved[j];out.push(Object.assign({},row,media,{name:row.name||c.providerName,title:row.title||row.name||c.providerName,quality:row.quality||"HD",headers:media.headers||row.headers||{},isDirect:true,type:media.type||mediaExt(media.url)||row.type||null}))}}return unique(out)}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTvDirect)return false;var old=obj[key];var wrap=async function(tmdbId,mediaType,season,episode){return tvRows(old,this,arguments)};wrap.__nuvioTvDirect=true;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
