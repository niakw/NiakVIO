#!/usr/bin/env python3
"""MovieBox official H5 runtime from a Nuvio TMDB identity.

The runtime keeps TMDB as the provider input.  It first consumes Core-owned
metadata when available; otherwise it reads the public TMDB title page (no API
credential) to obtain the factual title/year.  It then uses MovieBox's official
H5 BFF bootstrap/search/domain/play chain and returns only direct media rows.
No fixture IDs, titles, bearer tokens or third-party TMDB credentials are stored
in the bundle.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIEBOX.H5.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIEBOX_H5_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MOVIEBOX_H5_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function S(v){return String(v==null?"":v).trim()}
function N(v){try{return S(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return S(v).toLowerCase()}}
function A(a){var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=S((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.mediaType||"").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv")return null;var id=S((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{type:raw,tmdbId:id,season:raw==="movie"?0:(Number((o&&o.season)!=null?o.season:a[2])||1),episode:raw==="movie"?0:(Number((o&&o.episode)!=null?o.episode:a[3])||1)}}
function signal(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.requestTimeoutMs):undefined}catch(_e){return undefined}}
function expired(){try{var d=Number(g&&g.__nuvioProviderDeadlineMs);return Number.isFinite(d)&&d>0&&Date.now()>=d}catch(_e){return false}}
function entity(v){return S(v).replace(/&amp;/gi,"&").replace(/&#0*39;|&apos;/gi,"'").replace(/&quot;/gi,'"').replace(/&lt;/gi,"<").replace(/&gt;/gi,">")}
async function fetchText(url,opt){if(expired())return null;try{var x=Object.assign({},opt||{});var sg=signal();if(sg)x.signal=sg;x.redirect="follow";var r=await g.fetch(url,x);if(!r||!r.ok)return null;return{response:r,text:await r.text(),url:S(r.url||url)}}catch(_e){return null}}
function coreMeta(q){return(async function(){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type});if(z&&z.metadata)return z.metadata}}catch(_e){}try{var x=g&&g.__nuvioMediaContext||{},d=x.tmdbMetadata;if(d&&d.state==="ok"&&d.metadata)d=d.metadata;if(d)return d}catch(_e){}return null})()}
function titleFromMeta(d){if(!d)return null;var title=S(d.title||d.name||d.original_title||d.original_name),date=S(d.release_date||d.first_air_date),year=Number(date.slice(0,4))||0;return title?{title:title,year:year}:null}
async function publicTmdb(q){var url="https://www.themoviedb.org/"+(q.type==="movie"?"movie":"tv")+"/"+encodeURIComponent(q.tmdbId)+"?language=en-US",r=await fetchText(url,{headers:{"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9"}});if(!r)return null;var h=r.text,m=/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)["']/i.exec(h)||/<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:title["']/i.exec(h),t=m?entity(m[1]):"",tag=/<title[^>]*>([^<]+)<\/title>/i.exec(h),full=tag?entity(tag[1]):"",ym=/\(((?:19|20)\d{2})\)/.exec(full);if(!t&&full)t=full.replace(/\s*[—|-]\s*The Movie Database.*$/i,"").replace(/\s*\((?:19|20)\d{2}\)\s*$/,"").trim();return t?{title:t,year:ym?Number(ym[1]):0}:null}
async function identity(q){var m=titleFromMeta(await coreMeta(q));return m||await publicTmdb(q)}
function baseHeaders(origin){return{"User-Agent":c.userAgent,"Referer":origin+"/","Origin":origin,"X-Client-Info":c.clientInfo,"X-Request-Lang":"en","Accept":"application/json","Content-Type":"application/json"}}
async function req(state,url,opt,origin){if(expired())return null;origin=S(origin||c.siteOrigin).replace(/\/$/,"");var x=Object.assign({},opt||{}),h=Object.assign({},baseHeaders(origin),x.headers||{});if(state.token)h.Authorization="Bearer "+state.token;x.headers=h;var r=await fetchText(url,x);if(!r)return null;try{var xu=r.response&&r.response.headers&&typeof r.response.headers.get==="function"&&r.response.headers.get("x-user");if(xu){var j=JSON.parse(xu);if(j&&j.token)state.token=S(j.token)}}catch(_e){}var data={};try{data=JSON.parse(r.text)}catch(_e){}return{response:r.response,json:data,text:r.text,url:r.url}}
function rows(j){var d=j&&j.data||{};return Array.isArray(d.items)?d.items:Array.isArray(d.list)?d.list:[]}
function pick(items,id){var want=N(id.title),year=Number(id.year)||0,best=null,bestScore=-1;for(var i=0;i<items.length;i++){var x=items[i]||{},got=N(x.title),score=got===want?120:(got&&want&&(got.indexOf(want)>=0||want.indexOf(got)>=0)?80:-1),date=S(x.releaseDate||x.release_date),y=Number(date.slice(0,4))||0;if(score<0)continue;if(year&&y){if(year===y)score+=25;else score-=40}if(x.hasResource===true)score+=5;if(score>bestScore){best=x;bestScore=score}}return bestScore>=80?best:null}
function mediaRows(data,referer){var sets=[data&&data.streams,data&&data.hls,data&&data.dash],out=[],seen={};for(var si=0;si<sets.length;si++){var a=Array.isArray(sets[si])?sets[si]:[];for(var i=0;i<a.length;i++){var x=a[i]||{},u=S(x.url||x.path||x.file||x.streamUrl);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;var q=S(x.resolutions||x.resolution||x.quality||x.label||"HD"),lang=S(x.language||x.lang||x.audio||x.audioTrack||x.dub||"Original");out.push({name:"MovieBox | "+q,title:"MovieBox | "+q,url:u,quality:q,language:lang,headers:{"User-Agent":c.userAgent,"Referer":referer},provider:"moviebox",isDirect:true});if(out.length>=c.maxStreams)return out}}return out}
async function resolve(args,_ctx){var q=A(args);if(!q)return[];var state={token:""},started=Date.now(),pair=await Promise.all([identity(q),req(state,c.apiBase+"/home?host="+encodeURIComponent(c.siteHost),{},c.siteOrigin)]),id=pair[0],boot=pair[1];if(!id||!id.title||!boot||!state.token||expired())return[];var search=await req(state,c.apiBase+"/subject/search",{method:"POST",body:JSON.stringify({keyword:id.title,page:1,perPage:20})},c.siteOrigin);if(!search)return[];var subject=pick(rows(search.json),id);if(!subject)return[];var sid=S(subject.subjectId),detail=S(subject.detailPath);if(!sid||!detail)return[];var dom=await req(state,c.apiBase+"/media-player/get-domain",{},c.siteOrigin),domain=S(dom&&dom.json&&dom.json.data).replace(/\/$/,"");if(!domain||expired())return[];var ref=domain+"/spa/videoPlayPage/movies/"+detail+"?id="+encodeURIComponent(sid)+"&type=/movie/detail&detailSe="+q.season+"&detailEp="+q.episode+"&lang=en",play=await req(state,domain+"/wefeed-h5api-bff/subject/play?subjectId="+encodeURIComponent(sid)+"&se="+q.season+"&ep="+q.episode+"&detailPath="+encodeURIComponent(detail),{headers:{Referer:ref,Origin:domain,"X-Source":""}},domain);var data=play&&play.json&&play.json.data||{};if(!data.hasResource)return[];var out=mediaRows(data,ref);try{if(g)g.__niakvioMovieBoxLastProof={tmdbId:q.tmdbId,type:q.type,count:out.length,durationMs:Date.now()-started,title:id.title}}catch(_e){}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"moviebox",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "apiBase": "https://h5-api.aoneroom.com/wefeed-h5api-bff",
        "siteOrigin": "https://moviebox.ph",
        "siteHost": "moviebox.ph",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148 Safari/537.36",
        "clientInfo": '{"timezone":"Europe/Paris"}',
        "requestTimeoutMs": 7000,
        "maxStreams": 8,
    }
    cfg.update(dict(options or {}))
    cfg["requestTimeoutMs"] = max(2500, min(8000, int(cfg.get("requestTimeoutMs") or 7000)))
    cfg["maxStreams"] = max(1, min(12, int(cfg.get("maxStreams") or 8)))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "moviebox-official-h5-v1",
            "identity": "tmdb-direct-to-core-metadata-or-public-tmdb-title",
            "semanticLanes": ["movie", "tv"],
            "officialChain": ["tmdb-public-title-fallback", "moviebox-h5-bootstrap", "subject-search", "media-domain", "subject-play"],
            "embeddedCredential": False,
            "fixtureHardcodes": False,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
