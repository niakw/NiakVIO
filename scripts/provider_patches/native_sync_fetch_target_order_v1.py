#!/usr/bin/env python3
"""Make target-media traversal safe on NuvioTV's synchronous native fetch bridge.

Desktop/Mobile can launch target-media probes concurrently. NuvioTV's pinned
QuickJS bridge enters __native_fetch synchronously, so Promise.all does not
protect us from an early dead third-party embed monopolising the native network
timeout before a later first-party wrapper/direct HLS candidate is even tried.

This source transform keeps the normal concurrent path on non-TV runtimes. On
TV it orders candidates by evidence strength (direct media, same-origin wrapper,
then external player) and returns as soon as one strict media proof succeeds.
The strict resource/proof functions remain unchanged: this only changes traversal
order and budget consumption, never what counts as valid media.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_NATIVE_SYNC_FETCH_TARGET_ORDER_V1"
TARGET_MARKER = "NUVIO_TV_TARGET_MEDIA_V4"

OLD_RESOLVE = r'''async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var next=genericUrls(body,r.url||u),groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,r.url||u,depth+1,seen)})),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''

OLD_TV_ROWS = r'''async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''

HELPERS = r'''function serialNativeTargetRuntime(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative}catch(_e){return false}}
function targetRank(u,ref){u=s(u);if(/(?:\.m3u8|\.mpd)(?:[?#]|$)|\/hls2?\//i.test(u))return 0;var h=hostname(u),rh=hostname(ref);if(h&&rh&&h===rh)return 1;if(/(?:^|\.)(?:vidzy\.(?:org|live|cc)|fsvid\.lol|uqload\.(?:is|co|cx)|lecteurvideo\.com|xtremestream\.xyz|megaup\.net|veev\.to|veevcdn\.co|waaw\.to|lulustream\.com|luluvdo\.com|vidmoly\.(?:me|biz)|emmmmbed\.com|ironwallnet\.net)$/i.test(h))return 2;if(/(?:\/embed(?:[-./?]|$)|\/player(?:[-./?]|$)|\/e\/|\/f\/|\/video\.php(?:[?#]|$)|download\.megaup)/i.test(u))return 3;return 4}
function orderedTargets(values,ref){return (values||[]).map(function(v,i){return{v:v,i:i,r:targetRank(v,ref)}}).sort(function(a,b){return(a.r-b.r)||(a.i-b.i)}).map(function(x){return x.v})}
function orderedNativeRows(values){var out=[];(values||[]).slice(0,c.maxCandidates).forEach(function(raw,i){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);out.push({row:row,ref:ref,i:i,r:targetRank(row.url,ref)})});out.sort(function(a,b){return(a.r-b.r)||(a.i-b.i)});return out}'''

NEW_RESOLVE = r'''async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var r=await resource(u,baseHeaders,referer);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:r.headers}];var type=s(r.type).toLowerCase(),body=r.text||"";if(!body||(!/text|html|json|javascript|xml/i.test(type)&&!/[<>{}\[\]"']/.test(body)))return[];var ref=r.url||u,next=orderedTargets(genericUrls(body,ref),ref),out=[];if(serialNativeTargetRuntime()){for(var i=0;i<next.length;i++){var found=await resolve(next[i],r.headers,ref,depth+1,seen);if(found.length)return unique(found)}return[]}var groups=await Promise.all(next.map(function(v){return resolve(v,r.headers,ref,depth+1,seen)}));groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''

NEW_TV_ROWS = r'''async function tvRows(old,self,args){var native=await invoke(old,self,args),ordered=orderedNativeRows(native),out=[];if(serialNativeTargetRuntime()){for(var i=0;i<ordered.length;i++){var item=ordered[i],found=await resolve(item.row.url,item.row.headers,item.ref,0,{});if(found.length){found.forEach(function(media){out.push(compactRow(item.row,media))});return unique(out)}}return[]}var jobs=ordered.map(function(item){return resolve(item.row.url,item.row.headers,item.ref,0,{}).then(function(found){return found.map(function(media){return compactRow(item.row,media)})})}),groups=await Promise.all(jobs);groups.forEach(function(group){out=out.concat(group)});return unique(out)}'''


def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    if MARKER in source:
        return source
    if TARGET_MARKER not in source:
        return source
    resolve_count = source.count(OLD_RESOLVE)
    rows_count = source.count(OLD_TV_ROWS)
    if resolve_count != 1 or rows_count != 1:
        raise RuntimeError(
            f"target-media traversal anchors changed: resolve={resolve_count} tvRows={rows_count}"
        )
    patched = source.replace(OLD_RESOLVE, HELPERS + "\n" + NEW_RESOLVE, 1)
    patched = patched.replace(OLD_TV_ROWS, NEW_TV_ROWS, 1)
    return patched.rstrip() + f"\n/* {MARKER} */\n"
