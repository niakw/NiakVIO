#!/usr/bin/env python3
"""Append targeted strict media resolution for LecteurVideo/MegaUp/Vidzy.

The adapter keeps the provider catalogue/search implementation intact and only
replaces its final HTML/embed URLs with media URLs after runtime proof.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_TV_TARGET_MEDIA_V3"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "providerName": str(cfg.get("provider_name") or "Provider"),
        "maxDepth": max(2, min(int(cfg.get("max_depth", 5)), 6)),
        "maxCandidates": max(6, min(int(cfg.get("max_candidates", 20)), 36)),
        "timeoutMs": max(5000, min(int(cfg.get("timeout_ms", 18000)), 30000)),
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var ASSET=/\.(?:woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|gif|svg|ico|webmanifest|json|xml|vtt|srt)(?:[?#]|$)/i;
var SOCIAL=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|google\.com|googleusercontent\.com|t\.me|telegram\.me|whatsapp\.com)$/i;
var DEMO=/(?:big[_-]?buck[_-]?bunny|sample[-_]?videos|test-videos|chrome\/static\/videos|sticky\/videos|static\/money|grok-|radar_promo)/i;
function s(v){return String(v==null?"":v).replace(/[\u200B-\u200D\uFEFF]/g,"").trim()}
function clean(v){return s(v).replace(/&amp;|&#038;/gi,"&").replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}
function abs(v,b){try{return new URL(clean(v),b).toString()}catch(_){return ""}}
function hostname(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function origin(u){try{return new URL(u).origin}catch(_){return ""}}
function rejected(u){var h=hostname(u);return !h||ASSET.test(u)||SOCIAL.test(h)||DEMO.test(u)||/\$\{|encodeURIComponent\(|credentials:/i.test(u)}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function outputHeaders(base,ref,target){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){if(String(k).toLowerCase()!=="range")out[k]=s(base[k])});if(ref&&!out.Referer&&!out.referer)out.Referer=ref;var o=origin(ref||target);if(o&&!out.Origin&&!out.origin)out.Origin=o;if(!out.Accept)out.Accept="*/*";return out}
function probeHeaders(base,ref,target){var out=outputHeaders(base,ref,target);if(!/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(target)&&!out.Range&&!out.range)out.Range="bytes=0-262143";return out}
function startsHls(text){return clean(text).trimStart().startsWith("#EXTM3U")}
function startsDash(text){return /<MPD[\s>]/i.test(clean(text).slice(0,4096))}
function bytesKind(bytes){if(!bytes||!bytes.length)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes.length>=4&&bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes.length>=188&&bytes[0]===71&&(bytes.length<376||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var out="";for(var i=0;i<Math.min(bytes.length,262144);i++)out+=String.fromCharCode(bytes[i]);return out}}
async function resource(u,base,ref){try{var h=probeHeaders(base,ref,u),r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buffer=await r.arrayBuffer(),bytes=new Uint8Array(buffer),text=decode(bytes.slice(0,300000));return{ok:!!r.ok,status:r.status,url:s(r.url||u),type:type,bytes:bytes,text:text,headers:outputHeaders(base,ref,u)}}catch(_){return null}}
function proof(r){if(!r)return null;if(startsHls(r.text))return"hls";if(startsDash(r.text)||/application\/dash\+xml/i.test(r.type))return"dash";var binary=bytesKind(r.bytes);if(binary)return binary;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function decodeLiteral(raw){return String(raw||"").replace(/\\u([0-9a-f]{4})/gi,function(_,h){return String.fromCharCode(parseInt(h,16))}).replace(/\\x([0-9a-f]{2})/gi,function(_,h){return String.fromCharCode(parseInt(h,16))}).replace(/\\([0-7]{1,3})/g,function(_,o){return String.fromCharCode(parseInt(o,8))}).replace(/\\n/g,"\n").replace(/\\r/g,"\r").replace(/\\t/g,"\t").replace(/\\'/g,"'").replace(/\\"/g,'"').replace(/\\\\/g,"\\")}
function unpackPackers(source){var out=[],re=/eval\(function\(p,a,c,k,e,d\)\{while\(c--\)if\(k\[c\]\)p=p\.replace\(new RegExp\('\\\\b'\+c\.toString\(a\)\+'\\\\b','g'\),k\[c\]\);return p\}\('((?:\\.|[^'\\])*)',(\d+),(\d+),'((?:\\.|[^'\\])*)'\.split\('\|'\)\)\)/g,m;while((m=re.exec(String(source||"")))!==null){try{var payload=decodeLiteral(m[1]),radix=parseInt(m[2],10),count=parseInt(m[3],10),words=decodeLiteral(m[4]).split("|");for(var i=count-1;i>=0;i--){if(!words[i])continue;var key=i.toString(radix).replace(/[.*+?^${}()|[\]\\]/g,"\\$&");payload=payload.replace(new RegExp("\\b"+key+"\\b","g"),words[i])}out.push(payload)}catch(_){}}return out}
function decodeVidzy(text){var out=[];if(!/charCodeAt[\s\S]{0,160}(?:0x3d|61)[\s\S]{0,80}\*89/i.test(text))return out;var re=/["']([A-Za-z0-9+/=]{24,})["']/g,m;while((m=re.exec(text))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",rev=raw.split("").reverse().join(""),value="";for(var i=0;i<rev.length;i++)value+=String.fromCharCode(rev.charCodeAt(i)^((0x3d+i*89)&255));if(/^https?:\/\//i.test(value)&&!rejected(value)&&out.indexOf(value)<0)out.push(value)}catch(_){}}return out}
function genericUrls(text,base){var out=[],seen={};function add(v,front){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;seen[u]=1;if(front)out.unshift(u);else out.push(u)}var normalized=clean(text),packed=unpackPackers(normalized);packed.forEach(function(body){decodeVidzy(body).forEach(function(u){add(u,true)});scan(body)});decodeVidzy(normalized).forEach(function(u){add(u,true)});scan(normalized);function scan(body){var patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-link|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl|_fsvHls)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mp4|mkv|webm|mpd|embed|player|download\.megaup|megaup\.net|vidzy|lecteurvideo|\/hls2?\/|\/videos\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++)while((m=patterns[i].exec(body))!==null)add(m[1])}return out.slice(0,c.maxCandidates)}
function normalizeRows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){var keys=["streams","results","data"];for(var i=0;i<keys.length;i++)if(Array.isArray(value[keys[i]]))return value[keys[i]]}return[]}
function normalizeRow(row){if(!row||typeof row!=="object")return null;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u))return null;return Object.assign({},row,{url:u,headers:row.headers&&typeof row.headers==="object"?row.headers:{}})}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
function compactRow(row,media){var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,260),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);if(row.size)out.size=s(row.size);if(Array.isArray(row.subtitles)&&row.subtitles.length)out.subtitles=row.subtitles.slice(0,20);return out}
async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}
async function invoke(old,self,args){var settings=g.SCRAPER_SETTINGS&&typeof g.SCRAPER_SETTINGS==="object"?g.SCRAPER_SETTINGS:{};var attempts=[function(){return old.call(self,args[0],args[1],args[2],args[3])},function(){return old.call(self,args[0],args[1],args[2],args[3],settings)},function(){return old.call(self,{tmdbId:args[0],mediaType:args[1],season:args[2],episode:args[3],settings:settings})}];for(var i=0;i<attempts.length;i++){try{var rows=normalizeRows(await attempts[i]());if(rows.length)return rows}catch(_){}}return[]}
async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTargetMediaV3)return false;var old=obj[key],wrap=async function(tmdbId,mediaType,season,episode){return tvRows(old,this,arguments)};wrap.__nuvioTargetMediaV3=true;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
