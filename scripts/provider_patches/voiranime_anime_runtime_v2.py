#!/usr/bin/env python3
"""VoirAnime current-site anime runtime layered over the existing movie Lego.

The existing VoirAnime Lego owns movie extraction. This V2 captures that resolver
at runtime, handles only semantic anime through the observable current-site
contract, and delegates every other lane to the previous resolver. Core remains
the final getStreams dispatcher and owns runtime compatibility, cancellation,
identity and terminal-media fail-closed policy.

Clean-room anime chain:
  TMDB/Core title -> /anime/{slug}/ or WordPress search -> requested chapter ->
  LECTEUR selector pages (?host=...) -> external iframes -> shared bounded direct
  media crawler already present in ProviderBase.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VOIRANIME.ANIME.RUNTIME.V2"
MARKER = "NIAKVIO_VOIRANIME_ANIME_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_VOIRANIME_ANIME_RUNTIME_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
var previous=null;try{previous=g&&g.__niakvioProviderRuntimeResolverV1||null}catch(_e){}
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[’'`]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-").replace(/^-+|-+$/g,"")}
function stripTags(v){var src=String(v==null?"":v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return out.replace(/&(?:nbsp|amp|quot|#039);/gi," ").replace(/\s+/g," ").trim()}
function absolute(v,base){try{return new URL(s(v).replace(/&amp;/g,"&"),base).toString()}catch(_e){return""}}
function req(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();if(raw==="series")raw="tv";if(raw!=="anime")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return[];var md=(o&&(o.tmdbMetadata||o.metadata))||ctx.tmdbMetadata||ctx.fixtureMetadata||{};var title=s((o&&(o.title||o.name))||md.name||md.title||md.original_name||md.original_title||ctx.title);var year=Number(s(md.first_air_date||md.release_date||(o&&o.year)||ctx.year).slice(0,4))||0;return{tmdbId:id,title:title,year:year,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
async function metadata(q){if(q.title)return q;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"}),m=z&&z.metadata,t=s(m&&(m.name||m.title||m.original_name||m.original_title));if(t){q.title=t;q.year=q.year||Number(s(m.first_air_date||m.release_date).slice(0,4))||0;return q}}}catch(_e){}try{var ctx=g&&g.__nuvioMediaContext||{},m2=ctx.tmdbMetadata||ctx.fixtureMetadata||{},t2=s(m2.name||m2.title||m2.original_name||m2.original_title||ctx.title);if(t2){q.title=t2;q.year=q.year||Number(s(m2.first_air_date||m2.release_date).slice(0,4))||0}}catch(_e2){}return q}
function headers(ref,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function get(url,ref){try{var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||!r.ok)return null;return{text:await r.text(),url:r.url||url}}catch(_e){return null}}
function titleMatch(html,title){var m=/<title[^>]*>([\s\S]*?)<\/title>/i.exec(html||""),a=norm(stripTags(m&&m[1]||"")),b=norm(title);if(!a||!b)return false;if(a===b||a.indexOf(b)>=0||b.indexOf(a)>=0)return true;var toks=b.split(" ").filter(function(x){return x.length>=3}),hits=0;for(var i=0;i<toks.length;i++)if(a.indexOf(toks[i])>=0)hits++;return toks.length>0&&hits>=Math.max(1,Math.ceil(toks.length*0.6))}
function searchCandidates(html,base,q){var out=[],seen={},re=/<a\b[^>]*href=["']([^"']*\/anime\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m,target=norm(q.title);while((m=re.exec(html||""))!==null&&out.length<60){var u=absolute(m[1],base),label=stripTags(m[2]),n=norm(label),score=0;if(!u||u.indexOf(c.base+"/anime/")!==0)continue;if(n===target)score+=220;else if(n.indexOf(target)>=0||target.indexOf(n)>=0)score+=130;var toks=target.split(" ").filter(function(x){return x.length>=3});for(var i=0;i<toks.length;i++)if(n.indexOf(toks[i])>=0)score+=12;if(q.year&&n.indexOf(String(q.year))>=0)score+=20;if(score>=60&&!seen[u]){seen[u]=1;out.push({url:u,score:score})}}out.sort(function(a,b){return b.score-a.score});return out.slice(0,5)}
async function seriesPage(q){var bases=[slug(q.title)],direct=[];if(q.season>1){direct.push(c.base+"/anime/"+bases[0]+"-"+q.season+"/");direct.push(c.base+"/anime/"+bases[0]+"-saison-"+q.season+"/")}direct.push(c.base+"/anime/"+bases[0]+"/");direct.push(c.base+"/anime/"+bases[0]+"-vf/");for(var i=0;i<direct.length;i++){var p=await get(direct[i],c.base+"/");if(p&&titleMatch(p.text,q.title))return p}var search=await get(c.base+"/?s="+encodeURIComponent(q.title),c.base+"/");if(!search)return null;var rows=searchCandidates(search.text,search.url||c.base+"/",q);for(var j=0;j<rows.length;j++){var p2=await get(rows[j].url,search.url);if(p2&&titleMatch(p2.text,q.title))return p2}return null}
function episodeScore(href,label,q){var h=href.toLowerCase(),l=norm(label),e=Number(q.episode),score=0;var nums=[];var re=/(?:episode|ep|chapitre|chapter|e)[-_\s]*0*(\d{1,4})(?:\D|$)/gi,m;while((m=re.exec(h+" "+l))!==null)nums.push(Number(m[1]));var tail=h.match(/(?:-|\/|_)0*(\d{1,4})(?:-(?:vf|vostfr))?\/?(?:[?#].*)?$/i);if(tail)nums.push(Number(tail[1]));if(nums.indexOf(e)>=0)score+=250;if(l===String(e)||l==="episode "+e||l==="ep "+e)score+=200;if(q.season>1&&new RegExp("(?:saison|season|s)[-_ ]*0*"+q.season+"(?:\\D|$)","i").test(h+" "+l))score+=40;if(/\/anime\//.test(h))score+=10;return score}
function episodeUrl(html,base,q){var rows=[],seen={},re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&rows.length<500){var u=absolute(m[1],base);if(!u||u.indexOf(c.base+"/anime/")!==0||seen[u])continue;seen[u]=1;var label=stripTags(m[2]),score=episodeScore(u,label,q);if(score>0)rows.push({url:u,score:score})}rows.sort(function(a,b){return b.score-a.score});if(rows.length&&rows[0].score>=200)return rows[0].url;if(q.episode===1&&rows.length)return rows[0].url;return""}
function hostLabels(html){var out=[],seen={},re=/<option[^>]+value=["']([^"']+)["'][^>]*>/gi,m;while((m=re.exec(html||""))!==null&&out.length<16){var v=s(m[1]);if(/^LECTEUR\s+/i.test(v)&&!seen[v]){seen[v]=1;out.push(v)}}return out}
function iframeUrls(html,base){var out=[],seen={},re=/<iframe[^>]+src=["']([^"']+)["']/gi,m;while((m=re.exec(html||""))!==null&&out.length<20){var u=absolute(m[1],base),low=u.toLowerCase();if(!/^https?:/i.test(u)||seen[u])continue;if(/youtube\.com\/embed|youtu\.be\/|facebook\.com\/plugins|twitter\.com\/i\/videos|ok\.ru\/videoembed/.test(low))continue;seen[u]=1;out.push(u)}return out}
async function resolveAnime(q){q=await metadata(q);if(!q.title)return null;var series=await seriesPage(q);if(!series)return null;var ep=episodeUrl(series.text,series.url,q);if(!ep)return null;var page=await get(ep,series.url);if(!page)return null;var players=iframeUrls(page.text,page.url),labels=hostLabels(page.text);for(var i=0;i<labels.length&&players.length<12;i++){var hp=await get(page.url+(page.url.indexOf("?")>=0?"&":"?")+"host="+encodeURIComponent(labels[i]),page.url);if(!hp)continue;var found=iframeUrls(hp.text,hp.url);for(var j=0;j<found.length;j++)if(players.indexOf(found[j])<0)players.push(found[j])}if(!players.length||typeof _crawlDirectMedia!=="function")return null;var rows=[];try{rows=await _crawlDirectMedia(players,page.url,2)}catch(_e){rows=[]}if(!Array.isArray(rows)||!rows.length)return null;var out=[],seen={};for(var k=0;k<rows.length&&out.length<c.maxStreams;k++){var x=rows[k];if(!x||!x.url||seen[x.url])continue;seen[x.url]=1;x.name=x.name||"VoirAnime";x.title=(x.title||q.title)+" | VOSTFR";x.language=x.language||"VOSTFR";x.provider="voiranime";out.push(x)}return out.length?out:null}
async function resolve(args,ctx){var q=req(args);if(q===null){if(previous&&typeof previous.resolve==="function")return await previous.resolve(args,ctx);return null}if(!q||!q.tmdbId)return[];var own=await resolveAnime(q);if(own!==null&&own!==undefined)return own;if(previous&&typeof previous.resolve==="function")return await previous.resolve(args,ctx);return null}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"voiranime",resolve:resolve,previous:previous&&previous.provider||null}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://voir-anime.to").rstrip("/"),
        "maxStreams": max(1, min(6, int(cfg.get("maxStreams") or 4))),
        "userAgent": str(cfg.get("userAgent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
    }
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "voiranime-current-site-anime-v2",
            "scope": "anime-plus-delegate-previous",
            "identity": "core-tmdb-title-season-episode",
            "catalogue": "direct-slug-plus-wordpress-search",
            "episode": "chapter-link-selection",
            "players": "lecteur-selector-to-shared-direct-media-crawler",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "semanticLanes": ["anime"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
