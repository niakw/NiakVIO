#!/usr/bin/env python3
"""NuvioTV strict target-media resolver with platform playback context.

This is a drop-in superset of target-media V4. It preserves V4's text-only
fetch and protocol-relative URL compatibility while fixing the remaining
site -> player/embed -> media boundary for the native TV client:

* Referer and Origin are refreshed to the immediate parent on every hop.
* A small per-row cookie jar captures Set-Cookie and scopes Cookie by domain/path.
* The browser User-Agent used by the provider bridge is preserved for playback.
* The compact TV row keeps a useful size/description fallback without changing
  Desktop/Mobile mapping semantics.

V4 markers remain present so existing release-integrity and profile checks keep
working. Existing materialized V4 bundles are upgraded in place and reapply is
byte-idempotent.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def _load_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem + "_v5", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


TARGET = _load_apply(ROOT / "nuvio_tv_target_media_v3.py")
EXPOSE = _load_apply(ROOT / "expose_strict_wrapper_original.py")
FILTER = _load_apply(ROOT / "target_media_host_filter_v4.py")

V4_MARKER = "/* NUVIO_TV_TARGET_MEDIA_V4 */"
V5_MARKER = "/* NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT */"
FETCH_COMPAT_MARKER = "/* NUVIO_TV_TEXT_ONLY_FETCH_COMPAT_V1 */"
PROTOCOL_RELATIVE_MARKER = "/* NUVIO_TV_PROTOCOL_RELATIVE_URL_COMPAT_V1 */"
VIDZY_DECODER_START = "function decodeVidzy(text){"
VIDZY_DECODER_END = "function genericUrls(text,base){"
GENERIC_URLS_START = "function genericUrls(text,base){"
GENERIC_URLS_END = "function normalizeRows(value){"
LEGACY_DIRECT_MEDIA_MARKER = "/* NUVIO_TV_DIRECT_MEDIA_V2"
LEGACY_DIRECT_MEDIA_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
TARGET_MEDIA_MARKER = "/* NUVIO_TV_TARGET_MEDIA_V3:"
TARGET_MEDIA_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
REJECTED_V3 = r'''function rejected(u){var h=hostname(u);return !h||ASSET.test(u)||SOCIAL.test(h)||DEMO.test(u)||/\$\{|encodeURIComponent\(|credentials:/i.test(u)}'''
ABS_V3 = r'''function abs(v,b){try{return new URL(clean(v),b).toString()}catch(_){return ""}}'''
ABS_V4 = r'''function abs(v,b){try{var raw=clean(v);if(/^\/\//.test(raw)){var scheme=/^https:/i.test(String(b||""))?"https:":"http:";return scheme+raw}return new URL(raw,b).toString()}catch(_){return ""}}'''
RESOURCE_V3 = r'''async function resource(u,base,ref){try{var h=probeHeaders(base,ref,u),r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buffer=await r.arrayBuffer(),bytes=new Uint8Array(buffer),text=decode(bytes.slice(0,300000));return{ok:!!r.ok,status:r.status,url:s(r.url||u),type:type,bytes:bytes,text:text,headers:outputHeaders(base,ref,u)}}catch(_){return null}}'''
RESOURCE_V4 = r'''async function resource(u,base,ref){try{var h=probeHeaders(base,ref,u),r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",bytes=null,text="";if(typeof r.arrayBuffer==="function"){var buffer=await r.arrayBuffer();bytes=new Uint8Array(buffer);text=decode(bytes.slice(0,300000))}else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}return{ok:!!r.ok,status:r.status,url:s(r.url||u),type:type,bytes:bytes,text:text,headers:outputHeaders(base,ref,u)}}catch(_){return null}}'''

STRICT_BLOCKED_HOSTS = {
    "cloudflare.com", "googletagmanager.com", "google-analytics.com",
    "analytics.google.com", "static.cloudflareinsights.com",
    "cloudflareinsights.com", "connect.facebook.net", "doubleclick.net",
    "googlesyndication.com", "pagead2.googlesyndication.com",
    "api.themoviedb.org", "graphql.anilist.co", "arm.haglund.dev",
    "v3-cinemeta.strem.io",
}

VIDZY_DECODER_V4 = r'''function decodeVidzy(text,base){var out=[];if(!/charCodeAt[\s\S]{0,420}(?:0x3d|61)[\s\S]{0,240}\*\s*89/i.test(text))return out;var host=hostname(base),H=0;for(var j=0;j<host.length;j++)H=(H+host.charCodeAt(j))&255;var hostKeyed=/\+\s*H\s*\)\s*&\s*255|\+\s*H\s*&\s*255/i.test(text),re=/["']([A-Za-z0-9+/=]{24,})["']/g,m;while((m=re.exec(text))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",rev=raw.split("").reverse().join(""),keys=hostKeyed?[H]:[0],value="";for(var k=0;k<keys.length;k++){value="";for(var i=0;i<rev.length;i++)value+=String.fromCharCode(rev.charCodeAt(i)^((0x3d+i*89+keys[k])&255));if(/^https?:\/\//i.test(value)&&!rejected(value)&&out.indexOf(value)<0){out.push(value);break}}}catch(_){}}return out}'''
LECTEURVIDEO_DECODER_V4 = r'''function decodeLecteurVideo(text,base){var out=[],seen={},re=/\bshowVideo\s*\(\s*["']([A-Za-z0-9+/=]{16,})["']/gi,m;while((m=re.exec(String(text||"")))!==null){try{var raw=typeof g.atob==="function"?g.atob(m[1]):"",u=abs(raw,base);if(u&&!rejected(u)&&!seen[u]){seen[u]=1;out.push(u)}}catch(_){}}return out}'''
GENERIC_URLS_V4 = r'''function genericUrls(text,base){var out=[],seen={};var PLAYER_HOST=/(?:^|\.)(?:vidzy\.(?:org|live|cc)|fsvid\.lol|uqload\.(?:is|co|cx)|lecteurvideo\.com|xtremestream\.xyz|megaup\.net|veev\.to|veevcdn\.co|waaw\.to|lulustream\.com|luluvdo\.com|vidmoly\.(?:me|biz)|emmmmbed\.com|ironwallnet\.net)$/i;var DIRECT=/(?:\.m3u8|\.mpd)(?:[?#]|$)|\/hls2?\//i;var MEDIA_FILE=/\.(?:mp4|mkv|webm)(?:[?#]|$)/i;var PLAYER_PATH=/(?:\/embed(?:[-./?]|$)|\/player(?:[-./?]|$)|\/e\/|\/f\/|\/video\.php(?:[?#]|$)|download\.megaup)/i;var MEDIAISH_HOST=/(?:^|\.)(?:cdn|media|video|stream|vod|edge|storage|files?|cloud)[-.]/i;function allowed(u){if(!u||rejected(u))return false;var h=hostname(u);if(DIRECT.test(u))return true;if(PLAYER_HOST.test(h))return true;if(PLAYER_PATH.test(u))return true;if(MEDIA_FILE.test(u)&&MEDIAISH_HOST.test(h))return true;return false}function add(v,front){var u=abs(v,base);if(!allowed(u)||seen[u])return;seen[u]=1;if(front)out.unshift(u);else out.push(u)}var normalized=clean(text),packed=unpackPackers(normalized);packed.forEach(function(body){decodeVidzy(body,base).forEach(function(u){add(u,true)});decodeLecteurVideo(body,base).forEach(function(u){add(u,true)});scan(body)});decodeVidzy(normalized,base).forEach(function(u){add(u,true)});decodeLecteurVideo(normalized,base).forEach(function(u){add(u,true)});scan(normalized);function scan(body){var patterns=[/(?:src|data-src|data-url|data-embed|data-player|data-link|data-file|href)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl|_fsvHls)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null)add(m[1])}}return out.slice(0,c.maxCandidates)}'''

OUTPUT_OLD = r'''function outputHeaders(base,ref,target){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){if(String(k).toLowerCase()!=="range")out[k]=s(base[k])});if(ref&&!out.Referer&&!out.referer)out.Referer=ref;var o=origin(ref||target);if(o&&!out.Origin&&!out.origin)out.Origin=o;if(!out.Accept)out.Accept="*/*";return out}
function probeHeaders(base,ref,target){var out=outputHeaders(base,ref,target);if(!/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(target)&&!out.Range&&!out.range)out.Range="bytes=0-262143";return out}'''
OUTPUT_NEW = r'''var NUVIO_PLAYBACK_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
function headerKey(obj,name){var keys=Object.keys(obj||{}),want=String(name||"").toLowerCase();for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===want)return keys[i];return""}
function setHeader(obj,name,value){if(!value)return;var old=headerKey(obj,name);if(old&&old!==name)delete obj[old];obj[name]=String(value)}
function defaultCookiePath(url){try{var p=new URL(url).pathname||"/",i=p.lastIndexOf("/");return i<=0?"/":p.slice(0,i+1)}catch(_){return"/"}}
function splitSetCookie(value){var raw=s(value);if(!raw)return[];return raw.split(/,(?=\s*[^;,=\s]+\s*=)/g).map(function(v){return v.trim()}).filter(Boolean)}
function rememberCookie(jar,setCookie,url){if(!jar||!setCookie)return;var u;try{u=new URL(url)}catch(_){return}splitSetCookie(setCookie).forEach(function(line){var parts=line.split(";"),first=s(parts.shift()),eq=first.indexOf("=");if(eq<=0)return;var item={name:s(first.slice(0,eq)),value:s(first.slice(eq+1)),domain:u.hostname.toLowerCase(),hostOnly:true,path:defaultCookiePath(url),secure:false,expired:false};if(!item.name)return;parts.forEach(function(part){var x=s(part),i=x.indexOf("="),k=(i>=0?x.slice(0,i):x).trim().toLowerCase(),v=i>=0?s(x.slice(i+1)):"";if(k==="domain"&&v){item.domain=v.replace(/^\./,"").toLowerCase();item.hostOnly=false}else if(k==="path"&&v.charAt(0)==="/")item.path=v;else if(k==="secure")item.secure=true;else if(k==="max-age"&&Number(v)<=0)item.expired=true;else if(k==="expires"){var ts=Date.parse(v);if(Number.isFinite(ts)&&ts<=Date.now())item.expired=true}});var id=item.name.toLowerCase()+"|"+item.domain+"|"+item.path;for(var j=jar.length-1;j>=0;j--){var old=jar[j],oldId=old.name.toLowerCase()+"|"+old.domain+"|"+old.path;if(oldId===id)jar.splice(j,1)}if(!item.expired&&item.value)jar.push(item)})}
function seedCookieHeader(jar,headers,url){if(!jar||!headers||typeof headers!=="object")return;var k=headerKey(headers,"cookie"),raw=k?s(headers[k]):"";if(!raw)return;var h=hostname(url);if(!h)return;raw.split(";").forEach(function(part){var x=s(part),i=x.indexOf("=");if(i<=0)return;jar.push({name:s(x.slice(0,i)),value:s(x.slice(i+1)),domain:h,hostOnly:true,path:"/",secure:false,expired:false})})}
function captureCookies(jar,response,url){try{if(!response||!response.headers||typeof response.headers.get!=="function")return;var v=response.headers.get("set-cookie")||response.headers.get("Set-Cookie");if(v)rememberCookie(jar,v,url)}catch(_){}}
function cookieHeader(jar,target){var u;try{u=new URL(target)}catch(_){return""}var h=u.hostname.toLowerCase(),p=u.pathname||"/",secure=u.protocol==="https:",out=[];(jar||[]).forEach(function(x){var domainOk=x.hostOnly?h===x.domain:(h===x.domain||h.endsWith("."+x.domain));if(!domainOk||x.secure&&!secure||p.indexOf(x.path)!==0)return;out.push(x.name+"="+x.value)});return out.join("; ")}
function outputHeaders(base,ref,target,jar){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){var lower=String(k).toLowerCase();if(lower!=="range"&&lower!=="referer"&&lower!=="origin"&&lower!=="cookie")out[k]=s(base[k])});if(ref){setHeader(out,"Referer",ref);var o=origin(ref);if(o)setHeader(out,"Origin",o)}else{var bk=headerKey(base||{},"referer");if(bk)setHeader(out,"Referer",base[bk]);var bo=headerKey(base||{},"origin");if(bo)setHeader(out,"Origin",base[bo])}if(!headerKey(out,"user-agent"))setHeader(out,"User-Agent",NUVIO_PLAYBACK_UA);var cookie=cookieHeader(jar,target);if(cookie)setHeader(out,"Cookie",cookie);if(!headerKey(out,"accept"))out.Accept="*/*";return out}
function probeHeaders(base,ref,target,jar){var out=outputHeaders(base,ref,target,jar);if(!/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(target)&&!out.Range&&!out.range)out.Range="bytes=0-262143";return out}'''

RESOURCE_NEW = r'''async function resource(u,base,ref,jar){try{var h=probeHeaders(base,ref,u,jar),r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var finalUrl=s(r.url||u);captureCookies(jar,r,finalUrl);var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",bytes=null,text="";if(typeof r.arrayBuffer==="function"){var buffer=await r.arrayBuffer();bytes=new Uint8Array(buffer);text=decode(bytes.slice(0,300000))}else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}return{ok:!!r.ok,status:r.status,url:finalUrl,type:type,bytes:bytes,text:text,headers:outputHeaders(base,ref,finalUrl,jar)}}catch(_){return null}}'''

COMPACT_OLD = r'''function compactRow(row,media){var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,260),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);if(row.size)out.size=s(row.size);if(Array.isArray(row.subtitles)&&row.subtitles.length)out.subtitles=row.subtitles.slice(0,20);return out}'''
COMPACT_NEW = r'''function compactRow(row,media){var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,260),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);var size=s(row.size||"");if(!size){var desc=s(row.description||""),lang=s(row.language||""),parts=[];if(desc&&!/^(?:unknown|inconnue?|n\/?a)$/i.test(desc))size=desc;else{if(lang)parts.push(lang);if(media.kind==="hls")parts.push("HLS");else if(media.kind)parts.push(media.kind.toUpperCase());size=parts.join(" • ")}}if(size)out.size=size;if(Array.isArray(row.subtitles)&&row.subtitles.length)out.subtitles=row.subtitles.slice(0,20);return out}'''

RESOLVE_OLD = r'''async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''
RESOLVE_NEW = r'''async function resolve(u,baseHeaders,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};jar=jar||[];if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer,jar);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen,jar)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''

TVROWS_OLD = r'''async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''
TVROWS_NEW = r'''async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url),jar=[];seedCookieHeader(jar,row.headers,row.url);jobs.push(resolve(row.url,row.headers,ref,0,{},jar).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''


def strip_legacy_direct_media(text: str, enabled: bool) -> str:
    if not enabled:
        return text
    while True:
        start = text.find(LEGACY_DIRECT_MEDIA_MARKER)
        if start < 0:
            return text
        call = text.find(LEGACY_DIRECT_MEDIA_CALL, start)
        if call < 0:
            raise RuntimeError("unterminated direct-media v2 wrapper: call boundary missing")
        end = text.find(");", call)
        if end < 0:
            raise RuntimeError("unterminated direct-media v2 wrapper: closing boundary missing")
        text = text[:start] + text[end + 2 :]


def strip_target_media_wrappers(text: str, enabled: bool) -> str:
    if not enabled:
        return text
    while True:
        start = text.find(TARGET_MEDIA_MARKER)
        if start < 0:
            return text.rstrip()
        call = text.find(TARGET_MEDIA_CALL, start)
        if call < 0:
            raise RuntimeError("unterminated target-media wrapper: call boundary missing")
        end = text.find(");", call)
        if end < 0:
            raise RuntimeError("unterminated target-media wrapper: closing boundary missing")
        text = (text[:start] + text[end + 2 :]).rstrip()


def rejected_v4(blocked_hosts: list[str]) -> str:
    payload = json.dumps(blocked_hosts, ensure_ascii=False, separators=(",", ":"))
    return (
        "function rejected(u){var h=hostname(u);"
        "if(!h||ASSET.test(u)||SOCIAL.test(h)||DEMO.test(u)||/\\/troll\\/master\\.m3u8(?:[?#]|$)/i.test(u)||/\\/(?:static\\/hero(?:[-_][^/?#]*)?\\.(?:mp4|webm|avif)|cdn-cgi\\/challenge-platform)(?:[?#]|$)/i.test(u)||/%7b|%7d|decodedlink|\\$\\{|encodeURIComponent\\(|credentials:/i.test(u))return true;"
        f"var blocked={payload};for(var bi=0;bi<blocked.length;bi++){{var rule=blocked[bi];if(h===rule||h.endsWith('.'+rule))return true}}"
        "return false}"
    )


def upgrade_fetch_capability(text: str) -> str:
    if FETCH_COMPAT_MARKER in text:
        return text
    if RESOURCE_V4 in text:
        return text.rstrip() + "\n" + FETCH_COMPAT_MARKER + "\n"
    count = text.count(RESOURCE_V3)
    if count != 1:
        raise RuntimeError(f"target media resource() capability anchor count={count}")
    return text.replace(RESOURCE_V3, RESOURCE_V4, 1).rstrip() + "\n" + FETCH_COMPAT_MARKER + "\n"


def upgrade_protocol_relative_urls(text: str) -> str:
    if PROTOCOL_RELATIVE_MARKER in text:
        return text
    if ABS_V4 in text:
        return text.rstrip() + "\n" + PROTOCOL_RELATIVE_MARKER + "\n"
    count = text.count(ABS_V3)
    if count != 1:
        raise RuntimeError(f"target media abs() capability anchor count={count}")
    return text.replace(ABS_V3, ABS_V4, 1).rstrip() + "\n" + PROTOCOL_RELATIVE_MARKER + "\n"


def upgrade_player_decoders(text: str, blocked_hosts: list[str]) -> str:
    start = text.find(VIDZY_DECODER_START)
    if start >= 0:
        end = text.find(VIDZY_DECODER_END, start)
        if end < 0:
            raise RuntimeError("target media v3 decoder found without genericUrls boundary")
        text = text[:start] + VIDZY_DECODER_V4 + LECTEURVIDEO_DECODER_V4 + text[end:]

    generic_start = text.find(GENERIC_URLS_START)
    if generic_start < 0:
        raise RuntimeError("target media genericUrls() not found")
    generic_end = text.find(GENERIC_URLS_END, generic_start)
    if generic_end < 0:
        raise RuntimeError("target media normalizeRows boundary not found")
    text = text[:generic_start] + GENERIC_URLS_V4 + text[generic_end:]

    if REJECTED_V3 in text:
        text = text.replace(REJECTED_V3, rejected_v4(blocked_hosts), 1)
    elif "function rejected(u){" in text and "var blocked=" not in text:
        raise RuntimeError("unrecognized target-media rejected() implementation")
    return text


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"target-media v5 {label} anchor count={count}")
    return text.replace(old, new, 1)


def upgrade_playback_context(text: str) -> str:
    if V5_MARKER in text:
        return text
    text = _replace_once(text, OUTPUT_OLD, OUTPUT_NEW, "headers")
    text = _replace_once(text, RESOURCE_V4, RESOURCE_NEW, "resource")
    text = _replace_once(text, COMPACT_OLD, COMPACT_NEW, "compact-row")
    text = _replace_once(text, RESOLVE_OLD, RESOLVE_NEW, "resolve")
    text = _replace_once(text, TVROWS_OLD, TVROWS_NEW, "tv-rows")
    return text.rstrip() + "\n" + V5_MARKER + "\n"


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {})
    if V4_MARKER in text:
        patched = upgrade_fetch_capability(text)
        patched = upgrade_protocol_relative_urls(patched)
        return upgrade_playback_context(patched)

    blocked_hosts = sorted(
        STRICT_BLOCKED_HOSTS
        | {str(value).lower().lstrip(".") for value in cfg.get("blocked_hosts", []) if str(value).strip()}
    )
    cfg["blocked_hosts"] = blocked_hosts
    text = strip_legacy_direct_media(text, bool(cfg.get("strip_legacy_direct_media_v2")))
    text = strip_target_media_wrappers(text, bool(cfg.get("force_rewrap_target_media", False)))
    patched = TARGET(text, options=cfg, **kwargs)
    patched = upgrade_fetch_capability(patched)
    patched = upgrade_protocol_relative_urls(patched)
    patched = upgrade_player_decoders(patched, blocked_hosts)
    patched = EXPOSE(patched)
    patched = FILTER(patched, options=cfg)
    patched = patched.rstrip() + "\n" + V4_MARKER + "\n"
    return upgrade_playback_context(patched)
