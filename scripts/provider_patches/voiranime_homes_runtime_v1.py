#!/usr/bin/env python3
"""VoirAnime.homes current catalogue -> episode JSON -> HLS runtime.

Current search results encode the provider-local id as the numeric prefix of
`/<id>-<slug>.html`. Episode JSON then exposes per-language embed hosts. Only
validated direct HLS output is returned; signed/player URLs remain runtime-only.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VOIRANIME.HOMES.RUNTIME.V1"
MARKER = "NIAKVIO_VOIRANIME_HOMES_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VOIRANIME_HOMES_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function slug(v){return s(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
  function request(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var canonical=s((obj&&(obj.canonicalMediaType||obj.semanticType))||ctx.canonicalMediaType||"").toLowerCase();if(canonical!=="anime")return null;
    var season=Number((obj&&obj.season)!=null?obj.season:(ctx.season!=null?ctx.season:args[2]))||0;
    var episode=Number((obj&&obj.episode)!=null?obj.episode:(ctx.episode!=null?ctx.episode:args[3]))||0;
    if(!season||!episode)return null;
    var meta=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||{};
    var title=s((obj&&(obj.title||obj.name))||meta.title||meta.name||meta.original_title||meta.original_name||ctx.title||"");if(!title)return null;
    return {title:title,season:season,episode:episode};
  }
  function headers(referer,accept){return {"User-Agent":c.userAgent,"Accept":accept||"*/*","Referer":referer||c.site+"/"}}
  async function text(url,init){try{var r=await g.fetch(url,Object.assign({redirect:"follow"},init||{}));if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url}}catch(_e){return null}}
  async function search(q){
    var body="query="+encodeURIComponent(q.title)+"&page=1";
    return await text(c.site+"/engine/ajax/search.php",{method:"POST",headers:Object.assign(headers(c.site+"/","text/html,*/*"),{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"}),body:body});
  }
  function candidates(html,q){
    var out=[],re=/<div\b[^>]*class=['"][^'"]*search-item[^'"]*['"][^>]*onclick=['"]location\.href=(?:&quot;|['"])(\/([0-9]+)-([^'"&]+?)\.html)(?:&quot;|['"])[^>]*>([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>/gi,m;
    while((m=re.exec(html||""))!==null){
      var block=m[4]||"",tm=/<h3\b[^>]*class=['"][^'"]*search-title[^'"]*['"][^>]*>([\s\S]*?)<\/h3>/i.exec(block),name=s((tm&&tm[1]||"").replace(/<[^>]+>/g," "));
      var p=m[1],id=m[2],sl=m[3],score=0,target=slug(q.title),cand=slug(name||sl);
      if(cand===target)score+=100;else if(cand.indexOf(target)>=0||target.indexOf(cand)>=0)score+=55;
      var toks=target.split("-").filter(function(x){return x.length>=3});for(var i=0;i<toks.length;i++)if(cand.indexOf(toks[i])>=0)score+=8;
      if(new RegExp("(?:^|-)saison-0*"+q.season+"(?:-|$)","i").test(sl))score+=60;
      out.push({id:id,path:p,slug:sl,name:name,score:score});
    }
    if(!out.length){
      var loose=/location\.href=['"]\/([0-9]+)-([^'"]+)\.html['"]/gi,x;while((x=loose.exec(html||""))!==null){var sc=slug(x[2]).indexOf(slug(q.title))>=0?50:0;if(new RegExp("saison-0*"+q.season,"i").test(x[2]))sc+=60;out.push({id:x[1],path:"/"+x[1]+"-"+x[2]+".html",slug:x[2],name:"",score:sc})}
    }
    out.sort(function(a,b){return b.score-a.score});return out;
  }
  function hlsCandidates(raw){
    var value=s(raw).replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/&amp;/gi,"&"),out=[],seen={};
    var re=/https?:\/\/[^"'<>\\\s]+\.m3u8[^"'<>\\\s]*/gi,m;while((m=re.exec(value))!==null){var u=m[0];if(!seen[u]){seen[u]=1;out.push(u)}}return out;
  }
  async function resolveEmbed(embed,detail){
    var page=await text(embed,{headers:headers(detail,"text/html,*/*")});if(!page)return null;
    var urls=hlsCandidates(page.text);
    for(var i=0;i<urls.length&&i<3;i++){
      var media=await text(urls[i],{headers:headers(page.url||embed,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")});
      if(media&&/^#EXTM3U/m.test(media.text))return {url:urls[i],referer:page.url||embed,manifest:media.text};
    }
    return null;
  }
  function quality(text){var best=0,re=/RESOLUTION=\d+x(\d+)/gi,m;while((m=re.exec(text||""))!==null){var n=parseInt(m[1],10)||0;if(n>best)best=n}return best?best+"p":"HD"}
  async function resolve(args){
    var q=request(args);if(!q)return [];
    var sr=await search(q);if(!sr)return [];
    var rows=candidates(sr.text,q);if(!rows.length||rows[0].score<50)return [];
    var chosen=rows[0],detail=c.site+chosen.path,api=c.site+"/engine/ajax/manga_episodes_api.php?id="+encodeURIComponent(chosen.id);
    var ep=await text(api,{headers:headers(detail,"application/json,*/*")});if(!ep)return [];
    var data;try{data=JSON.parse(ep.text)}catch(_e){return []}
    var out=[],seen={};
    for(var li=0;li<c.languageOrder.length;li++){
      var key=c.languageOrder[li],lang=data&&data[key],slot=lang&&lang[String(q.episode)];if(!slot||typeof slot!=="object")continue;
      var hosts=Object.keys(slot);
      for(var hi=0;hi<hosts.length;hi++){
        var host=hosts[hi],embed=s(slot[host]);if(!/^https?:\/\//i.test(embed))continue;
        var media=await resolveEmbed(embed,detail);if(!media||seen[media.url])continue;seen[media.url]=1;
        var label=key.toLowerCase()==="vf"?"VF":"VOSTFR";
        out.push({name:"VoirAnime | "+host+" | "+label,title:"VoirAnime | "+host+" | "+label,url:media.url,quality:quality(media.manifest),language:label,headers:headers(media.referer,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"voiranime",isDirect:true});
        if(out.length>=c.maxStreams)return out;
      }
    }
    return out;
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__niakvioVoirAnimeHomesV1)return false;var wrapped=async function(){return await resolve(arguments)};wrapped.__niakvioVoirAnimeHomesV1=true;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "site": str(cfg.get("site") or "https://voiranime.homes"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"),
        "languageOrder": cfg.get("language_order") or ["vf", "vostfr"],
        "maxStreams": int(cfg.get("max_streams") or 4),
    }
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={"runtime": payload, "identity": "canonical-anime-title-season", "searchId": "numeric-href-prefix", "episodeJson": "vf-vostfr-host-map", "signedMediaPersisted": False, "legacyExecutableSeed": False},
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
