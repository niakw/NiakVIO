#!/usr/bin/env python3
"""VoirAnime movie-only current-site runtime Lego.

The canonical provider already has a working anime path in its native runtime.
This Lego therefore registers only a movie resolver with Core dispatch and
returns ``null`` for every non-movie request so the native anime path is kept.
Movie evidence is clean-room: TMDB title -> canonical voir-anime.to root -> exact
FILM chapter -> chapter player map -> existing bounded direct-media crawler.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VOIRANIME.HOMES.RUNTIME.V1"
MARKER = "NIAKVIO_VOIRANIME_HOMES_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VOIRANIME_HOMES_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function slug(v){return s(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
  function request(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var canonical=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||args[1]||ctx.canonicalMediaType||ctx.semanticType||ctx.mediaType||"").toLowerCase();
    if(canonical==="series")canonical="tv";
    if(canonical!=="movie")return null;
    var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
    if(!/^\d+$/.test(id))return [];
    var meta=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||{};
    var title=s((obj&&(obj.title||obj.name))||meta.title||meta.name||meta.original_title||meta.original_name||ctx.title||"");
    return {type:"movie",tmdbId:id,title:title};
  }
  async function metadata(q){
    if(q.title)return q;
    try{
      var fn=g&&g.__nuvioCoreGetTmdbDataV1;
      if(typeof fn==="function"){
        var z=await fn({tmdbId:q.tmdbId,mediaType:"movie",tmdbNamespace:"movie"}),m=z&&z.metadata;
        var t=s(m&&(m.title||m.name||m.original_title||m.original_name));if(t){q.title=t;return q}
      }
    }catch(_e){}
    try{var ctx=g&&g.__nuvioMediaContext||{},m2=ctx.tmdbMetadata||{},t2=s(m2.title||m2.name||m2.original_title||m2.original_name||ctx.title);if(t2)q.title=t2}catch(_e2){}
    return q;
  }
  function headers(referer,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(referer)h.Referer=referer;return h}
  async function text(url,init){try{var r=await g.fetch(url,Object.assign({redirect:"follow"},init||{}));if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url}}catch(_e){return null}}
  function absolute(u,base){try{return new URL(s(u).replace(/&amp;/gi,"&").replace(/\\\//g,"/"),base).toString()}catch(_e){return""}}
  function cleanLabel(raw){var x=s(raw),o="",tag=false;for(var i=0;i<x.length;i++){var ch=x.charAt(i);if(ch==="<"){tag=true;o+=" ";continue}if(tag){if(ch===">")tag=false;continue}o+=ch}return o.replace(/&(?:nbsp|amp);/gi," ").replace(/\s+/g," ").trim()}
  function movieChapter(rootHtml,rootUrl,q){
    var target=slug(q.title),best="",bestScore=-1,m,re=/<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
    while((m=re.exec(rootHtml||""))!==null){
      var label=cleanLabel(m[2]),ls=slug(label),u=absolute(m[1],rootUrl),score=0;
      if(!u||u.indexOf(c.movieSite+"/anime/")!==0)continue;
      if(/\bfilm\b/i.test(label))score+=70;
      if(ls===target||ls.indexOf(target)>=0||target.indexOf(ls)>=0)score+=90;
      var toks=target.split("-").filter(function(x){return x.length>=2});for(var i=0;i<toks.length;i++)if(ls.indexOf(toks[i])>=0)score+=8;
      if(score>bestScore){best=u;bestScore=score}
    }
    return bestScore>=110?best:"";
  }
  function chapterPlayers(html,base){
    var out=[],seen=Object.create(null),m;
    function add(v){var u=absolute(v,base);if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u)}
    var frame=/<iframe[^>]+src=["']([^"']+)["']/gi;while((m=frame.exec(html||""))!==null)add(m[1]);
    var block=/thisChapterSources\s*=\s*\{([\s\S]*?)\}\s*;/i.exec(html||"");
    if(block){
      var srcRe=/src=\\?["'](https?:\\?\/\\?\/[^\\"']+)[\\"']/gi;
      while((m=srcRe.exec(block[1]))!==null)add(m[1]);
      var direct=/https?:\\?\/\\?\/[^\\"'<>\s]+/gi;while((m=direct.exec(block[1]))!==null)add(m[0]);
    }
    return out;
  }
  async function resolveMovie(q){
    q=await metadata(q);if(!q.title)return [];
    var root=c.movieSite+"/anime/"+slug(q.title)+"/";
    var rp=await text(root,{headers:headers(c.movieSite+"/","text/html,application/xhtml+xml,*/*")});if(!rp)return [];
    var titleTag=(/<title[^>]*>([\s\S]*?)<\/title>/i.exec(rp.text)||[])[1]||"";
    if(slug(cleanLabel(titleTag)).indexOf(slug(q.title))<0)return [];
    var chapter=movieChapter(rp.text,rp.url||root,q);if(!chapter)return [];
    var cp=await text(chapter,{headers:headers(rp.url||root,"text/html,application/xhtml+xml,*/*")});if(!cp)return [];
    var ct=(/<title[^>]*>([\s\S]*?)<\/title>/i.exec(cp.text)||[])[1]||"";
    if(slug(cleanLabel(ct)).indexOf(slug(q.title))<0||!/film/i.test(ct))return [];
    var players=chapterPlayers(cp.text,cp.url||chapter);if(!players.length||typeof _crawlDirectMedia!=="function")return [];
    var rows;try{rows=await _crawlDirectMedia(players,cp.url||chapter,2)}catch(_e){rows=[]}
    if(!Array.isArray(rows))return [];
    var out=[],seen=Object.create(null);
    for(var i=0;i<rows.length&&out.length<c.maxStreams;i++){
      var x=rows[i];if(!x||!x.url||seen[x.url])continue;seen[x.url]=1;
      x.name=x.name||"VoirAnime | Movie";x.title=q.title+" | VOSTFR";x.language=x.language||"VOSTFR";x.provider="voiranime";out.push(x)
    }
    return out;
  }
  async function resolve(args,_ctx){var q=request(args);if(q===null)return null;if(!q||!q.tmdbId)return [];return await resolveMovie(q)}
  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"voiranime",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "movieSite": str(cfg.get("movie_site") or "https://voir-anime.to").rstrip("/"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": int(cfg.get("max_streams") or 4),
    }
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "scope": "movie-only-provider-resolver",
            "nativeFallback": "all-non-movie-requests",
            "movieIdentity": "tmdb-title-root-plus-film-chapter",
            "movieChapterSources": "madara-thisChapterSources",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "signedMediaPersisted": False,
            "providerBaseModified": False,
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
