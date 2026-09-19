#!/usr/bin/env python3
"""Clean VidFast page -> enc/dec API -> terminal stream runtime."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDFAST.RUNTIME.V1"
MARKER = "NIAKVIO_VIDFAST_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VIDFAST_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function headers(extra){return Object.assign({"User-Agent":c.userAgent,"Referer":c.base+"/","X-Requested-With":"XMLHttpRequest","Accept":"*/*"},extra||{})}
function req(args){var f=args[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var type=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(type==="series")type="tv";if(type!=="movie"&&type!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;var season=Number((o&&(o.season||o.seasonNumber))||ctx.season||args[2]||0),episode=Number((o&&(o.episode||o.episodeNumber))||ctx.episode||args[3]||0);if(type==="tv"&&(!season||!episode))return null;return{type:type,id:id,season:season,episode:episode}}
async function text(url,opt){try{var r=await g.fetch(url,opt||{headers:headers()});return r&&r.ok?await r.text():""}catch(_e){return""}}
async function jsonReq(url,opt){try{var r=await g.fetch(url,opt||{headers:headers()});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function unescapeJsonString(v){try{return JSON.parse('"'+String(v||"").replace(/"/g,'\\"')+'"')}catch(_e){return String(v||"").replace(/\\\//g,"/").replace(/\\u0026/g,"&").replace(/\\u003d/gi,"=").replace(/\\u002f/gi,"/")}}
function encryptedToken(html){var raw=String(html||""),patterns=[/\\?"en\\?"\s*:\s*\\?"([^"\\]*(?:\\.[^"\\]*)*)\\?"/i,/"en"\s*:\s*"([^"]+)"/i],m;for(var i=0;i<patterns.length;i++){m=patterns[i].exec(raw);if(m&&m[1])return unescapeJsonString(m[1])}return""}
async function decrypt(value){if(!value)return null;return await jsonReq(c.decrypt+"/dec-vidfast",{method:"POST",headers:headers({"Content-Type":"application/json"}),body:JSON.stringify({text:value,version:"1"})})}
function quality(row){var blob=s((row&&row.description)||"")+" "+s((row&&row.name)||"");if(row&&row["4kAvailable"]===true||/\b(?:2160|4k)\b/i.test(blob))return"2160p";var m=blob.match(/\b(1080|720|480|360)p?\b/i);return m?m[1]+"p":"Auto"}
async function resolve(args){var q=req(args);if(!q)return null;var page=q.type==="movie"?c.base+"/movie/"+q.id+"/":c.base+"/tv/"+q.id+"/"+q.season+"/"+q.episode+"/",html=await text(page,{headers:headers()});if(!html)return[];var token=encryptedToken(html);if(!token)return[];var enc=await jsonReq(c.decrypt+"/enc-vidfast?text="+encodeURIComponent(token)+"&version=1",{headers:headers()});var root=enc&&(enc.result||enc.data||enc);if(!root||!root.stream||!root.servers)return[];var csrf=s(root.csrf),h=headers(csrf?{"X-CSRF-Token":csrf}:{}),encryptedServers=await text(root.stream,{method:"POST",headers:h}),serverDecoded=await decrypt(encryptedServers),servers=serverDecoded&&(serverDecoded.result||serverDecoded.data||serverDecoded);if(!Array.isArray(servers))return[];var out=[],seen={};for(var i=0;i<servers.length&&out.length<c.maxStreams;i++){var row=servers[i]||{},data=s(row.data);if(!data)continue;var endpoint=s(root.servers).replace(/\/$/,"")+"/"+data,encrypted=await text(endpoint,{method:"POST",headers:h});if(!encrypted)continue;var dec=await decrypt(encrypted),result=dec&&(dec.result||dec.data||dec),url=s(result&&result.url);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;var ql=quality(Object.assign({},row,result||{}));out.push({name:"VidFast",title:"VidFast"+(ql!=="Auto"?" - "+ql:""),url:url,quality:ql,provider:"vidfast",isDirect:/\.(?:m3u8|mp4)(?:[?#]|$)/i.test(url),headers:h})}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"vidfast",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://vidfast.vc",
        "decrypt": "https://enc-dec.app/api",
        "maxStreams": 8,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["decrypt"] = str(cfg.get("decrypt") or "").rstrip("/")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "vidfast-page-encdec-csrf-v1",
            "identity": "tmdb-direct",
            "semanticLanes": ["movie", "tv"],
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
