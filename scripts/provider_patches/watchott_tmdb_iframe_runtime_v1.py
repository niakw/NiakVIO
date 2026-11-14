#!/usr/bin/env python3
"""WatchOTT TMDB-direct server-rendered iframe runtime oracle.

Observed on the residential Mac:
- movie: /play?id={tmdbId}&type=movie
- tv/anime transport: /play?id={tmdbId}&type=tv&season={season}&episode={episode}
- the HTML server-renders requested content identity and a player iframe.
The iframe is handed to ProviderBase's bounded terminal-media crawler.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WATCHOTT.TMDB_IFRAME.RUNTIME.V1"
MARKER = "NIAKVIO_WATCHOTT_TMDB_IFRAME_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_WATCHOTT_TMDB_IFRAME_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/&[^;]+;/g," ").replace(/[^a-z0-9]+/g," ").trim()}
function req(a){
  var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
  try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&o.semanticType)||ctx.semanticType||"").toLowerCase();
  var raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||semantic||"").toLowerCase();
  if(raw==="series")raw="tv";
  var anime=semantic==="anime"||raw==="anime";
  var type=raw==="movie"?"movie":"tv";
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId);
  if(!/^\d+$/.test(id))return[];
  var season=Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:ctx.season))||1;
  var episode=Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:ctx.episode))||1;
  return{type:type,semantic:anime?"anime":type,tmdbId:id,season:season,episode:episode}
}
function headers(ref){var h={"User-Agent":c.ua,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function text(url,ref){try{var r=await g.fetch(url,{headers:headers(ref)});if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
async function meta(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var ctx=g&&g.__nuvioMediaContext||{};return ctx.tmdbMetadata||null}catch(_e){return null}}
function expectedTitle(m){return s(m&&(m.title||m.name||m.original_title||m.original_name))}
function identityOk(html,q,title){
  var low=norm(html),want=norm(title);
  if(want&&low.indexOf(want)<0)return false;
  if(q.type==="tv"){
    var seasonRe=new RegExp("(?:season|saison)\\s*0*"+q.season+"(?:\\D|$)","i");
    var episodeRe=new RegExp("(?:episode|ep|e)\\s*0*"+q.episode+"(?:\\D|$)","i");
    if(!seasonRe.test(html)||!episodeRe.test(html))return false;
  }
  return true
}
function iframes(html,base){
  var out=[],seen={},re=/<iframe\b[^>]*\bsrc\s*=\s*["']([^"']+)["'][^>]*>/gi,m;
  while((m=re.exec(html||""))!==null&&out.length<8){
    var u=s(m[1]).replace(/&amp;/gi,"&");
    try{u=new URL(u,base).toString()}catch(_e){continue}
    if(!/^https?:/i.test(u)||seen[u])continue;
    seen[u]=1;out.push(u)
  }
  return out
}
async function resolve(a,_ctx){
  var q=req(a);if(!q||!q.tmdbId)return[];
  var m=await meta(q),title=expectedTitle(m);
  var url=c.base+"/play?id="+encodeURIComponent(q.tmdbId)+"&type="+encodeURIComponent(q.type);
  if(q.type==="tv")url+="&season="+encodeURIComponent(String(q.season))+"&episode="+encodeURIComponent(String(q.episode));
  var page=await text(url,c.base+"/");if(!page)return[];
  if(!identityOk(page.text,q,title))return[];
  var frames=iframes(page.text,page.url);if(!frames.length)return[];
  var direct=[];
  try{if(typeof _crawlDirectMedia==="function")direct=await _crawlDirectMedia(frames,page.url,Math.max(1,Number(c.maxDepth)||2))}catch(_e){direct=[]}
  if(!Array.isArray(direct)||!direct.length)return[];
  var out=[],seen={};
  for(var i=0;i<direct.length&&out.length<Math.max(1,Number(c.maxStreams)||6);i++){
    var st=direct[i];if(!st||!st.url||seen[st.url])continue;seen[st.url]=1;
    st=Object.assign({},st);
    st.provider="watchott";
    st.name=st.name||c.name;
    st.title=(st.title||title||c.name)+(q.type==="tv"?" | S"+q.season+"E"+q.episode:"");
    if(!st.headers)st.headers={"Referer":page.url};
    out.push(st)
  }
  return out
}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"watchott",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://watchott.org",
        "name": "WatchOTT",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        "maxDepth": 2,
        "maxStreams": 6,
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("WatchOTT base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "tmdb-direct-server-rendered-iframe-v1",
            "identity": "tmdb-route-plus-rendered-title-season-episode",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["movie", "tv", "anime"],
            "terminalTraversal": "providerbase-bounded-direct-media-crawler",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
