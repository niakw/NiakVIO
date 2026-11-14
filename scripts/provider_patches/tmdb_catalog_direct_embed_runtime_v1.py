#!/usr/bin/env python3
"""Reusable identity-safe TMDB catalogue -> direct embed provider runtime."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.GENERIC.TMDB_CATALOG_DIRECT_EMBED.RUNTIME.V1"
GENERIC_REUSABLE = True
MARKER = "NIAKVIO_TMDB_CATALOG_DIRECT_EMBED_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_TMDB_CATALOG_DIRECT_EMBED_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
 var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(semantic==="series")semantic="tv";if(semantic!=="movie"&&semantic!=="tv"&&semantic!=="anime")return null;
 var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;
 return{semantic:semantic,transport:semantic==="movie"?"movie":"tv",tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:q.transport,tmdbNamespace:q.transport});return projected(r)}}catch(_e){}return null}
function title(md){return s(md&&(md.title||md.name||md.original_title||md.original_name))}
function enc(v){return encodeURIComponent(s(v))}
function fill(t,q,md){return s(t).replace(/\{tmdbId\}|\{id\}/g,q.tmdbId).replace(/\{season\}/g,String(q.season)).replace(/\{episode\}/g,String(q.episode)).replace(/\{query\}/g,enc(title(md)))}
function headers(ref){var h={"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9,fr;q=0.7"};if(ref)h.Referer=ref;return h}
async function get(url,ref){try{var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});var t=await r.text();return{ok:!!r.ok,status:Number(r.status)||0,url:s(r.url)||url,text:t||""}}catch(_e){return{ok:false,status:0,url:url,text:""}}}
function cardIdentity(html,q){var id=q.tmdbId,type=q.transport==="movie"?"movie":"tv";
 var card=new RegExp("data-id\\s*=\\s*[\"']"+id+"[\"'][\\s\\S]{0,900}?data-type\\s*=\\s*[\"']"+type+"[\"']|data-type\\s*=\\s*[\"']"+type+"[\"'][\\s\\S]{0,900}?data-id\\s*=\\s*[\"']"+id+"[\"']","i");
 var href=new RegExp("href\\s*=\\s*[\"']/"+type+"/"+id+"(?:[/?#\"'])","i");
 return card.test(html||"")||href.test(html||"")}
function detailUrl(q){return c.siteBase+"/"+(q.transport==="movie"?"movie":"tv")+"/"+q.tmdbId}
function htmlDecode(v){return s(v).replace(/&amp;/gi,"&").replace(/&#0*39;|&apos;/gi,"'").replace(/&quot;/gi,'"').replace(/&lt;/gi,"<").replace(/&gt;/gi,">")}
function preloadUrl(html,q){var re=/\bdata-preload-src\s*=\s*["']([^"']+)["']/ig,m;while((m=re.exec(html||""))!==null){var raw=htmlDecode(m[1]);try{var u=new URL(raw,c.siteBase);if(u.hostname===new URL(c.embedBase).hostname&&u.pathname.indexOf("/"+q.tmdbId)>=0)return u}catch(_e){}}return null}
function queryHas(query,key){var parts=s(query).replace(/^\?/,"").split("&");for(var i=0;i<parts.length;i++){if(decodeURIComponent((parts[i].split("=")[0]||"").replace(/\+/g," "))===key)return true}return false}
function queryAdd(query,key,value){var q=s(query).replace(/^\?/,"");if(queryHas(q,key))return q;var pair=encodeURIComponent(key)+"="+encodeURIComponent(value);return q?q+"&"+pair:pair}
function embedUrl(q,html){var template=q.transport==="movie"?c.movieEmbedTemplate:c.tvEmbedTemplate;var path=fill(template,q,null);var base=c.embedBase.replace(/\/$/,"");var raw=/^https?:/i.test(path)?path:base+(path.charAt(0)==="/"?path:"/"+path);var split=raw.indexOf("?"),root=split>=0?raw.slice(0,split):raw,query=split>=0?raw.slice(split+1):"";
 var preload=preloadUrl(html,q);if(preload&&preload.search)query=s(preload.search).replace(/^\?/,"");
 if(c.parentOriginParam)query=queryAdd(query,c.parentOriginParam,c.siteBase);
 if(q.transport==="tv"&&c.tvAutoNextParam)query=queryAdd(query,c.tvAutoNextParam,"true");
 return root+(query?"?"+query:"")}
async function terminal(seed,referer,q){var rows=[];try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([seed],referer,c.maxDepth)}catch(_e){rows=[]}if(!Array.isArray(rows))return[];var out=[],seen={};for(var i=0;i<rows.length&&out.length<c.maxStreams;i++){var row=rows[i]||{},u=s(row.url);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;var x=Object.assign({},row);x.provider=c.provider;x.name=x.name||c.name;x.title=x.title||c.name;x.headers=Object.assign({"Referer":referer,"User-Agent":c.userAgent},x.headers||{});if(q.transport==="tv"){x.season=q.season;x.episode=q.episode}out.push(x)}return out}
async function resolve(args,_ctx){var q=req(args);if(q===null)return null;if(!q)return[];var md=await metadata(q),want=title(md);if(!want)return[];
 var search=fill(c.searchTemplate,q,md);if(!/^https?:/i.test(search))search=c.siteBase+(search.charAt(0)==="/"?search:"/"+search);
 var sr=await get(search,c.siteBase+"/");if(!sr.ok||!cardIdentity(sr.text,q))return[];
 var detail=detailUrl(q),dr=await get(detail,search);if(!dr.ok)return[];
 var idNeedle=new RegExp("(?:data-(?:id|hist-id)|/(?:movie|tv)/)\\s*[\"']?"+q.tmdbId+"(?:[\"'/?#&\\s]|$)","i");if(!idNeedle.test(dr.text)&&dr.url.indexOf("/"+q.transport+"/"+q.tmdbId)<0)return[];
 var embed=embedUrl(q,dr.text);return await terminal(embed,dr.url||detail,q)}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:c.provider,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply_owned(
    text: str,
    managed_fix_id: str,
    options: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> str:
    cfg = {
        "provider": "",
        "name": "",
        "siteBase": "",
        "searchTemplate": "/search?q={query}",
        "embedBase": "",
        "movieEmbedTemplate": "/embed/movie/{tmdbId}",
        "tvEmbedTemplate": "/embed/tv/{tmdbId}/{season}/{episode}",
        "parentOriginParam": "parent_origin",
        "tvAutoNextParam": "",
        "maxDepth": 2,
        "maxStreams": 8,
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        ),
    }
    cfg.update(dict(options or {}))
    required = ("provider", "name", "siteBase", "embedBase")
    missing = [key for key in required if not str(cfg.get(key) or "").strip()]
    if missing:
        raise ValueError("missing generic direct-embed options: " + ",".join(missing))
    cfg["siteBase"] = str(cfg["siteBase"]).rstrip("/")
    cfg["embedBase"] = str(cfg["embedBase"]).rstrip("/")
    js = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(cfg, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        str(managed_fix_id).strip().upper(),
        js.lstrip(),
        data={
            "runtimeFamily": "tmdb-catalog-direct-embed-v1",
            "identity": "catalogue-card-tmdb-id-before-embed",
            "runtimeResolverRegistration": True,
            "genericReusable": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    return apply_owned(text, MANAGED_FIX_ID, options=options, **kwargs)


if __name__ == "__main__":
    raise SystemExit("patch module only")
