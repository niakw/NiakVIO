#!/usr/bin/env python3
"""NiakVIO-owned AnimeVOSTFR current-site runtime.

Clean-room execution chain:
TMDB/Core metadata -> site search -> /animes/ page -> exact episode page ->
trembed/player tab -> external iframe -> bounded Core media crawler.
No upstream JavaScript is embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMEVOSTFR.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMEVOSTFR_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMEVOSTFR_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function uniq(a){return Array.from(new Set((a||[]).filter(Boolean)))}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[’']/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function abs(v,b){try{return new URL(s(v),b||c.base).toString()}catch(_e){return""}}
function visible(v){var src=String(v==null?"":v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return s(out).replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\s+/g," ").trim()}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g.__nuvioMediaContext||{}}catch(_e){}var semantic=s((o&&o.semanticType)||x.semanticType||"").toLowerCase(),raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.mediaType||semantic||"anime").toLowerCase();if(raw==="series")raw="tv";if(semantic==="anime"||raw==="tv")raw="anime";if(raw!=="anime")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{tmdbId:id,type:"anime",transport:"tv",season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1}}
function hdr(ref,accept){var h={"User-Agent":c.ua,"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function text(url,opt){try{var o=Object.assign({redirect:"follow"},opt||{});o.headers=Object.assign(hdr(o.referer||""),o.headers||{});delete o.referer;var r=typeof _fetch==="function"?await _fetch(url,o):await g.fetch(url,o);if(!r||r.ok===false)return null;return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
async function metadata(q){try{var fn=g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.transport,tmdbNamespace:q.transport}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var x=g.__nuvioMediaContext||{};return x.tmdbMetadata||x.fixtureMetadata||null}catch(_e){return null}}
function titles(m){var a=[];if(m){a.push(m.name,m.title,m.original_name,m.original_title);if(Array.isArray(m.aliases))a=a.concat(m.aliases);var alt=m.alternative_titles&&(m.alternative_titles.titles||m.alternative_titles.results);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)a.push(alt[i]&&(alt[i].title||alt[i].name))}return uniq(a.map(s)).filter(Boolean).slice(0,6)}
function score(label,wanted){var a=norm(label),b=norm(wanted);if(!a||!b)return 0;if(a===b)return 120;if(a.indexOf(b)===0||b.indexOf(a)===0)return 90;var aa=a.split(" ").filter(Boolean),bb=b.split(" ").filter(Boolean),hit=aa.filter(function(t){return bb.indexOf(t)>=0}).length;return Math.round(70*hit/Math.max(aa.length,bb.length,1))}
function searchLabel(inner,u){var label=visible(inner);if(label)return label;var im=String(inner||"").match(/\\b(?:alt|title)=["']([^"']+)["']/i);if(im&&im[1]){label=visible(im[1]);if(label)return label}try{var path=new URL(u).pathname,mark="/animes/",pos=path.indexOf(mark),slug=pos>=0?path.slice(pos+mark.length):path;while(slug.charAt(0)==="/")slug=slug.slice(1);while(slug.charAt(slug.length-1)==="/")slug=slug.slice(0,-1);slug=slug.replace(/[-_]+/g," ");return visible(decodeURIComponent(slug))}catch(_e){return""}}
function searchRows(html){var out=[],seen={},re=/<a[^>]+href=["']([^"']*\/animes\/[^"'#?]+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<80){var u=abs(m[1],c.base),label=searchLabel(m[2],u);if(!u||seen[u])continue;seen[u]=1;out.push({url:u,label:label})}return out}
async function findAnime(tt,q){for(var t=0;t<Math.min(tt.length,4);t++){var page=await text(c.base+"/?s="+encodeURIComponent(tt[t]),{referer:c.base+"/"});if(!page)continue;var rows=searchRows(page.text),best=null,bestScore=0;for(var i=0;i<rows.length;i++){var sc=score(rows[i].label||rows[i].url,tt[t]),low=(rows[i].label+" "+rows[i].url).toLowerCase();if(/\b(?:film|movie|ova|ona|special)\b/.test(low))sc-=35;var sm=low.match(/saison[- _]*(\d+)/);if(sm)sc+=Number(sm[1])===q.season?35:-45;if(sc>bestScore){bestScore=sc;best=rows[i]}}if(best&&bestScore>=45)return best}return null}
function episodeRows(html,base){var out=[],seen={},re=/<a[^>]+href=["']([^"']*(?:\/episode\/|episode-)[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<500){var u=abs(m[1],base),label=visible(m[2]);if(!u||seen[u])continue;seen[u]=1;out.push({url:u,label:label})}return out}
function episodeScore(row,q){var blob=(row.url+" "+row.label).toLowerCase(),score=0;var sm=blob.match(/(?:saison[- _]?|\/)(\d+)[-_ /]*episode[- _]?(\d+)/i);if(sm){if(Number(sm[1])===q.season&&Number(sm[2])===q.episode)score+=150;else if(Number(sm[2])===q.episode)score+=50;else return-100}var em=blob.match(/(?:episode|ep)[- _]?(\d+)/i);if(em)score+=Number(em[1])===q.episode?80:-50;if(new RegExp("(?:^|[^0-9])"+q.episode+"(?:[^0-9]|$)").test(row.label))score+=30;return score}
async function findEpisode(anime,q){var page=await text(anime.url,{referer:c.base+"/"});if(!page)return null;var rows=episodeRows(page.text,page.url),best=null,bestScore=-999;for(var i=0;i<rows.length;i++){var sc=episodeScore(rows[i],q);if(sc>bestScore){bestScore=sc;best=rows[i]}}if(best&&bestScore>=60)return best.url;var slug="";try{slug=new URL(anime.url).pathname.replace(/^.*\/animes\//,"").replace(/\/$/,"")}catch(_e){}if(slug){var guesses=[c.base+"/episode/"+slug+"-"+q.season+"-episode-"+q.episode+"/",c.base+"/episode/"+slug+"-episode-"+q.episode+"/"];for(var j=0;j<guesses.length;j++){var z=await text(guesses[j],{referer:page.url});if(z&&z.text.length>500)return z.url}}return null}
function playerRows(html,base){var out=[],seen={},re=/(?:src|data-src)=["']([^"']+)["']/gi,m;while((m=re.exec(html||""))!==null&&out.length<20){var u=abs(m[1],base);if(!u||seen[u])continue;if(u.indexOf("trembed")<0&&u.indexOf(c.base)<0)continue;seen[u]=1;out.push(u)}return out}
async function externalPlayer(url,ref){var p=await text(url,{referer:ref});if(!p)return"";var re=/(?:src|data-src|href)=["'](https?:\/\/[^"']+)["']/gi,m;while((m=re.exec(p.text))!==null){var u=s(m[1]);if(!u||u.indexOf("animevostfr")>=0)continue;return u}return""}
function langFrom(url){var x=s(url).toLowerCase();if(/(?:^|[-_/])vf(?:[-_/]|$)/.test(x))return"VF";if(/vostfr/.test(x))return"VOSTFR";if(/(?:^|[-_/])vo(?:[-_/]|$)/.test(x))return"VO";return"VOSTFR"}
async function resolve(a,_ctx){var q=req(a);if(!q)return[];var m=await metadata(q),tt=titles(m);if(!tt.length)return[];var anime=await findAnime(tt,q);if(!anime)return[];var episode=await findEpisode(anime,q);if(!episode)return[];var ep=await text(episode,{referer:anime.url});if(!ep)return[];var players=playerRows(ep.text,ep.url),out=[],seen={};for(var i=0;i<players.length&&out.length<c.maxStreams;i++){var ext=await externalPlayer(players[i],ep.url);if(!ext||seen[ext])continue;seen[ext]=1;var lang=langFrom(anime.url+" "+anime.label),rows=[];try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([ext],players[i],2)}catch(_e){rows=[]}if(!Array.isArray(rows)||!rows.length)continue;for(var j=0;j<rows.length&&out.length<c.maxStreams;j++){var st=Object.assign({},rows[j]);if(!st.url)continue;st.name="AnimeVOSTFR | "+lang;st.title=(st.title||"AnimeVOSTFR")+" | S"+q.season+"E"+q.episode+" | "+lang;st.language=lang;st.provider="animevostfr";st.headers=Object.assign({"Referer":c.base+"/"},st.headers||{});out.push(st)}}return out}
try{g.__niakvioProviderRuntimeResolverV1={provider:"animevostfr",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://animevostfr.org",
        "maxStreams": 6,
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 6), 12))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "animevostfr-search-episode-trembed-v1",
            "identity": "core-tmdb-anime-title-season-episode",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["anime"],
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
