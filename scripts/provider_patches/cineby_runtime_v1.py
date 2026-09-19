#!/usr/bin/env python3
"""Cineby clean-v3 runtime Lego.

Primary path keeps the proven Wings/speedracelight family. When that family is
unavailable, Cineby itself is the address/identity authority: movie and TV pages
are addressed directly by TMDB id and current player URLs are discovered from
the page at request time. Signed/rotating downstream player URLs are never
persisted as provider DATA.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix
from provider_wings_runtime_common import render_wings_runtime

MANAGED_FIX_ID = "PROVIDER.CINEBY.WINGS.V1"
MARKER = "NIAKVIO_CINEBY_WINGS_V1"
FALLBACK_MARKER = "NIAKVIO_CINEBY_TMDB_PAGE_FALLBACK_V2"

PAGE_FALLBACK = r'''
/* NIAKVIO_CINEBY_TMDB_PAGE_FALLBACK_V2 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return ""}}
  function esc(v){return s(v).replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}
  function uniq(rows){var out=[],seen=Object.create(null);for(var i=0;i<rows.length;i++){var u=s(rows[i]);if(!u||seen[u])continue;seen[u]=1;out.push(u)}return out}
  function decode(v){return s(v).replace(/&amp;/gi,"&").replace(/&#0*38;/gi,"&").replace(/\\\//g,"/").replace(/\\u0026/gi,"&")}
  function direct(u){return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/(?:hls|dash|stream)(?:\/|[?#]|$)/i.test(s(u))}
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
    try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0];
    return {id:id,type:type==="movie"?"movie":"tv",season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1};
  }
  function headers(ref){return {"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Origin":c.siteBase,"Referer":ref||c.siteBase+"/"}}
  function ignore(u){return /(?:google-analytics|googletagmanager|doubleclick|facebook|twitter|discord|tmdb|themoviedb)|\.(?:js|css|png|jpe?g|gif|svg|webp|ico|woff2?)(?:[?#]|$)/i.test(u)}
  function rootIdentity(u,q){
    var x=s(u);if(!x||x.indexOf(q.id)<0)return false;if(q.type==="movie")return true;
    try{
      var p=new URL(x),path=decodeURIComponent(p.pathname||"");
      var triplet=new RegExp("/(?:tv|series|episode)?/?"+esc(q.id)+"/0*"+q.season+"/0*"+q.episode+"(?:/|$)","i");
      if(triplet.test(path))return true;
      var id=s(p.searchParams.get("id")||p.searchParams.get("tmdb")||p.searchParams.get("tmdbId"));
      var sn=Number(p.searchParams.get("season")||p.searchParams.get("s")||0);
      var ep=Number(p.searchParams.get("episode")||p.searchParams.get("e")||0);
      return id===q.id&&sn===q.season&&ep===q.episode;
    }catch(_e){return false}
  }
  function playerCandidates(html,base,q,requireIdentity){
    var out=[],source=s(html),m,re;
    function add(raw){var u=abs(decode(raw),base);if(!/^https?:\/\//i.test(u)||ignore(u))return;if(requireIdentity&&!rootIdentity(u,q))return;out.push(u)}
    re=/<(?:iframe|source|video)\b[^>]*\bsrc\s*=\s*["']([^"']+)["']/gi;while((m=re.exec(source))&&out.length<80)add(m[1]);
    re=/\b(?:src|url|file|embed|player)\s*[:=]\s*["'](https?:\\?\/\\?\/[^"']+)["']/gi;while((m=re.exec(source))&&out.length<120)add(m[1]);
    re=/(https?:\\?\/\\?\/[^\s"'<>]{8,900})/gi;while((m=re.exec(source))&&out.length<160)add(m[1]);
    return uniq(out);
  }
  function score(u,q){
    var x=s(u).toLowerCase(),n=0;if(x.indexOf(q.id)>=0)n+=100;if(direct(x))n+=80;
    if(q.type==="tv"){
      if(new RegExp("(?:/|=)"+q.season+"(?:/|&|$)").test(x))n+=20;
      if(new RegExp("(?:/|=)"+q.episode+"(?:/|&|$)").test(x))n+=20;
      if(/\/(?:tv|series|episode)\//.test(x))n+=10;
    } else if(/\/(?:movie|film|filme)\//.test(x)||/[?&]type=movie(?:&|$)/.test(x)) n+=10;
    return n;
  }
  async function crawl(url,ref,q,depth){
    try{
      var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||!r.ok)return [];
      var finalUrl=s(r.url||url);if(direct(finalUrl))return [{url:finalUrl,referer:ref||c.siteBase+"/"}];
      var body=await r.text(),all=playerCandidates(body,finalUrl,q,false),media=[];
      for(var i=0;i<all.length;i++)if(direct(all[i]))media.push({url:all[i],referer:finalUrl});
      if(media.length||depth<=0)return media.slice(0,8);
      var nested=all.filter(function(u){return !direct(u)}).sort(function(a,b){return score(b,q)-score(a,q)}).slice(0,4),out=[];
      for(var j=0;j<nested.length&&out.length<8;j++){
        var rows=await crawl(nested[j],finalUrl,q,depth-1);for(var k=0;k<rows.length;k++)out.push(rows[k]);
      }
      return out.slice(0,8);
    }catch(_e){return []}
  }
  async function fallback(args){
    var q=requestArgs(args);if(!/^\d+$/.test(q.id))return [];
    var page=c.siteBase+(q.type==="movie"?"/film/":"/series/")+encodeURIComponent(q.id);
    try{
      var r=await g.fetch(page,{headers:headers(c.siteBase+"/"),redirect:"follow"});if(!r||!r.ok)return [];
      var html=await r.text(),players=playerCandidates(html,r.url||page,q,true).sort(function(a,b){return score(b,q)-score(a,q)}).slice(0,10),resolved=[];
      for(var i=0;i<players.length&&resolved.length<8;i++){
        if(direct(players[i])){resolved.push({url:players[i],referer:r.url||page});continue}
        var rows=await crawl(players[i],r.url||page,q,2);for(var j=0;j<rows.length;j++)resolved.push(rows[j]);
        if(resolved.length>=3)break;
      }
      var out=[],seen=Object.create(null);for(var z=0;z<resolved.length;z++){
        var row=resolved[z]||{},u=s(row.url);if(!direct(u)||seen[u])continue;seen[u]=1;
        out.push({name:"Cineby [dynamic]",title:"Cineby",url:u,quality:"Auto",language:"",provider:"cineby",headers:{"Referer":s(row.referer||page),"Origin":c.siteBase,"User-Agent":c.userAgent}});
      }
      return out.slice(0,8);
    }catch(_e){return []}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioCinebyPageFallbackV2)return false;
    var prior=container[key];
    var wrapped=async function(){var rows=[];try{rows=await prior.apply(this,arguments)}catch(_e){rows=[]}if(Array.isArray(rows)&&rows.length)return rows;return await fallback(arguments)};
    wrapped.__niakvioCinebyPageFallbackV2=true;container[key]=wrapped;return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def render_cineby_page_fallback(*, site_base: str, user_agent: str) -> str:
    payload = {
        "siteBase": str(site_base).rstrip("/"),
        "userAgent": str(user_agent),
    }
    if not payload["siteBase"].startswith(("http://", "https://")):
        raise ValueError("Cineby siteBase must be http(s)")
    return PAGE_FALLBACK.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    user_agent = str(
        cfg.get("user_agent")
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    runtime = {
        "apiBase": str(cfg.get("api_base") or "https://api.speedracelight.com"),
        "origin": str(cfg.get("origin") or "https://www.cineby.at"),
        "referer": str(cfg.get("referer") or "https://www.cineby.at/"),
        "userAgent": user_agent,
        "providerId": "cineby",
        "providerName": "Cineby",
        "installMarker": "__niakvioCinebyWingsV1",
        "endpoints": list(cfg.get("endpoints") or [{"label": "CDN", "path": "cdn/sources-with-title"}]),
    }
    site_base = str(cfg.get("site_base") or "https://cineby.top").rstrip("/")
    body = render_wings_runtime(marker=MARKER, config=runtime) + "\n" + render_cineby_page_fallback(
        site_base=site_base,
        user_agent=user_agent,
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        body,
        data={
            "runtime": runtime,
            "siteBase": site_base,
            "family": "wings-v1+tmdb-page-fallback-v2",
            "identity": "core-tmdb-direct",
            "movieEntry": "/film/{tmdbId}",
            "tvEntry": "/series/{tmdbId}",
            "tvPlayerRootRequiresEpisodeIdentity": True,
            "dynamicPlayersPersisted": False,
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
