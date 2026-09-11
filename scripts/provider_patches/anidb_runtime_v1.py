#!/usr/bin/env python3
"""AniDB.app clean-v3 runtime adapter.

Runtime contract follows the current public AniDB frontend used by ani-cli:
search HTML -> anime id -> episode API -> language/embed API -> HLS master.
Canonical anime identity is required before the first provider network request.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIDB.RUNTIME.V1"
MARKER = "NIAKVIO_ANIDB_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIDB_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function slug(v){return s(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
  function abs(base,value){try{return new URL(s(value),base).href}catch(_e){return ""}}
  function request(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var canonical=s((obj&&(obj.canonicalMediaType||obj.semanticType))||ctx.canonicalMediaType||"").toLowerCase();
    if(canonical!=="anime")return null;
    var meta=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||{};
    var title=s((obj&&(obj.title||obj.name))||meta.title||meta.name||meta.original_name||meta.original_title||ctx.title||"");
    if(!title)return null;
    var ep=Number((obj&&obj.episode)!=null?obj.episode:(ctx.episode!=null?ctx.episode:args[3]))||1;
    if(ep<1)return null;
    return {title:title,episode:ep};
  }
  function headers(referer,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"*/*"};if(referer)h.Referer=referer;return h}
  async function text(url,referer){try{var r=await g.fetch(url,{headers:headers(referer,"text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"),redirect:"follow"});if(!r||!r.ok)return null;return await r.text()}catch(_e){return null}}
  async function json(url,referer){var raw=await text(url,referer);if(raw==null)return null;try{return JSON.parse(raw)}catch(_e){return null}}
  function searchIds(html,title){
    var target=slug(title),out=[],seen=Object.create(null),re=/href=["'](?:https?:\/\/[^"']+)?\/anime\/([a-z0-9-]+-([0-9]+))["']/gi,m;
    while((m=re.exec(html||""))!==null){var full=s(m[1]),id=s(m[2]),base=full.replace(/-[0-9]+$/,'');if(!id||seen[id])continue;seen[id]=1;out.push({id:id,slug:base,score:base===target?3:(base.indexOf(target)===0||target.indexOf(base)===0?2:0)})}
    out.sort(function(a,b){return b.score-a.score});return out;
  }
  function collectEpisodes(node,out){
    if(!node)return;
    if(Array.isArray(node)){for(var i=0;i<node.length;i++)collectEpisodes(node[i],out);return}
    if(typeof node!=="object")return;
    if(node.id!=null&&node.number!=null){var id=Number(node.id),num=Number(node.number);if(id>0&&num>0)out.push({id:id,number:num})}
    Object.keys(node).forEach(function(k){collectEpisodes(node[k],out)});
  }
  function collectEmbeds(node,path,out){
    if(!node)return;
    if(Array.isArray(node)){for(var i=0;i<node.length;i++)collectEmbeds(node[i],path,out);return}
    if(typeof node!=="object")return;
    var embed=s(node.embed_url||node.embedUrl||"");
    if(embed){var lang=s(node.language||node.lang||path[path.length-1]||"original").toLowerCase();out.push({url:embed,lang:lang})}
    Object.keys(node).forEach(function(k){if(k!=="embed_url"&&k!=="embedUrl")collectEmbeds(node[k],path.concat([k]),out)});
  }
  function masterFromEmbed(html,base){
    var patterns=[/file\s*:\s*["']([^"']+)["']/i,/source\s*:\s*["']([^"']+\.m3u8[^"']*)["']/i,/["'](https?:\/\/[^"']+\.m3u8[^"']*)["']/i];
    for(var i=0;i<patterns.length;i++){var m=patterns[i].exec(html||"");if(m){var u=abs(base,m[1].replace(/\\\//g,"/"));if(/^https?:\/\//i.test(u))return u}}
    return "";
  }
  function langLabel(v){var x=s(v).toLowerCase();if(/eng|dub/.test(x))return "EN Dub";if(/jpn|jp|sub/.test(x))return "JP Sub";return x?x.toUpperCase():"Original"}
  async function resolve(args){
    var q=request(args);if(!q)return [];
    var base=s(c.base).replace(/\/+$/,"");if(!/^https?:\/\//i.test(base))return [];
    var searchUrl=base+"/browse?q="+encodeURIComponent(q.title),searchHtml=await text(searchUrl,base+"/");if(!searchHtml)return [];
    var candidates=searchIds(searchHtml,q.title);if(!candidates.length||candidates[0].score<2)return [];
    var animeId=candidates[0].id;
    var eps=await json(base+"/api/frontend/anime/"+encodeURIComponent(animeId)+"/episodes",searchUrl);if(!eps)return [];
    var episodeRows=[];collectEpisodes(eps,episodeRows);var selected=null;
    for(var i=0;i<episodeRows.length;i++){if(Number(episodeRows[i].number)===q.episode){selected=episodeRows[i];break}}
    if(!selected)return [];
    var langs=await json(base+"/api/frontend/episode/"+selected.id+"/languages",searchUrl);if(!langs)return [];
    var embeds=[];collectEmbeds(langs,[],embeds);if(!embeds.length)return [];
    var out=[],seen=Object.create(null);
    for(var j=0;j<embeds.length;j++){
      var embed=abs(base,embeds[j].url);if(!embed)continue;
      var page=await text(embed,searchUrl);if(!page)continue;
      var master=masterFromEmbed(page,embed);if(!master||seen[master])continue;
      var manifest=await text(master,embed);if(!manifest||!/^#EXTM3U/m.test(manifest))continue;
      seen[master]=1;out.push({name:"AniDB | "+langLabel(embeds[j].lang),title:"AniDB | "+langLabel(embeds[j].lang),url:master,quality:"HD",language:langLabel(embeds[j].lang),headers:headers(embed,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"anidb"});
      if(out.length>=c.maxStreams)break;
    }
    return out;
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__niakvioAniDbRuntimeV1)return false;var wrapped=async function(){return await resolve(arguments)};wrapped.__niakvioAniDbRuntimeV1=true;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://anidb.app"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        ),
        "maxStreams": int(cfg.get("max_streams") or 4),
    }
    wrapper = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "identity": "canonical-anime-title-before-network",
            "search": "/browse?q={title}",
            "episodes": "/api/frontend/anime/{id}/episodes",
            "languages": "/api/frontend/episode/{episodeId}/languages",
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
