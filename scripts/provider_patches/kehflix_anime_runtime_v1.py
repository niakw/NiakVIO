#!/usr/bin/env python3
"""NiakVIO-owned Kehflix anime resolver for the current signed episode API.

Kehflix movie/TV already work through the generic ProviderBase path. The anime
payload differs: it currently exposes direct MP4 URLs that may be blocked to the
runner plus exact episode-correlated iframe players (not pre-wrapped stream-gw
URLs). This provider Lego handles semantic anime only and lets Core dispatch
fall back to the native runtime for every other lane.

The resolver derives the title slug from Core TMDB metadata, obtains the site's
short-lived signed title key from the exact title page, calls the exact episode
API, and prioritizes same-origin gateway rows / correlated players before raw
media. No provider response token, title, fixture id, player/CDN hostname or
media URL is baked into the patch.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.KEHFLIX.ANIME_RUNTIME.V1"
MARKER = "NIAKVIO_KEHFLIX_ANIME_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_KEHFLIX_ANIME_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function txt(v){return String(v==null?"":v).trim()}
function uniq(v){return Array.from(new Set((v||[]).filter(Boolean)))}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=txt((obj&&(obj.canonicalMediaType||obj.semanticType))||ctx.canonicalMediaType||ctx.mediaType||(obj&&(obj.mediaType||obj.type))||args[1]||"movie").toLowerCase();if(raw==="series")raw="tv";if(raw!=="anime")return null;var id=txt((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||(typeof first==="string"?first:"")||"");if(!/^\d+$/.test(id))return null;return{type:"anime",transport:"tv",tmdbId:id,season:Math.max(1,Number((obj&&obj.season)!=null?obj.season:args[2])||1),episode:Math.max(1,Number((obj&&obj.episode)!=null?obj.episode:args[3])||1)}}
function base(){var out="";try{out=txt(NIAKVIO_PROVIDER_MODEL.officialSite||NIAKVIO_PROVIDER_MODEL.knownSite)}catch(_e){}if(!out)out=txt(c.base);return out.replace(/\/$/,"")}
function slug(v){try{if(typeof _slug==="function")return _slug(v)}catch(_e){}return txt(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
async function response(url,opt){try{return typeof _fetch==="function"?await _fetch(url,opt||{}):await g.fetch(url,opt||{})}catch(_e){return null}}
async function metadata(q){var meta=null;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:String(q.tmdbId),mediaType:"tv",tmdbNamespace:"tv"});meta=z&&z.metadata||null}}catch(_e){}if(!meta){try{if(typeof _tmdb==="function")meta=await _tmdb(q.tmdbId,"tv")}catch(_e){}}if(!meta){try{var ctx=g&&g.__nuvioMediaContext||{};meta=ctx.tmdbMetadata||null}catch(_e){}}return meta}
function titles(meta){var out=[];if(meta){out.push(meta.title,meta.name,meta.original_title,meta.original_name);if(Array.isArray(meta.aliases))out=out.concat(meta.aliases)}return uniq(out.map(txt).filter(Boolean)).slice(0,6)}
function htmlDecode(v){return txt(v).replace(/&amp;|&#038;/gi,"&").replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'")}
function signedKeys(html){var source=txt(html),out=[],m,re1=/[?&]k=([^&"'<>\\\s]+)/gi,re2=/\bk\s*[:=]\s*["']([^"']{20,})["']/gi,re3=/([A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})/g;for(var r of [re1,re2,re3]){while((m=r.exec(source))!==null){var v=htmlDecode(m[1]);try{v=decodeURIComponent(v)}catch(_e){}if(v&&!out.includes(v))out.push(v);if(out.length>=12)break}if(out.length>=12)break}return out}
function abs(raw,b){var v=txt(raw);if(!v)return"";try{return new URL(v,b+"/").toString()}catch(_e){return""}}
function language(v){var x=txt(v).toLowerCase();if(x==="vf"||x==="vff"||x==="fr"||x==="french")return"fr";if(x.indexOf("vost")>=0)return"vostfr";return x||undefined}
function decorate(rows,source){var out=[];for(var i=0;i<(rows||[]).length;i++){var row=rows[i];if(!row||typeof row!=="object")continue;row.name=row.name||"Kehflix";row.title=row.title||("Kehflix"+(source&&source.quality&&source.quality!=="Unknown"?" "+txt(source.quality):""));row.language=row.language||language(source&&source.language);row.provider=row.provider||"kehflix";out.push(row)}return out}
function correlatedPlayer(url,referer,source){var rows=[];try{if(typeof _streams==="function")rows=_streams([url],referer)}catch(_e){}rows=decorate(rows,source);for(var i=0;i<rows.length;i++){if(rows[i]&&typeof rows[i]==="object")rows[i].__nuvioCorrelatedPlayerFallbackV1={url:url}}return rows}
async function crawl(url,referer,source,depth){try{if(typeof _crawlDirectMedia==="function"){var rows=await _crawlDirectMedia([url],referer,depth);if(rows&&rows.length)return decorate(rows,source)}}catch(_e){}return[]}
async function episodePayload(b,titleUrl,key,q){var u=b+"/api/streams/episode?id="+encodeURIComponent(q.tmdbId)+"&season="+encodeURIComponent(String(q.season))+"&episode="+encodeURIComponent(String(q.episode))+"&k="+encodeURIComponent(key),r=await response(u,{headers:{Referer:titleUrl}});if(!r||r.ok===false)return null;try{var d=await r.json();return d&&d.ok===true&&Array.isArray(d.sources)?d:null}catch(_e){return null}}
async function resolveSources(b,titleUrl,sources){var gateways=[],players=[],media=[];for(var i=0;i<sources.length&&i<16;i++){var s=sources[i];if(!s||typeof s!=="object")continue;var raw=txt(s.src||s.url),u=abs(raw,b);if(!u)continue;if(/^\/api\/stream-gw\?/i.test(raw)){gateways.push({url:u,source:s});continue}var isDirect=false,isPlayer=false;try{isDirect=typeof _directMedia==="function"&&_directMedia(u)}catch(_e){}try{isPlayer=typeof _playerLike==="function"&&_playerLike(u)}catch(_e){}if(txt(s.type).toLowerCase()==="iframe"||(!isDirect&&isPlayer))players.push({url:u,source:s});else if(/^https?:\/\//i.test(u))media.push({url:u,source:s})}
var out=[];
for(var gidx=0;gidx<gateways.length&&out.length<c.targetStreams;gidx++){var gr=gateways[gidx],rows=[];try{if(typeof _streams==="function")rows=_streams([gr.url],titleUrl)}catch(_e){}out=out.concat(decorate(rows,gr.source))}
for(var p=0;p<players.length&&out.length<c.targetStreams;p++){var pr=players[p],direct=await crawl(pr.url,titleUrl,pr.source,2);if(direct.length)out=out.concat(direct);else out=out.concat(correlatedPlayer(pr.url,titleUrl,pr.source))}
for(var m=0;m<media.length&&out.length<c.targetStreams;m++){var mr=media[m],found=await crawl(mr.url,titleUrl,mr.source,1);if(found.length)out=out.concat(found)}
return out.slice(0,c.targetStreams)}
async function resolve(args,_ctx){var q=req(args);if(q===null)return null;var b=base();if(!/^https?:\/\//i.test(b))return[];var meta=await metadata(q),tt=titles(meta);if(!tt.length)return[];for(var t=0;t<tt.length;t++){var s=slug(tt[t]);if(!s)continue;var titleUrl=b+"/title/tv/"+encodeURIComponent(q.tmdbId)+"-"+s,r=await response(titleUrl,{headers:{Referer:b+"/"}});if(!r||r.ok===false)continue;var html="";try{html=await r.text()}catch(_e){}var keys=signedKeys(html);for(var k=0;k<keys.length;k++){var payload=await episodePayload(b,titleUrl,keys[k],q);if(!payload)continue;var rows=await resolveSources(b,titleUrl,payload.sources);if(rows.length)return rows}}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"kehflix",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {"base": "", "targetStreams": 4}
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["targetStreams"] = max(1, min(8, int(cfg.get("targetStreams") or 4)))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "signed-title-episode-api-v1",
            "identity": "core-tmdb-tv-metadata-to-current-title-page",
            "semanticLanes": ["anime"],
            "nativeDelegation": ["movie", "tv"],
            "semanticTransportBoundary": "prefer-core-canonical-anime-over-provider-tv-transport",
            "sourcePriority": ["same-origin-gateway", "episode-correlated-player", "verified-direct-media"],
            "correlatedPlayerFallback": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "fixtureHardcodes": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
