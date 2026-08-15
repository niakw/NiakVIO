#!/usr/bin/env python3
"""Upgrade the strict NuvioTV target-media resolver with playback context.

V4 already handles the pinned TV runtime's text-only fetch Response and broken
protocol-relative URL polyfill.  V5 keeps those guarantees and fixes the
remaining site -> player/embed -> final-media gap: the immediate Referer/Origin
is refreshed on every hop, the browser User-Agent is carried into the final
row, and Set-Cookie values observed while traversing the player chain are kept
in a small per-row, domain/path-scoped jar and emitted as Cookie only for a
matching descendant request.  This is intentionally ephemeral and never shared
between providers or rows.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem + "_v5base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V4 = _load_module(ROOT / "nuvio_tv_target_media_v4.py")
MARKER = "/* NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT */"

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

RESOURCE_OLD = V4.RESOURCE_V4
RESOURCE_NEW = r'''async function resource(u,base,ref,jar){try{var h=probeHeaders(base,ref,u,jar),r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var finalUrl=s(r.url||u);captureCookies(jar,r,finalUrl);var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",bytes=null,text="";if(typeof r.arrayBuffer==="function"){var buffer=await r.arrayBuffer();bytes=new Uint8Array(buffer);text=decode(bytes.slice(0,300000))}else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}return{ok:!!r.ok,status:r.status,url:finalUrl,type:type,bytes:bytes,text:text,headers:outputHeaders(base,ref,finalUrl,jar)}}catch(_){return null}}'''

COMPACT_OLD = r'''function compactRow(row,media){var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,260),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);if(row.size)out.size=s(row.size);if(Array.isArray(row.subtitles)&&row.subtitles.length)out.subtitles=row.subtitles.slice(0,20);return out}'''
COMPACT_NEW = r'''function compactRow(row,media){var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,260),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);var size=s(row.size||"");if(!size){var desc=s(row.description||""),lang=s(row.language||""),parts=[];if(desc&&!/^(?:unknown|inconnue?|n\/?a)$/i.test(desc))size=desc;else{if(lang)parts.push(lang);if(media.kind==="hls")parts.push("HLS");else if(media.kind)parts.push(media.kind.toUpperCase());size=parts.join(" • ")}}if(size)out.size=size;if(Array.isArray(row.subtitles)&&row.subtitles.length)out.subtitles=row.subtitles.slice(0,20);return out}'''

RESOLVE_OLD = r'''async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''
RESOLVE_NEW = r'''async function resolve(u,baseHeaders,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};jar=jar||[];if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer,jar);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen,jar)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''

TVROWS_OLD = r'''async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''
TVROWS_NEW = r'''async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url),jar=[];seedCookieHeader(jar,row.headers,row.url);jobs.push(resolve(row.url,row.headers,ref,0,{},jar).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"target-media v5 {label} anchor count={count}")
    return text.replace(old, new, 1)


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    patched = V4.apply(text, options=options, **kwargs)
    if MARKER in patched:
        return patched
    patched = _replace_once(patched, OUTPUT_OLD, OUTPUT_NEW, "headers")
    patched = _replace_once(patched, RESOURCE_OLD, RESOURCE_NEW, "resource")
    patched = _replace_once(patched, COMPACT_OLD, COMPACT_NEW, "compact-row")
    patched = _replace_once(patched, RESOLVE_OLD, RESOLVE_NEW, "resolve")
    patched = _replace_once(patched, TVROWS_OLD, TVROWS_NEW, "tv-rows")
    return patched.rstrip() + "\n" + MARKER + "\n"
