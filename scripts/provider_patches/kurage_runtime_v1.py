#!/usr/bin/env python3
"""NiakVIO-owned Kurage AniList/tRPC runtime.

Clean-room adapter from the observed public request contract:
Core metadata -> season-aware AniList identity -> Kurage tRPC catalogue+sub+dub
source batch -> source rows. The upstream obfuscated bundle is never embedded or
executed. Core owns timeout, cancellation, terminal HTTP/media validation and
final output.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.KURAGE.RUNTIME.V1"
MARKER = "NIAKVIO_KURAGE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_KURAGE_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function txt(v){return String(v==null?"":v).trim()}
function uniq(v){return Array.from(new Set((v||[]).filter(Boolean)))}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=txt((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"anime").toLowerCase();if(raw==="series")raw="tv";if(raw!=="tv"&&raw!=="anime")return null;var id=txt((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return null;return{type:raw,transport:"tv",tmdbId:id,season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1}}
function norm(v){return txt(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[’']/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
async function fetchJson(url,opt){try{var options=opt||{};options.headers=Object.assign({"User-Agent":c.userAgent,"Accept":"application/json, text/plain, */*","Accept-Language":"en-US,en;q=0.9","Origin":c.base,"Referer":c.base+"/"},options.headers||{});var r=typeof _fetch==="function"?await _fetch(url,options):await g.fetch(url,options);if(!r||r.ok===false)return null;return await r.json()}catch(_e){return null}}
async function metadata(q){var show=null,episode=null;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:String(q.tmdbId),mediaType:"tv",tmdbNamespace:"tv",season:q.season,episode:q.episode});show=z&&z.metadata||null;episode=z&&z.episodeMetadata||null}}catch(_e){}if(!show){try{if(typeof _tmdb==="function")show=await _tmdb(q.tmdbId,"tv")}catch(_e){}}if(!show){try{var ctx=g&&g.__nuvioMediaContext||{};show=ctx.tmdbMetadata||ctx.fixtureMetadata||null;episode=episode||ctx.episodeMetadata||null}catch(_e){}}return{show:show,episode:episode}}
function titles(meta){var out=[];if(meta){out.push(meta.name,meta.title,meta.original_name,meta.original_title);if(Array.isArray(meta.aliases))out=out.concat(meta.aliases)}return uniq(out.map(txt).filter(Boolean)).slice(0,6)}
function metaYear(md,q){var ep=md&&md.episode,show=md&&md.show,epYear=Number(txt(ep&&(ep.air_date||ep.release_date||ep.year)).slice(0,4))||0;if(q&&Number(q.season)>1&&epYear)return epYear;return Number(txt(show&&(show.first_air_date||show.release_date||show.year)).slice(0,4))||epYear||0}
function aniNames(row){return[row&&row.title&&row.title.english,row&&row.title&&row.title.romaji,row&&row.title&&row.title.native].map(txt).filter(Boolean)}
function seasonMarker(row){var names=aniNames(row);for(var i=0;i<names.length;i++){var value=names[i],m=/\bseason\s*(\d{1,2})\b/i.exec(value)||/\b(\d{1,2})(?:st|nd|rd|th)\s+season\b/i.exec(value)||/\bpart\s*(\d{1,2})\b/i.exec(value);if(m){var n=Number(m[1]);if(Number.isInteger(n)&&n>0&&n<50)return n}}return 0}
function sequel(row){var edges=row&&row.relations&&Array.isArray(row.relations.edges)?row.relations.edges:[];for(var i=0;i<edges.length;i++){var e=edges[i]||{},node=e.node||{};if(txt(e.relationType).toUpperCase()==="SEQUEL"&&node&&node.id)return node}return null}
var MEDIA_FIELDS="id type format title{romaji english native} startDate{year month day} endDate{year month day} episodes relations{edges{relationType node{id type format title{romaji english native} startDate{year month day} endDate{year month day} episodes}}}";
async function aniById(id){var query="query($id:Int){Media(id:$id,type:ANIME){"+MEDIA_FIELDS+"}}",data=await fetchJson(c.anilist,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:query,variables:{id:Number(id)}})});return data&&data.data&&data.data.Media||null}
async function advanceSeason(row,wantedSeason){var current=row,currentSeason=seasonMarker(row)||1;if(currentSeason>wantedSeason)return null;while(current&&currentSeason<wantedSeason){var next=sequel(current);if(!next&&current.id){var hydrated=await aniById(current.id);next=sequel(hydrated)}if(!next||!next.id)return null;current=next;currentSeason+=1}return currentSeason===wantedSeason?current:null}
async function anilist(title,year,season){var query="query($search:String){Page(perPage:20){media(search:$search,type:ANIME){"+MEDIA_FIELDS+"}}}",data=await fetchJson(c.anilist,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:query,variables:{search:title}})}),rows=data&&data.data&&data.data.Page&&data.data.Page.media;if(!Array.isArray(rows))return null;var target=norm(title),wanted=Math.max(1,Number(season)||1),best=null,bestScore=-1,bestMarker=0;for(var i=0;i<rows.length;i++){var r=rows[i]||{},names=aniNames(r).map(norm).filter(Boolean),score=0,marker=seasonMarker(r);if(names.indexOf(target)>=0)score+=300;else for(var j=0;j<names.length;j++){if(names[j].indexOf(target)>=0||target.indexOf(names[j])>=0)score=Math.max(score,180)}if(marker===wanted)score+=600;else if(marker>0&&marker!==wanted)score-=260;var rowYear=Number(r.startDate&&r.startDate.year)||0;if(year&&rowYear===year)score+=wanted>1?220:80;if(score>bestScore){best=r;bestScore=score;bestMarker=marker}}if(bestScore<80||!best)return null;if(wanted<=1)return best;if(bestMarker===wanted)return best;if(!bestMarker&&year&&Number(best.startDate&&best.startDate.year)===Number(year))return best;return await advanceSeason(best,wanted)}
function trpcUrl(id,episode){var input={"0":{json:{id:Number(id)}},"1":{json:{animeId:Number(id),episode:Number(episode),language:"sub"}},"2":{json:{animeId:Number(id),episode:Number(episode),language:"dub"}}};return c.base+c.trpcPath+"?batch=1&input="+encodeURIComponent(JSON.stringify(input))}
function mediaLike(url){return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/api\/proxy\//i.test(txt(url))}
function absoluteUrl(url){var u=txt(url);if(!u)return"";try{return new URL(u,c.base+"/").toString()}catch(_e){return""}}
function headerObject(obj){if(!obj||typeof obj!=="object"||Array.isArray(obj))return{};var src=obj.headers&&typeof obj.headers==="object"&&!Array.isArray(obj.headers)?obj.headers:{};var out={};for(var k in src){if(/^(?:referer|referrer|user-agent|origin|accept-language)$/i.test(k))out[k]=txt(src[k])}return out}
function walk(value,out,ctx,depth){if(depth>12||out.length>=24||value==null)return;if(Array.isArray(value)){for(var i=0;i<value.length;i++)walk(value[i],out,ctx,depth+1);return}if(typeof value!=="object")return;var localHeaders=Object.assign({},ctx.headers||{},headerObject(value));var lang=txt(value.language||value.lang||ctx.language||"");var quality=txt(value.quality||value.resolution||ctx.quality||"Auto");var keys=["url","file","src","source","stream","link","playbackUrl","playback_url"];for(var i=0;i<keys.length;i++){var u=value[keys[i]];if(typeof u==="string"){var resolved=absoluteUrl(u);if(resolved&&(mediaLike(resolved)||keys[i]!=="source"))out.push({url:resolved,headers:localHeaders,language:lang,quality:quality})}}for(var k in value){var child=value[k];if(child&&typeof child==="object")walk(child,out,{headers:localHeaders,language:lang||(/dub/i.test(k)?"English (DUB)":/sub/i.test(k)?"SUB":""),quality:quality},depth+1)}}
function dedupe(rows){var seen=new Set(),out=[];for(var i=0;i<rows.length;i++){var r=rows[i];if(!r||!/^https?:/i.test(txt(r.url)))continue;var key=txt(r.url);if(seen.has(key))continue;seen.add(key);out.push(r)}return out}
async function resolve(args,_ctx){var q=req(args);if(!q)return[];var md=await metadata(q),meta=md&&md.show,tt=titles(meta);if(!tt.length)return[];var year=metaYear(md,q),ani=null;for(var i=0;i<tt.length&&!ani;i++)ani=await anilist(tt[i],year,q.season);if(!ani||!ani.id)return[];var data=await fetchJson(trpcUrl(ani.id,q.episode),{headers:{"trpc-accept":"application/json","x-trpc-source":"nextjs-react"}});if(!data)return[];var rows=[];walk(data,rows,{},0);rows=dedupe(rows);var out=[];for(var j=0;j<rows.length&&out.length<c.targetStreams;j++){var r=rows[j],url=r.url,headers=Object.assign({Origin:c.base,Referer:c.base+"/"},r.headers||{});var item={name:"Kurage",title:"Kurage "+(r.language||"Auto"),url:url,quality:r.quality||"Auto",language:r.language||"",headers:headers,provider:"kurage",season:q.season,episode:q.episode,anilistId:Number(ani.id)};out.push(item)}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"kurage",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://kurage.live",
        "anilist": "https://graphql.anilist.co",
        "trpcPath": "/api/trpc/catalog.anilistInfo,episodes.source,episodes.source",
        "targetStreams": 6,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["targetStreams"] = max(1, min(8, int(cfg.get("targetStreams") or 6)))
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "anilist-kurage-trpc-v2-season-aware",
            "identity": "core-tmdb-season-episode-to-anilist-season-to-trpc",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "seasonAwareIdentity": True,
            "semanticLanes": ["anime"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
