#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIZONE.RUNTIME.V1"
MARKER = "NIAKVIO_ANIZONE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIZONE_RUNTIME_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function arr(v){return Array.isArray(v)?v:[]}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g,"")}
function abs(u,b){try{return new URL(s(u),b).toString()}catch(_e){return""}}
function attr(tag,key){var m=s(tag).match(new RegExp("\\b"+key+"\\s*=\\s*['\"]([^'\"]+)['\"]","i"));return m?s(m[1]):""}
function aliases(md){var out=[md&&md.title,md&&md.name,md&&md.original_title,md&&md.original_name],a=md&&md.alternative_titles&&(md.alternative_titles.results||md.alternative_titles.titles);if(Array.isArray(a))for(var i=0;i<a.length;i++)out.push(a[i]&&(a[i].title||a[i].name));var seen={},r=[];for(var j=0;j<out.length;j++){var x=s(out[j]);if(!x||seen[x])continue;seen[x]=1;r.push(x)}return r.slice(0,8)}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||{};var canonical=s((obj&&obj.canonicalMediaType)||ctx.canonicalMediaType).toLowerCase();if(canonical!=="anime")return null;var ns=s((obj&&obj.tmdbNamespace)||ctx.tmdbNamespace).toLowerCase();if(ns!=="movie"&&ns!=="tv")ns="tv";var season=Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode=Number((obj&&obj.episode)!=null?obj.episode:args[3])||1;var imdb=s((obj&&(obj.imdbId||obj.imdb_id))||ctx.imdbId||(md.external_ids&&md.external_ids.imdb_id));return{md:md,namespace:ns,season:season,episode:episode,imdbId:imdb,aliases:aliases(md)}}
function headers(ref){return{"User-Agent":c.userAgent,"Accept":"text/html,application/json,*/*","Accept-Language":"en-US,en;q=0.9","Referer":ref||c.base+"/"}}
async function jsonGet(url){try{var r=await g.fetch(url,{headers:headers(c.base+"/")});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function textGet(url,ref){try{var r=await g.fetch(url,{headers:headers(ref)});if(!r||!r.ok)return"";return await r.text()}catch(_e){return""}}
function scoreSnippet(snippet,titles){var n=norm(snippet),best=0;for(var i=0;i<titles.length;i++){var q=norm(titles[i]);if(!q)continue;if(n===q)best=Math.max(best,100);else if(n.indexOf(q)>=0||q.indexOf(n)>=0)best=Math.max(best,80);else{var words=s(titles[i]).toLowerCase().split(/[^a-z0-9]+/),hits=0;for(var w=0;w<words.length;w++)if(words[w].length>=3&&n.indexOf(norm(words[w]))>=0)hits++;best=Math.max(best,hits*12)}}return best}
function chooseSlug(html,titles){var re=/href=["'](?:https?:\/\/anizone\.to)?\/anime\/([^"'\/?#]+)(?:[\/?#][^"']*)?["']/gi,m,seen={},rows=[];while((m=re.exec(html))&&rows.length<100){var slug=s(m[1]);if(!slug||seen[slug])continue;seen[slug]=1;var start=Math.max(0,m.index-1000),end=Math.min(html.length,re.lastIndex+1800),snippet=html.slice(start,end);rows.push({slug:slug,score:scoreSnippet(slug+" "+snippet,titles)})}rows.sort(function(a,b){return b.score-a.score});return rows.length?rows[0].slug:""}
function decodeHtml(v){return s(v).replace(/&amp;/g,"&").replace(/&#0*38;/g,"&").replace(/&quot;/g,'"').replace(/&#0*39;/g,"'")}
function findMaster(html,base){var m=html.match(/<media-player[^>]*\bsrc=["']([^"']+)["']/i);if(!m)m=html.match(/https?:\/\/[^"'\s<>]+\.m3u8(?:\?[^"'\s<>]*)?/i);var u=m&&(m[1]||m[0]);return u?abs(decodeHtml(u),base):""}
function subtitles(html,base){var out=[],re=/<track\b[^>]*>/gi,m;while((m=re.exec(html))&&out.length<20){var tag=m[0],src=attr(tag,"src"),kind=attr(tag,"kind").toLowerCase();if(!src)continue;if(kind&&kind!=="subtitles"&&kind!=="captions"&&!/\.(?:ass|vtt)(?:[?#]|$)/i.test(src))continue;out.push({url:abs(decodeHtml(src),base),name:attr(tag,"label")||"Subtitle",language:attr(tag,"srclang")||"en"})}return out.filter(function(x){return!!x.url})}
async function resolve(args){var q=req(args);if(!q)return[];var title="",mappedEpisode=q.episode,mapping=null;if(q.namespace==="tv"){if(!/^tt\d+$/i.test(q.imdbId))return[];mapping=await jsonGet(c.mapping+"?id="+encodeURIComponent(q.imdbId)+"&s="+encodeURIComponent(q.season)+"&e="+encodeURIComponent(q.episode));if(!mapping||!mapping.mal_id)return[];mappedEpisode=Number(mapping.mal_episode)||q.episode;title=s(mapping.anime_title);if(!title){var mal=await jsonGet(c.jikan+encodeURIComponent(String(mapping.mal_id)));title=s(mal&&mal.data&&mal.data.title)}}else{title=s(q.md.title||q.md.original_title||q.aliases[0]);mappedEpisode=1}if(!title)return[];var query=s(mapping&&mapping.anime_title)||title.split(":")[0].trim(),searchUrl=c.base+"/anime?search="+encodeURIComponent(query),html=await textGet(searchUrl,c.base+"/");if(!html)return[];var titles=[title,query].concat(q.aliases),slug=chooseSlug(html,titles);if(!slug)return[];var epUrl=c.base+"/anime/"+encodeURIComponent(slug)+"/"+encodeURIComponent(String(mappedEpisode)),epHtml=await textGet(epUrl,searchUrl);if(!epHtml)return[];var master=findMaster(epHtml,epUrl);if(!master)return[];return[{name:c.name,title:c.name+" · "+title+" · E"+mappedEpisode,url:master,quality:"Multi",type:"m3u8",provider:c.provider,headers:headers(epUrl),subtitles:subtitles(epHtml,epUrl)}]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAniZoneRuntimeV1)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioAniZoneRuntimeV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://anizone.to",
        "mapping": "https://id-mapping-api-malid.hf.space/api/resolve",
        "jikan": "https://api.jikan.moe/v4/anime/",
        "provider": "anizone",
        "name": "AniZone",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3",
    }
    cfg.update(dict(options or {}))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtime": cfg,
            "identity": "core-tmdb-external-id-to-mal-to-provider-slug",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
