#!/usr/bin/env python3
"""VoirAnime.rip provider-local runtime.

Clean-room reconstruction from exact provider HTTP proof:
- POST /template-php/defaut/fetch.php with form query={title}
- select an identity-compatible /{slug}/ result
- fetch /{slug}/saison-{season}/episode-{episode}/
- parse VF/VOSTFR iframe/script player URLs
- hand each provider-owned embed to ProviderBase's bounded terminal crawler

No provider domain or route is shared with any other provider.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VOIRANIME-RIP.RUNTIME.V1"
MARKER = "NIAKVIO_VOIRANIME_RIP_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VOIRANIME_RIP_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function S(v){return String(v==null?"":v).trim()}
function N(v){try{return S(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}catch(_e){return S(v).toLowerCase()}}
function A(v,b){try{return new URL(S(v),b||c.base).toString()}catch(_e){return""}}
function H(ref,accept){var h={"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7","User-Agent":c.userAgent};if(ref)h.Referer=ref;return h}
async function T(url,opt){try{var o=opt&&typeof opt==="object"?Object.assign({},opt):{};o.headers=Object.assign(H(o.referer||""),o.headers||{});delete o.referer;var r=await g.fetch(url,o);if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
function Q(args){var f=args[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}var semantic=S((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||args[1]||x.semanticType||x.canonicalMediaType||x.mediaType||"anime").toLowerCase();if(semantic==="series"||semantic==="tv")semantic="anime";if(semantic!=="anime")return null;var raw=S((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(raw))return{invalid:true};return{tmdbId:raw,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:x.episode))||1}}
async function M(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var x=g&&g.__nuvioMediaContext||{};return x.tmdbMetadata||null}catch(_e){return null}}
function aliases(m){var a=[m&&m.name,m&&m.title,m&&m.original_name,m&&m.original_title],alt=m&&m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)a.push(alt[i]&&(alt[i].title||alt[i].name));var out=[],seen={};for(var j=0;j<a.length;j++){var v=S(a[j]),k=N(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}}return out.slice(0,6)}
function visible(v){return S(v).replace(/<script\b[\s\S]*?<\/script\s*>/gi," ").replace(/<style\b[\s\S]*?<\/style\s*>/gi," ").replace(/<[^>]+>/g," ").replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\s+/g," ").trim()}
function results(html){var out=[],seen={},re=/<a[^>]*class=["'][^"']*va-search-result[^"']*["'][^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<30){var u=A(m[1],c.base),block=m[2],tm=/<[^>]*class=["'][^"']*va-search-result-title[^"']*["'][^>]*>([\s\S]*?)<\//i.exec(block),label=visible(tm?tm[1]:block);if(!u||seen[u])continue;var pm=new URL(u).pathname.match(/^\/([^/?#]+)\/?$/);if(!pm)continue;seen[u]=1;out.push({url:u,slug:pm[1],title:label})}return out}
function score(label,wanted){var a=N(label),b=N(wanted);if(!a||!b)return-999;if(a===b)return200;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return140;var bt=b.split(" ").filter(function(x){return x.length>2}),hit=0;for(var i=0;i<bt.length;i++)if(a.indexOf(bt[i])>=0)hit++;return hit*20-(bt.length-hit)*12}
async function search(names){for(var i=0;i<names.length;i++){var q=names[i],r=await T(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Accept":"text/html, */*","Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},referer:c.base+"/",body:"query="+encodeURIComponent(q)});if(!r)continue;var rows=results(r.text);rows.sort(function(a,b){return score(b.title,q)-score(a.title,q)});if(rows.length&&score(rows[0].title,q)>=40)return rows.slice(0,5)}return[]}
function players(html){var out=[],seen={};function add(u,lang){u=A(S(u).replace(/&amp;/gi,"&").replace(/\\\//g,"/"),c.base);if(!/^https?:/i.test(u)||seen[u])return;seen[u]=1;out.push({url:u,lang:lang||""})}var frame=/<(?:iframe|video)[^>]+(?:id=["']videoPlayer["'][^>]+)?src=["']([^"']+)["']/gi,m;while((m=frame.exec(html||""))!==null)add(m[1],"");var wrap=/<[^>]*class=["'][^"']*video-wrapper[^"']*["'][^>]*>[\s\S]{0,2500}?<iframe[^>]+src=["']([^"']+)["']/gi,w;while((w=wrap.exec(html||""))!==null)add(w[1],"");var scripts=(html||"").match(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi)||[];for(var i=0;i<scripts.length;i++){var re=/["']?(vostfr|vf)["']?\s*[:=]\s*["']?(https?:\/\/[^'"\s;,}]+)/gi,x;while((x=re.exec(scripts[i]))!==null)add(x[2],x[1].toUpperCase())}return out}
async function terminal(row,episodeUrl){var direct=[];try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia([row.url],episodeUrl,2)}catch(_e){direct=[]}if(!Array.isArray(direct)||!direct.length)return[];var out=[];for(var i=0;i<direct.length&&i<2;i++){var st=Object.assign({},direct[i]);st.provider="voiranime-rip";st.name="VoirAnime.rip"+(row.lang?" | "+row.lang:"");st.title=(st.title||"VoirAnime.rip")+(row.lang?" | "+row.lang:"");if(row.lang)st.language=row.lang==="VF"?"fr":"VOSTFR";if(!st.headers)st.headers={"Referer":episodeUrl};out.push(st)}return out}
async function resolve(args){var q=Q(args);if(q===null)return null;if(!q||q.invalid)return[];var md=await M(q),names=aliases(md);if(!names.length)return[];var matches=await search(names);for(var i=0;i<matches.length;i++){var ep=c.base+"/"+matches[i].slug+"/saison-"+q.season+"/episode-"+q.episode+"/",page=await T(ep,{referer:c.base+"/"});if(!page)continue;var ps=players(page.text),out=[],seen={};for(var j=0;j<ps.length&&out.length<c.maxStreams;j++){var rows=await terminal(ps[j],page.url);for(var k=0;k<rows.length&&out.length<c.maxStreams;k++){var key=S(rows[k].url);if(key&&!seen[key]){seen[key]=1;out.push(rows[k])}}}if(out.length)return out}return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"voiranime-rip",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://voiranime.rip",
        "maxStreams": 4,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 4), 8))
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("VoirAnime.rip runtime base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "voiranime-rip-search-episode-embed-v1",
            "runtimeResolverRegistration": True,
            "semanticLanes": ["anime"],
            "identity": "core-tmdb-title-to-provider-search-season-episode",
            "terminalResolution": "provider-embed-to-shared-bounded-crawler",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
