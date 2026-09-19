#!/usr/bin/env python3
"""Clean VidFast multi-authority page -> enc/dec API -> terminal stream runtime."""
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
function headers(base,extra){return Object.assign({"User-Agent":c.userAgent,"Referer":s(base).replace(/\/$/,"")+"/","X-Requested-With":"XMLHttpRequest","Accept":"*/*"},extra||{})}
function req(args){var f=args[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var type=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(type==="series")type="tv";if(type!=="movie"&&type!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;var season=Number((o&&(o.season||o.seasonNumber))||ctx.season||args[2]||0),episode=Number((o&&(o.episode||o.episodeNumber))||ctx.episode||args[3]||0);if(type==="tv"&&(!season||!episode))return null;return{type:type,id:id,season:season,episode:episode}}
function abs(value,base){try{return new URL(s(value),s(base).replace(/\/$/,"")+"/").toString()}catch(_e){return s(value)}}
function route(row,q){var p=q.type==="movie"?s(row.movie):s(row.tv);if(!p)return"";return s(row.base).replace(/\/$/,"")+p.replace(/\{id\}/g,encodeURIComponent(q.id)).replace(/\{season\}/g,encodeURIComponent(q.season)).replace(/\{episode\}/g,encodeURIComponent(q.episode))}
async function text(url,opt){try{var r=await g.fetch(url,opt||{});return r&&r.ok?await r.text():""}catch(_e){return""}}
async function jsonReq(url,opt){try{var r=await g.fetch(url,opt||{});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function unescapeJsonString(v){try{return JSON.parse('"'+String(v||"").replace(/"/g,'\\"')+'"')}catch(_e){return String(v||"").replace(/\\\//g,"/").replace(/\\u0026/g,"&").replace(/\\u003d/gi,"=").replace(/\\u002f/gi,"/")}}
function encryptedToken(html){var raw=String(html||""),patterns=[/\\?"en\\?"\s*:\s*\\?"([^"\\]*(?:\\.[^"\\]*)*)\\?"/i,/"en"\s*:\s*"([^"]+)"/i],m;for(var i=0;i<patterns.length;i++){m=patterns[i].exec(raw);if(m&&m[1])return unescapeJsonString(m[1])}return""}
async function decrypt(value,base){if(!value)return null;return await jsonReq(c.decrypt+"/dec-vidfast",{method:"POST",headers:headers(base,{"Content-Type":"application/json"}),body:JSON.stringify({text:value,version:"1"})})}
function quality(row){var blob=s((row&&row.description)||"")+" "+s((row&&row.name)||"");if(row&&row["4kAvailable"]===true||/\b(?:2160|4k)\b/i.test(blob))return"2160p";var m=blob.match(/\b(1080|720|480|360)p?\b/i);return m?m[1]+"p":"Auto"}
async function genericCrawl(page,base){if(typeof _crawlDirectMedia!=="function")return[];try{var rows=await _crawlDirectMedia([page],page,2),out=[],seen={};for(var i=0;i<(rows||[]).length&&out.length<c.maxStreams;i++){var r=rows[i]||{},u=s(r.url);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;out.push({name:"VidFast",title:"VidFast"+(r.quality?" - "+r.quality:""),url:u,quality:s(r.quality||"Auto"),language:s(r.language||""),provider:"vidfast",isDirect:/\.(?:m3u8|mp4)(?:[?#]|$)/i.test(u),headers:headers(base)})}return out}catch(_e){return[]}}
async function resolveBase(row,q){var base=s(row.base).replace(/\/$/,""),page=route(row,q);if(!base||!page)return[];var html=await text(page,{headers:headers(base)});if(!html)return[];var token=encryptedToken(html);if(!token)return await genericCrawl(page,base);var enc=await jsonReq(c.decrypt+"/enc-vidfast?text="+encodeURIComponent(token)+"&version=1",{headers:headers(base)}),root=enc&&(enc.result||enc.data||enc);if(!root||!root.stream||!root.servers)return[];var csrf=s(root.csrf),h=headers(base,csrf?{"X-CSRF-Token":csrf}:{}),streamUrl=abs(root.stream,base),serverBase=abs(root.servers,base).replace(/\/$/,""),encryptedServers=await text(streamUrl,{method:"POST",headers:h}),serverDecoded=await decrypt(encryptedServers,base),servers=serverDecoded&&(serverDecoded.result||serverDecoded.data||serverDecoded);if(!Array.isArray(servers))return[];var out=[],seen={};for(var i=0;i<servers.length&&out.length<c.maxStreams;i++){var item=servers[i]||{},data=s(item.data);if(!data)continue;var endpoint=serverBase+"/"+data,encrypted=await text(endpoint,{method:"POST",headers:h});if(!encrypted)continue;var dec=await decrypt(encrypted,base),result=dec&&(dec.result||dec.data||dec),url=s(result&&result.url);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;var ql=quality(Object.assign({},item,result||{}));out.push({name:"VidFast",title:"VidFast"+(ql!=="Auto"?" - "+ql:""),url:url,quality:ql,provider:"vidfast",isDirect:/\.(?:m3u8|mp4)(?:[?#]|$)/i.test(url),headers:h})}return out}
async function resolve(args){var q=req(args);if(!q)return null;for(var i=0;i<c.bases.length;i++){var out=await resolveBase(c.bases[i],q);if(out.length)return out}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"vidfast",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "bases": [
            {"base": "https://vidfast.to", "movie": "/embed/movie/{id}", "tv": "/embed/tv/{id}/{season}/{episode}"},
            {"base": "https://vidfast.vc", "movie": "/movie/{id}/", "tv": "/tv/{id}/{season}/{episode}/"},
        ],
        "decrypt": "https://enc-dec.app/api",
        "maxStreams": 8,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    bases = cfg.get("bases") if isinstance(cfg.get("bases"), list) else []
    if not bases and cfg.get("base"):
        bases = [{"base": cfg.get("base"), "movie": "/movie/{id}/", "tv": "/tv/{id}/{season}/{episode}/"}]
    cfg["bases"] = [
        {
            "base": str(row.get("base") or "").rstrip("/"),
            "movie": str(row.get("movie") or "/movie/{id}/"),
            "tv": str(row.get("tv") or "/tv/{id}/{season}/{episode}/"),
        }
        for row in bases
        if isinstance(row, dict) and str(row.get("base") or "").strip()
    ]
    cfg.pop("base", None)
    cfg["decrypt"] = str(cfg.get("decrypt") or "").rstrip("/")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "vidfast-multibase-page-encdec-csrf-v2",
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
