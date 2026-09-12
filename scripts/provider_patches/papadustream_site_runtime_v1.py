#!/usr/bin/env python3
"""PapaDuStream current-site movie runtime Lego.

Uses the observable current contract:
  /search/{title}/ -> /movie/{slug} -> Livewire snapshot video links.
ProviderBase remains immutable; TV/anime continue through the native runtime.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.PAPADUSTREAM.SITE.RUNTIME.V1"
MARKER = "NIAKVIO_PAPADUSTREAM_SITE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_PAPADUSTREAM_SITE_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function visible(v){var x=s(v),o="",tag=false;for(var i=0;i<x.length;i++){var ch=x.charAt(i);if(ch==="<"){tag=true;o+=" ";continue}if(tag){if(ch===">")tag=false;continue}o+=ch}return o.replace(/&nbsp;/gi," ").replace(/&amp;/gi,"&").replace(/\s+/g," ").trim()}
function request(a){var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||a[1]||ctx.semanticType||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();if(raw==="series")raw="tv";if(raw!=="movie")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return[];return{type:"movie",tmdbId:id}}
async function getText(url,opt){try{var o=opt&&typeof opt==="object"?Object.assign({},opt):{};o.headers=Object.assign({"User-Agent":c.ua,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"},o.headers||{});var r=await g.fetch(url,o);if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
async function meta(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"movie",tmdbNamespace:"movie"}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var ctx=g&&g.__nuvioMediaContext||{};return ctx.tmdbMetadata||null}catch(_e){return null}}
function title(m){return s(m&&(m.title||m.name||m.original_title||m.original_name))}
function decode(v){return s(v).replace(/&quot;/gi,'"').replace(/&amp;/gi,'&').replace(/&#x2F;/gi,'/').replace(/\\\//g,'/').replace(/\\u002[fF]/g,'/').replace(/\\u003[aA]/g,':')}
function movieLinks(html,expected){var out=[],re=/<a[^>]+href=["']([^"']*\/movie\/[^"'#?]+)["'][^>]*>([\s\S]*?)<\/a>/gi,m,n=norm(expected);while((m=re.exec(html))!==null){var u=decode(m[1]),label=norm(visible(m[2]));if(n&&label&&label!==n&&label.indexOf(n)<0&&n.indexOf(label)<0)continue;try{u=new URL(u,c.base).toString()}catch(_e){continue}if(u.indexOf(c.base+"/movie/")===0&&!out.includes(u))out.push(u)}return out}
function players(html){var full=decode(html),out=[],seen={};function add(u){u=decode(u);if(!/^https?:\/\//i.test(u)||seen[u])return;if(/(?:youtube\.com|youtu\.be|image\.tmdb|cloudflareinsights|zencdn|jsdelivr|focusameneducation|aqle3)/i.test(u))return;seen[u]=1;out.push(u)}var patterns=[/&quot;link&quot;:&quot;([^&<]+?)&quot;/gi,/\"link\"\s*:\s*\"([^\"]+)\"/gi,/link\s*[:=]\s*["']([^"']+)["']/gi];for(var p=0;p<patterns.length;p++){var re=patterns[p],m;while((m=re.exec(html))!==null)add(m[1])}var raw=/https?:\/\/[^\s"'<>\\]+/gi,x;while((x=raw.exec(full))!==null){if(/(?:vidzy|doply|sandratableother|uqload|multiup|filemoon)/i.test(x[0]))add(x[0])}return out}
function rank(u){u=u.toLowerCase();if(u.indexOf('filemoon')>=0)return 0;if(u.indexOf('vidzy')>=0)return 1;if(u.indexOf('uqload')>=0)return 2;if(u.indexOf('doply')>=0)return 3;if(u.indexOf('sandratableother')>=0)return 4;return 9}
async function crawl(ps,ref){ps=ps.slice().sort(function(a,b){return rank(a)-rank(b)});var out=[],seen={};for(var i=0;i<ps.length&&i<6&&out.length<4;i++){try{if(typeof _crawlDirectMedia!=="function")break;var rows=await _crawlDirectMedia([ps[i]],ref,2);if(!Array.isArray(rows))continue;for(var j=0;j<rows.length;j++){var x=rows[j];if(!x||!x.url||seen[x.url])continue;seen[x.url]=1;x.name=x.name||"PapaDuStream";x.title=x.title||"PapaDuStream VF";x.language=x.language||"VF";x.provider=x.provider||"papadustream";out.push(x)}}catch(_e){}}return out}
async function resolve(a,_ctx){var q=request(a);if(q===null)return null;if(!q||!q.tmdbId)return[];var m=await meta(q),t=title(m);if(!t)return[];var search=await getText(c.base+"/search/"+encodeURIComponent(t)+"/",{headers:{Referer:c.base+"/"}});if(!search)return[];var links=movieLinks(search.text,t);if(!links.length){var slug=norm(t).replace(/\s+/g,'-');if(slug)links=[c.base+"/movie/"+encodeURIComponent(slug)]}for(var i=0;i<links.length&&i<3;i++){var d=await getText(links[i],{headers:{Referer:search.url}});if(!d)continue;var bodyNorm=norm(d.text.slice(0,20000));if(bodyNorm&&bodyNorm.indexOf(norm(t))<0)continue;var rows=await crawl(players(d.text),d.url);if(rows.length)return rows}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"papadustream",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://papadustream-v2.watch",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("PapaDuStream site runtime base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "papadustream-livewire-site-v1",
            "identity": "core-tmdb-title-to-current-search-and-movie-detail",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie"],
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
