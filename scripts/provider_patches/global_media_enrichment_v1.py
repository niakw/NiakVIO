#!/usr/bin/env python3
"""Globally enrich embed/player rows with proven direct media and playback context.

The enrichment is intentionally bounded and does not transcode or proxy media.
When a provider returns a public player/embed page, Niakvio follows only a small
candidate graph, proves direct HLS/DASH/container media, and emits an additional
direct row. The direct row carries the same browser request context used to
resolve it (Referer, Origin, User-Agent and domain/path-scoped session cookies),
so native players do not lose information that was implicitly present inside
the web player. Cookies are ephemeral per source row and never shared between
providers or unrelated domains. Textual HLS/DASH proof also works on NuvioTV's
text-only QuickJS fetch Response; binary proof still requires arrayBuffer().
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1"


def _strip_existing_wrapper(text: str) -> str:
    old = text.find(f"/* {MARKER}:")
    if old < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', old)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global media enrichment wrapper")
    return (text[:old] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "maxRows": max(1, min(int(cfg.get("max_rows", 6)), 12)),
        "maxDepth": max(1, min(int(cfg.get("max_depth", 2)), 3)),
        "maxCandidates": max(2, min(int(cfg.get("max_candidates", 10)), 20)),
        "timeoutMs": max(2500, min(int(cfg.get("timeout_ms", 6500)), 12000)),
        "preserveOriginal": bool(cfg.get("preserve_original", True)),
        "defaultUserAgent": str(cfg.get("default_user_agent") or ""),
        "implementationRevision": "scoped-playback-context-v4",
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if f"/* {marker} */" in text:
        return text
    text = _strip_existing_wrapper(text)

    js = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var ASSET=/\.(?:css|js|mjs|map|png|jpe?g|gif|svg|ico|woff2?|ttf|otf|eot|json|xml|vtt|srt)(?:[?#]|$)/i;
var BADHOST=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|googletagmanager\.com|google-analytics\.com|doubleclick\.net)$/i;
var DEFAULT_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_){return""}}
function rejected(v){var h=host(v);return !/^https?:\/\//i.test(v)||!h||BADHOST.test(h)||ASSET.test(v)||/(?:trailer|bande-annonce|big[_-]?buck[_-]?bunny|sample[-_]?video|\/troll\/master\.m3u8)/i.test(v)}
function directByName(v){return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/hls2?\//i.test(v)}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function keyOf(o,name){var keys=Object.keys(o||{}),want=String(name||"").toLowerCase();for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===want)return keys[i];return""}
function setHeader(o,name,value){if(!value)return;var k=keyOf(o,name);if(k&&k!==name)delete o[k];o[name]=String(value)}
function baseHeaders(row){
  var out={};
  function merge(src){if(src&&typeof src==="object")Object.keys(src).forEach(function(k){if(String(k).toLowerCase()!=="range"&&s(src[k]))out[k]=s(src[k])})}
  try{merge(row&&row.headers)}catch(_e){}
  try{merge(row&&row.requestHeaders)}catch(_e){}
  try{merge(row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request)}catch(_e){}
  return out;
}
function splitSetCookie(value){
  var raw=s(value);if(!raw)return[];
  return raw.split(/,(?=\s*[^;,=\s]+\s*=)/g).map(function(x){return x.trim()}).filter(Boolean);
}
function defaultPath(url){try{var p=new URL(url).pathname||"/";if(p.charAt(0)!=="/")return"/";var i=p.lastIndexOf("/");return i<=0?"/":p.slice(0,i+1)}catch(_e){return"/"}}
function rememberCookie(jar,setCookie,url){
  if(!jar||!setCookie)return;
  var parsed;try{parsed=new URL(url)}catch(_e){return}
  splitSetCookie(setCookie).forEach(function(line){
    var parts=line.split(";"),first=s(parts.shift()),eq=first.indexOf("=");if(eq<=0)return;
    var name=s(first.slice(0,eq)),value=s(first.slice(eq+1));if(!name)return;
    var item={name:name,value:value,domain:parsed.hostname.toLowerCase(),hostOnly:true,path:defaultPath(url),secure:false,expired:false};
    parts.forEach(function(part){var x=s(part),i=x.indexOf("="),ak=(i>=0?x.slice(0,i):x).trim().toLowerCase(),av=i>=0?s(x.slice(i+1)):"";
      if(ak==="domain"&&av){item.domain=av.replace(/^\./,"").toLowerCase();item.hostOnly=false}
      else if(ak==="path"&&av.charAt(0)==="/")item.path=av;
      else if(ak==="secure")item.secure=true;
      else if(ak==="max-age"&&Number(av)<=0)item.expired=true;
      else if(ak==="expires"){var ts=Date.parse(av);if(Number.isFinite(ts)&&ts<=Date.now())item.expired=true}
    });
    var id=item.name.toLowerCase()+"|"+item.domain+"|"+item.path;
    for(var i=jar.length-1;i>=0;i--){var old=jar[i],oldId=old.name.toLowerCase()+"|"+old.domain+"|"+old.path;if(oldId===id)jar.splice(i,1)}
    if(!item.expired&&item.value)jar.push(item);
  });
}
function captureCookies(jar,response,url){
  try{if(!response||!response.headers||typeof response.headers.get!=="function")return;var v=response.headers.get("set-cookie")||response.headers.get("Set-Cookie");if(v)rememberCookie(jar,v,url)}catch(_e){}
}
function cookieHeader(jar,target){
  var u;try{u=new URL(target)}catch(_e){return""}
  var h=u.hostname.toLowerCase(),p=u.pathname||"/",secure=u.protocol==="https:",out=[];
  (jar||[]).forEach(function(x){var domainOk=x.hostOnly?h===x.domain:(h===x.domain||h.endsWith("."+x.domain));if(!domainOk)return;if(x.secure&&!secure)return;if(p.indexOf(x.path)!==0)return;out.push(x.name+"="+x.value)});
  return out.join("; ");
}
function mergeCookies(a,b){
  var order=[],map={};function add(raw){s(raw).split(";").forEach(function(part){var x=s(part),i=x.indexOf("=");if(i<=0)return;var n=s(x.slice(0,i)),v=s(x.slice(i+1)),k=n.toLowerCase();if(!map[k])order.push(k);map[k]={n:n,v:v}})}add(a);add(b);return order.map(function(k){return map[k].n+"="+map[k].v}).join("; ")
}
function headers(row,referer,target,jar){
  var out=baseHeaders(row);
  if(referer){setHeader(out,"Referer",referer);try{setHeader(out,"Origin",new URL(referer).origin)}catch(_e){}}
  if(c.defaultUserAgent&&!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",c.defaultUserAgent);
  var scoped=cookieHeader(jar,target),existing=keyOf(out,"Cookie");if(scoped)setHeader(out,"Cookie",mergeCookies(existing?out[existing]:"",scoped));
  if(!directByName(target)&&!keyOf(out,"Range"))out.Range="bytes=0-262143";
  return out;
}
function kindBytes(bytes){if(!bytes||bytes.length<4)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes[0]===71&&(bytes.length<189||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var x="";for(var i=0;i<Math.min(bytes.length,262144);i++)x+=String.fromCharCode(bytes[i]);return x}}
async function fetchResource(url,row,referer,jar){try{
  var requestHeaders=headers(row,referer,url,jar),r=await g.fetch(url,{headers:requestHeaders,redirect:"follow",signal:timeout()});if(!r)return null;
  captureCookies(jar,r,s(r.url||url));
  var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",bytes=null,text="";
  if(typeof r.arrayBuffer==="function"){var buf=await r.arrayBuffer();bytes=new Uint8Array(buf);text=decode(bytes.slice(0,300000))}
  else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}
  return{ok:!!r.ok,status:r.status,url:s(r.url||url),type:type,bytes:bytes,text:text,headers:headers(row,referer,r.url||url,jar)}
}catch(_){return null}}
function proof(r){if(!r||!r.ok)return null;var t=s(r.text).trimStart();if(t.indexOf("#EXTM3U")===0)return"hls";if(/<MPD[\s>]/i.test(t.slice(0,4096))||/application\/dash\+xml/i.test(r.type))return"dash";var b=kindBytes(r.bytes);if(b)return b;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;seen[u]=1;out.push(u)}var body=s(text),patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mpd|mp4|mkv|webm|embed|player|\/e\/|\/hls2?\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null){add(m[1]);if(out.length>=c.maxCandidates)return out}}return out}
async function resolve(url,row,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(url))return[];seen=seen||{};if(seen[url])return[];seen[url]=1;var r=await fetchResource(url,row,referer,jar);if(!r)return[];var k=proof(r);if(k)return[{url:r.url||url,kind:k,headers:r.headers}];if(!/html|text|json|javascript|xml/i.test(r.type)&&!/[<>{}\[\]"']/.test(r.text||""))return[];var next=candidates(r.text,r.url||url),out=[];for(var i=0;i<next.length&&out.length<c.maxCandidates;i++){var found=await resolve(next[i],row,r.url||url,depth+1,seen,jar);for(var j=0;j<found.length;j++)if(!out.some(function(x){return x.url===found[j].url}))out.push(found[j])}return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function clone(row,media){var out=Object.assign({},row,{url:media.url,headers:media.headers||row.headers||{},isDirect:true,type:media.kind});if(media.kind==="hls"&&"format" in out)out.format="m3u8";if(media.kind==="dash"&&"format" in out)out.format="mpd";return out}
function refererOf(row,u){var h=baseHeaders(row),k=keyOf(h,"Referer");return s(k?h[k]:(row&&(row.referer||row.referrer||row.playerUrl||row.embedUrl||row.pageUrl))||u)}
async function enrich(list){var out=[],seen={};function add(row){var u=s(row&&row.url);if(!u||seen[u])return;seen[u]=1;out.push(row)}for(var i=0;i<list.length;i++){var row=list[i];if(!row||typeof row!=="object")continue;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u)){if(c.preserveOriginal)add(row);continue}if(i<c.maxRows&&!directByName(u)){var ref=refererOf(row,u),jar=[],found=await resolve(u,row,ref,0,{},jar);for(var j=0;j<found.length;j++)add(clone(row,found[j]))}add(row)}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalMediaEnrichmentV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var list=await enrich(x.list);return rebuild(v,x,list)};wrap.__nuvioGlobalMediaEnrichmentV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + js.lstrip()
