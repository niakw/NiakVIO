#!/usr/bin/env python3
"""NiakVIO-owned AniKotoTV identity -> MegaPlay runtime.

Current upstream no longer uses the historical AniKoto catalogue/AJAX routes.
The clean-room chain is:
  Core TMDB metadata -> public TMDB/MAL/AniList mapping -> MegaPlay stream page
  -> /stream/getSources -> terminal media.

No upstream provider JavaScript is embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIKOTOTV.RUNTIME.V2"
MARKER = "NIAKVIO_ANIKOTOTV_RUNTIME_V3"

WRAPPER = r'''
/* NIAKVIO_ANIKOTOTV_RUNTIME_V3 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||x.semanticType||x.canonicalMediaType||a[1]||"anime").toLowerCase();if(semantic==="tv")semantic="anime";if(semantic!=="anime")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{tmdbId:id,season:Number((o&&(o.season||o.seasonNumber))||x.season||a[2]||1)||1,episode:Number((o&&(o.episode||o.episodeNumber))||x.episode||a[3]||1)||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||x.tmdbMetadata||x.fixtureMetadata||null}}
function projected(v){if(v&&v.state==="ok"&&v.metadata)v=v.metadata;return v&&typeof v==="object"?v:null}
async function metadata(q){var m=projected(q.metadata);if(m)return m;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"});return projected(r)}}catch(_e){}return null}
function hdr(ref,extra){var h={"User-Agent":c.ua,"Accept":"application/json,text/html,*/*","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return Object.assign(h,extra||{})}
async function jsonGet(url,ref){try{var r=await g.fetch(url,{headers:hdr(ref),redirect:"follow"});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function textGet(url,ref,extra){try{var r=await g.fetch(url,{headers:hdr(ref,extra),redirect:"follow"});if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text(),headers:r.headers}}catch(_e){return null}}
function absoluteEpisode(q,m){var n=q.episode;if(q.season<=1)return n;var seasons=m&&Array.isArray(m.seasons)?m.seasons:[];for(var sn=1;sn<q.season;sn++){var hit=null;for(var i=0;i<seasons.length;i++)if(Number(seasons[i]&&seasons[i].season_number)===sn){hit=seasons[i];break}var count=Number(hit&&hit.episode_count);if(!count)return q.episode;n+=count}return n}
async function mapped(q){var u=c.mapping+"?id="+encodeURIComponent(q.tmdbId)+"&s="+encodeURIComponent(q.season)+"&e="+encodeURIComponent(q.episode),j=await jsonGet(u,"");if(!j||typeof j!=="object")return null;var mal=s(j.mal||j.mal_id||j.malId),ani=s(j.anilist||j.ani_id||j.aniId),ep=Number(j.episode||j.absoluteEpisode||j.absolute_episode||0);if(mal)return{kind:"mal",id:mal,episode:ep};if(ani)return{kind:"ani",id:ani,episode:ep};return null}
async function anilist(title){title=s(title);if(!title)return null;var query="query ($search: String) { Media (search: $search, type: ANIME) { id idMal } }";try{var r=await g.fetch("https://graphql.anilist.co",{method:"POST",headers:hdr("",{"Content-Type":"application/json","Accept":"application/json"}),body:JSON.stringify({query:query,variables:{search:title}})});if(!r||!r.ok)return null;var j=await r.json(),m=j&&j.data&&j.data.Media;if(!m)return null;if(m.idMal)return{kind:"mal",id:String(m.idMal),episode:0};if(m.id)return{kind:"ani",id:String(m.id),episode:0};return null}catch(_e){return null}}
function title(m){return s(m&&(m.name||m.title||m.original_name||m.original_title))}
function sourceFile(j){var src=j&&j.sources;if(src&&typeof src==="object"&&!Array.isArray(src)){var u=s(src.file||src.url||src.src);if(/^https?:\/\//i.test(u))return u}if(Array.isArray(src)){for(var i=0;i<src.length;i++){var r=src[i],u=s(r&&typeof r==="object"?(r.file||r.url||r.src):r);if(/^https?:\/\//i.test(u))return u}}return""}
function tracks(j){var out=[];for(var i=0;i<((j&&j.tracks)||[]).length;i++){var r=j.tracks[i]||{},u=s(r.file||r.url),kind=s(r.kind).toLowerCase();if(u&&(kind==="captions"||kind==="subtitles"))out.push({id:s(r.label||r.lang||"Subtitles"),url:u,language:s(r.srclang||r.lang||"eng")})}return out}
async function getSources(page,domain){var id=(String(page.text||"").match(/data-id=["'](\d+)["']/i)||[])[1]||"";if(!id){var im=(String(page.text||"").match(/<iframe[^>]+src=["']([^"']+)/i)||[])[1]||"";if(im){try{var iu=new URL(im,page.url).toString(),p2=await textGet(iu,page.url);if(p2){id=(String(p2.text||"").match(/data-id=["'](\d+)["']/i)||[])[1]||"";if(id)page=p2}}catch(_e){}}}if(!id)return null;try{var endpoint="https://"+domain+"/stream/getSources?id="+encodeURIComponent(id),r=await g.fetch(endpoint,{headers:hdr(page.url,{"X-Requested-With":"XMLHttpRequest"}),redirect:"follow"});if(!r||!r.ok)return null;var j=await r.json(),u=sourceFile(j);if(!u)return null;return{url:u,subtitles:tracks(j)}}catch(_e){return null}}
async function resolve(a){var q=req(a);if(!q)return null;var m=await metadata(q),identity=await mapped(q);if(!identity)identity=await anilist(title(m));if(!identity)return[];var ep=identity.episode||absoluteEpisode(q,m)||q.episode,out=[];for(var mi=0;mi<c.modes.length;mi++){var mode=c.modes[mi],pageUrl="https://"+c.domain+"/stream/"+identity.kind+"/"+encodeURIComponent(identity.id)+"/"+encodeURIComponent(ep)+"/"+mode,p=await textGet(pageUrl,"https://"+c.domain+"/");if(!p)continue;var src=await getSources(p,c.domain);if(!src)continue;out.push({name:"AniKotoTV | "+(mode==="sub"?"SUB":"DUB"),title:(title(m)||"AniKotoTV")+" | S"+q.season+"E"+q.episode+" | "+mode.toUpperCase(),url:src.url,quality:"Auto",language:mode==="sub"?"Japanese (SUB)":"English (DUB)",provider:"anikototv",isDirect:/\.(?:m3u8|mp4)(?:[?#]|$)/i.test(src.url),subtitles:src.subtitles,headers:{Referer:"https://"+c.domain+"/",Origin:"https://"+c.domain}})}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"anikototv",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "mapping": "https://arm.haglund.dev/api/v2/tmdb",
        "domain": "megaplay.buzz",
        "modes": ["sub", "dub"],
        "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
    }
    cfg.update(dict(options or {}))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "anikototv-tmdb-mal-anilist-megaplay-v3",
            "identity": "core-tmdb-to-mal-anilist",
            "semanticLanes": ["anime"],
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
