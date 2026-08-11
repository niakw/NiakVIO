#!/usr/bin/env python3
"""Append a binary-strict NuvioTV output resolver.

The wrapper follows the real TV contract (four positional arguments and global
SCRAPER_SETTINGS), rejects assets/social/demo media, and only publishes a URL
after the response proves HLS/DASH or a real video container signature.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_TV_DIRECT_MEDIA_V2"
STRIP_MARKERS = (
    "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
    "/* NUVIO_STREAM_OUTPUT_SANITIZER_V",
    "/* NUVIO_TV_DIRECT_MEDIA_V1",
)


def strip_unproven_wrappers(text: str, enabled: bool) -> str:
    if not enabled:
        return text
    indexes = [index for marker in STRIP_MARKERS if (index := text.find(marker)) >= 0]
    return text[: min(indexes)] if indexes else text


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    text = strip_unproven_wrappers(text, bool(cfg.get("strip_unproven_wrappers")))
    payload = {
        "providerName": str(cfg.get("provider_name") or "Provider"),
        "maxDepth": max(1, min(int(cfg.get("max_depth", 4)), 5)),
        "maxCandidates": max(4, min(int(cfg.get("max_candidates", 16)), 30)),
        "timeoutMs": max(3000, min(int(cfg.get("timeout_ms", 12000)), 22000)),
        "blockedHosts": [str(value).lower().lstrip(".") for value in cfg.get("blocked_hosts", [])],
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var ASSET=/\.(?:woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|gif|svg|ico|webmanifest|json|xml|vtt|srt)(?:[?#]|$)/i;
var DEMO=/(?:chrome\/static\/videos|sticky\/videos|static\/money|grok-|radar_promo|big[_-]?buck[_-]?bunny|sample[-_]?videos|test-videos)/i;
var SOCIAL=/(?:^|\.)(?:twitter\.com|x\.com|twimg\.com|google\.com|googleusercontent\.com|gitlab\.com|github\.com|facebook\.com|instagram\.com)$/i;
function s(v){return String(v==null?"":v).replace(/[\u200B-\u200D\uFEFF]/g,"").trim()}
function clean(v){return s(v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}
function abs(v,b){try{return new URL(clean(v),b).toString()}catch(_){return ""}}
function hostname(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function origin(u){try{return new URL(u).origin}catch(_){return ""}}
function rejected(u){var h=hostname(u);if(!h||ASSET.test(u)||DEMO.test(u)||SOCIAL.test(h))return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;return false}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function headers(base,ref,target){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){out[k]=s(base[k])});if(ref&&!out.Referer&&!out.referer)out.Referer=ref;var o=origin(ref||target);if(o&&!out.Origin&&!out.origin)out.Origin=o;if(!out.Accept)out.Accept="*/*";return out}
function startsHls(text){return clean(text).trimStart().startsWith("#EXTM3U")}
function startsDash(text){return /<MPD[\s>]/i.test(clean(text).slice(0,4096))}
function bytesKind(bytes){if(!bytes||!bytes.length)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes.length>=4&&bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes.length>=188&&bytes[0]===71&&(bytes.length<376||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var out="";for(var i=0;i<Math.min(bytes.length,262144);i++)out+=String.fromCharCode(bytes[i]);return out}}
async function resource(u,h){try{var r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buffer=await r.arrayBuffer(),bytes=new Uint8Array(buffer),text=decode(bytes.slice(0,262144));return{ok:!!r.ok,status:r.status,url:s(r.url||u),type:type,bytes:bytes,text:text}}catch(_){return null}}
function proof(r){if(!r)return null;if(startsHls(r.text))return"hls";if(startsDash(r.text)||/application\/dash\+xml/i.test(r.type))return"dash";var binary=bytesKind(r.bytes);if(binary)return binary;if(/^video\//i.test(r.type)&&!/^video\/(?:svg|x-font)/i.test(r.type))return"video";return null}
function unescapeJs(v){try{return JSON.parse('"'+s(v).replace(/"/g,'\\"')+'"')}catch(_){return clean(v)}}
function unpack(source){var out=[],re=/eval\(function\(p,a,c,k,e,[rd]\)\{[\s\S]*?\}\(\s*['"]((?:\\.|[^'"\\])*)['"]\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*['"]((?:\\.|[^'"\\])*)['"]\.split\(['"]\|['"]\)/g,m;while((m=re.exec(s(source)))!==null){try{var payload=unescapeJs(m[1]),radix=parseInt(m[2],10),count=parseInt(m[3],10),words=unescapeJs(m[4]).split("|");function key(n){return n.toString(radix)}for(var i=count-1;i>=0;i--){if(!words[i])continue;var rx=new RegExp("\\b"+key(i).replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"\\b","g");payload=payload.replace(rx,words[i])}out.push(payload)}catch(_){}}return out}
function base64(source){var out=[],re=/(?:atob|base64_decode)\(\s*['"]([A-Za-z0-9+/=]{16,})['"]\s*\)/gi,m;while((m=re.exec(s(source)))!==null){try{var value=typeof g.atob==="function"?g.atob(m[1]):"";if(value)out.push(value)}catch(_){}}return out}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;var low=u.toLowerCase();if(!/(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd|\/hls\/|\/hls2\/|master\.m3u8|embed|player|watch|stream|video|\/e\/|\/v\/)/i.test(low))return;seen[u]=1;out.push(u)}function scan(body){body=clean(body);var patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-link|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mp4|mkv|webm|mpd|embed|player|watch|stream|\/e\/|\/v\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++)while((m=patterns[i].exec(body))!==null)add(m[1])}scan(text);unpack(text).forEach(scan);base64(text).forEach(scan);return out.slice(0,c.maxCandidates)}
function normalizeRows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){var keys=["streams","results","data"];for(var i=0;i<keys.length;i++)if(Array.isArray(value[keys[i]]))return value[keys[i]]}return[]}
function normalizeRow(row){if(!row||typeof row!=="object")return null;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u))return null;return Object.assign({},row,{url:u,headers:row.headers&&typeof row.headers==="object"?row.headers:{}})}
function compactRow(row,media){var subs=Array.isArray(row.subtitles)?row.subtitles.filter(function(x){return x&&x.url&&!rejected(x.url)}).slice(0,20):undefined;var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,240),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||row.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);if(row.size)out.size=s(row.size);if(subs&&subs.length)out.subtitles=subs;return out}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var h=headers(baseHeaders,referer,u),r=await resource(u,h);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:h}];var type=s(r.type).toLowerCase();if(/text\/html|application\/xhtml|javascript|json|text\//i.test(type)||/[<>{}\[\]"']/.test(r.text)){var next=candidates(r.text,r.url||u),jobs=next.slice(0,c.maxCandidates).map(function(v){return resolve(v,h,r.url||u,depth+1,seen)}),groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}return[]}
async function invoke(old,self,args){var settings=g.SCRAPER_SETTINGS&&typeof g.SCRAPER_SETTINGS==="object"?g.SCRAPER_SETTINGS:{};var attempts=[function(){return old.call(self,args[0],args[1],args[2],args[3])},function(){return old.call(self,args[0],args[1],args[2],args[3],settings)},function(){return old.call(self,{tmdbId:args[0],mediaType:args[1],season:args[2],episode:args[3],settings:settings})}];for(var i=0;i<attempts.length;i++){try{var rows=normalizeRows(await attempts[i]());if(rows.length)return rows}catch(_){}}return[]}
async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTvDirectV2)return false;var old=obj[key],wrap=async function(tmdbId,mediaType,season,episode){return tvRows(old,this,arguments)};wrap.__nuvioTvDirectV2=true;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
