#!/usr/bin/env python3
"""NiakVIO-owned AllWish search -> watch -> terminal runtime.

Evidence authority:
- user browser capture: /filter?keyword=death+note -> /watch/death-note-.../ep-37
  -> fetch.nexabloom.top HLS
- current upstream still uses the same /filter?keyword= provider search family.

The runtime does not execute upstream JavaScript. Core owns TMDB identity, terminal
media validation, cancellation/timeouts and final stream normalization.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLWISH.RUNTIME.V1"
MARKER = "NIAKVIO_ALLWISH_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ALLWISH_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function S(v){return String(v==null?"":v).trim()}
function N(v){var x=S(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[’'`]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function A(v,b){try{return new URL(S(v),b||c.base).toString()}catch(_e){return""}}
function H(ref){var h={"User-Agent":c.ua,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function T(url,ref){try{var r=await g.fetch(url,{headers:H(ref),redirect:"follow"});if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
function Q(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var t=S((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.mediaType||"tv").toLowerCase();if(t==="series")t="tv";if(t!=="movie"&&t!=="tv")return null;
  var id=S((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return{invalid:true};
  return{type:t,tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1}
}
async function M(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type}),m=z&&z.metadata||z;if(m&&typeof m==="object")return m}}catch(_e){}try{var x=g&&g.__nuvioMediaContext||{},m2=x.tmdbMetadata||x.fixtureMetadata||x.metadata;if(m2&&typeof m2==="object")return m2}catch(_e2){}return null}
function aliases(m,q){var vals=[q.type==="tv"?(m&&m.name):(m&&m.title),m&&m.original_name,m&&m.original_title,m&&m.name,m&&m.title],alt=m&&m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)vals.push(alt[i]&&(alt[i].title||alt[i].name));var out=[],seen={};for(var j=0;j<vals.length;j++){var v=S(vals[j]),k=N(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}}return out.slice(0,6)}
function seasonCounts(m){var out={};if(Array.isArray(m&&m.seasons))for(var i=0;i<m.seasons.length;i++){var r=m.seasons[i]||{},sn=Number(r.season_number),ec=Number(r.episode_count);if(sn>0&&ec>0)out[sn]=ec}return out}
function absEpisode(q,m){var n=q.episode,counts=seasonCounts(m);for(var sn=1;sn<q.season;sn++){var ec=Number(counts[sn]);if(!ec)return q.episode;n+=ec}return n}
function visible(v){var src=String(v==null?"":v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return S(out).replace(/&(?:nbsp|amp|quot|#0*39|apos);/gi," ").replace(/\s+/g," ").trim()}
function attr(tag,key){var m=String(tag||"").match(new RegExp("\\b"+key+"\\s*=\\s*([\\\"'])([\\s\\S]*?)\\1","i"));return m?m[2].replace(/&amp;/gi,"&"):""}
function score(label,want,year,season){var a=N(label),b=N(want);if(!a||!b)return-999;var sc=a===b?200:(a.indexOf(b)>=0||b.indexOf(a)>=0?135:0);if(!sc){var words=b.split(" ").filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<words.length;i++)if(a.indexOf(words[i])>=0)hit++;sc=hit*24-(words.length-hit)*10}if(year){var ym=String(label||"").match(/\b(19|20)\d{2}\b/);if(ym)sc+=Number(ym[0])===Number(year)?25:-25}if(Number(season)>1){var sm=String(label||"").match(/(?:season|part|saison|\bs)\s*(\d+)/i);if(sm)sc+=Number(sm[1])===Number(season)?35:-45}return sc}
function searchRows(html,b){var out=[],seen={},re=/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<80){var u=A(attr(m[1],"href"),b);if(!u||u.indexOf("/watch/")<0)continue;var label=visible(m[2]);if(!label)label=visible(m[0]);if(!label||seen[u])continue;seen[u]=1;out.push({url:u,label:label})}return out}
async function find(names,q,m){var date=S(q.type==="tv"?(m&&m.first_air_date):(m&&m.release_date)),year=date.slice(0,4),queries=[];for(var i=0;i<names.length&&queries.length<8;i++){queries.push(names[i]);if(q.type==="tv"&&q.season>1)queries.push(names[i]+" Season "+q.season)}var seen={};for(var qi=0;qi<queries.length;qi++){var query=S(queries[qi]),key=N(query);if(!query||seen[key])continue;seen[key]=1;var page=await T(c.base+"/filter?keyword="+encodeURIComponent(query),c.base+"/");if(!page)continue;var rows=searchRows(page.text,page.url),best=null,bestScore=-999;for(var ri=0;ri<rows.length;ri++){for(var ni=0;ni<names.length;ni++){var sc=score(rows[ri].label,names[ni],year,q.season);if(sc>bestScore){bestScore=sc;best=rows[ri]}}}if(best&&bestScore>=40)return best}return null}
function watchBase(u){return S(u).replace(/\/ep-\d+\/?(?:[?#].*)?$/i,"").replace(/\/$/,"")}
async function crawl(url,q,m){var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([url],url,c.depth)}catch(_e){direct=[]}if(!Array.isArray(direct)||!direct.length)return[];var title=S(q.type==="tv"?(m&&m.name):(m&&m.title))||"AllWish",out=[],seen={};for(var i=0;i<direct.length&&out.length<c.maxStreams;i++){var row=direct[i]||{},u=S(row.url);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;var x=Object.assign({},row);x.provider="allwish";x.name="AllWish";x.title=title+(q.type==="tv"?" | S"+q.season+"E"+q.episode:"");if(!x.headers)x.headers={"Referer":url,"User-Agent":c.ua};out.push(x)}return out}
async function resolve(a){var q=Q(a);if(q===null)return null;if(!q||q.invalid)return[];var m=await M(q),names=aliases(m,q);if(!m||!names.length)return[];var found=await find(names,q,m);if(!found)return[];var base=watchBase(found.url),eps=[q.episode],abs=absEpisode(q,m);if(abs!==q.episode)eps.push(abs);if(q.type==="movie")eps=[1];for(var i=0;i<eps.length;i++){var watch=base+"/ep-"+eps[i],rows=await crawl(watch,q,m);if(rows.length)return rows}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"allwish",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://all-wish.me",
        "depth": 3,
        "maxStreams": 6,
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["depth"] = max(1, min(int(cfg.get("depth") or 3), 4))
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 6), 10))
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("AllWish runtime base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "allwish-filter-watch-terminal-crawl-v1",
            "runtimeResolverRegistration": True,
            "semanticLanes": ["movie", "tv"],
            "identity": "core-tmdb-title-year-season-episode",
            "terminalResolution": "provider-watch-to-shared-bounded-crawler",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
