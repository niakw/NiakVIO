#!/usr/bin/env python3
"""Cinegram provider-local runtime learned from residential reverse engineering.

Representative movie chain:
TMDB/Core metadata -> current Cinegram GET search -> exact title/year movie row
-> detail page -> inline cinemov AJAX token -> player HTML -> terminal media crawl.

TV/anime intentionally fall through until their episode/player chain is proven.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.CINEGRAM.RUNTIME.V1"
MARKER = "NIAKVIO_CINEGRAM_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_CINEGRAM_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function seasonCoord(v){if(v==null||s(v)==="")return 1;var n=Number(v);return Number.isInteger(n)&&n>=0?n:1}
function episodeCoord(v){if(v==null||s(v)==="")return 1;var n=Number(v);return Number.isInteger(n)&&n>=1?n:1}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/&amp;/g," and ").replace(/[^a-z0-9]+/g," ").trim()}
function htmlDecode(v){return s(v).replace(/&amp;/gi,"&").replace(/&#0*39;|&apos;/gi,"'").replace(/&quot;/gi,'"').replace(/&lt;/gi,"<").replace(/&gt;/gi,">")}
function req(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
 var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(semantic==="series")semantic="tv";if(semantic!=="movie"&&semantic!=="tv"&&semantic!=="anime")return null;
 var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
 return{semantic:semantic,transport:semantic==="movie"?"movie":"tv",tmdbId:id,season:seasonCoord((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season)),episode:episodeCoord((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode)),metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:q.transport,tmdbNamespace:q.transport});return projected(r)}}catch(_e){}return null}
function title(md){return s(md&&(md.title||md.name||md.original_title||md.original_name))}
function year(md){var d=s(md&&(md.release_date||md.first_air_date));return /^\d{4}/.test(d)?Number(d.slice(0,4)):0}
function headers(ref,ajax){var h={"User-Agent":c.userAgent,"Accept":ajax?"text/html,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9,fr;q=0.7"};if(ref)h.Referer=ref;if(ajax)h["X-Requested-With"]="XMLHttpRequest";return h}
async function get(url,ref,ajax){try{var r=await g.fetch(url,{headers:headers(ref,ajax),redirect:"follow"});var t=await r.text();return{ok:!!r.ok,status:Number(r.status)||0,url:s(r.url)||url,text:t||""}}catch(_e){return{ok:false,status:0,url:url,text:""}}}
function searchRows(html){var out=[],re=/<a\b[^>]*class=["'][^"']*hthis[^"']*["'][^>]*href=["']([^"']+)["'][^>]*title=["']([^"']+)["'][^>]*>[\s\S]{0,2600}?<p[^>]*>\s*(\d{4})\s*<\/p>/gi,m;while((m=re.exec(html||""))!==null&&out.length<30){var href=htmlDecode(m[1]),label=htmlDecode(m[2]).replace(/\s+online\s+free\s*$/i,""),y=Number(m[3])||0;if(href.indexOf("/movie/")<0)continue;out.push({href:href,title:label,year:y})}return out}
function score(row,want,wantYear){var a=norm(row.title),b=norm(want),n=0;if(!a||!b)return-1;if(a===b)n=120;else if(a.indexOf(b)>=0||b.indexOf(a)>=0)n=75;else return-1;if(wantYear&&row.year){if(wantYear===row.year)n+=30;else n-=55}return n}
function pick(rows,want,wantYear){var best=null,bestScore=-1;for(var i=0;i<rows.length;i++){var n=score(rows[i],want,wantYear);if(n>bestScore){best=rows[i];bestScore=n}}return bestScore>=90?best:null}
function abs(u,base){try{return new URL(htmlDecode(u),base).toString()}catch(_e){return""}}
function ajaxSpec(html){var re=/\$\.get\(\s*["']([^"']*\/ajax\/cinemov\.php)["']\s*,\s*\{\s*["']?t["']?\s*:\s*["'](\d+)["']/i,m=re.exec(html||"");return m?{path:m[1],token:m[2]}:null}
function playerSeeds(html,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u)}
 var re=/<(?:iframe|source|video)[^>]+src=["']([^"']+)["']/gi,m;while((m=re.exec(html||""))!==null&&out.length<12)add(m[1]);
 var js=/(?:file|src|url)\s*[:=]\s*["'](https?:\/\/[^"'\s]+)["']/gi,x;while((x=js.exec(html||""))!==null&&out.length<12)add(x[1]);
 return out}
async function terminal(seeds,ref,q){var out=[],seen={};for(var i=0;i<seeds.length&&i<8&&out.length<c.maxStreams;i++){var rows=[];try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([seeds[i]],ref,2)}catch(_e){rows=[]}if(!Array.isArray(rows))continue;for(var j=0;j<rows.length&&out.length<c.maxStreams;j++){var x=rows[j]||{},u=s(x.url);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;var r=Object.assign({},x);r.provider="cinegram";r.name=r.name||"Cinegram";r.title=r.title||"Cinegram";r.headers=Object.assign({"Referer":ref,"User-Agent":c.userAgent},r.headers||{});if(q.transport==="tv"){r.season=q.season;r.episode=q.episode}out.push(r)}}return out}
async function movie(q,md){var want=title(md);if(!want)return[];var search=c.base+"/index.php?menu=search&query="+encodeURIComponent(want),sr=await get(search,c.base+"/",false);if(!sr.ok)return[];var hit=pick(searchRows(sr.text),want,year(md));if(!hit)return[];var detailUrl=abs(hit.href,c.base+"/");if(!detailUrl)return[];var detail=await get(detailUrl,search,false);if(!detail.ok||norm(detail.text.slice(0,18000)).indexOf(norm(want))<0)return[];var spec=ajaxSpec(detail.text);if(!spec)return[];var ajaxUrl=abs(spec.path,c.base+"/")+"?t="+encodeURIComponent(spec.token),player=await get(ajaxUrl,detail.url,true);if(!player.ok||!player.text||/^\s*(?:404|not found)\s*$/i.test(player.text))return[];var seeds=playerSeeds(player.text,player.url||ajaxUrl);if(!seeds.length)return[];return await terminal(seeds,detail.url,q)}
async function resolve(args,_ctx){var q=req(args);if(q===null)return null;if(!q||!q.tmdbId)return[];if(q.transport!=="movie")return null;var md=await metadata(q);if(!md)return[];return await movie(q,md)}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"cinegram",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://cinegram.tv",
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        ),
        "maxStreams": 8,
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    js = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(cfg, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "catalogue-html-tmdb-ajax-player-v1",
            "identity": "core-tmdb-title-year-search-detail",
            "semanticLanes": ["movie"],
            "runtimeResolverRegistration": True,
            "manualOracle": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
