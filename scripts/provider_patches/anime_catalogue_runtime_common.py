#!/usr/bin/env python3
"""Shared clean-v3 runtime generator for anime catalogue providers.

The upstream bundles remain knowledge-only. Provider-owned adapters consume Core
TMDB metadata and re-implement only the current provider transport contracts.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

WRAPPER = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function arr(v){return Array.isArray(v)?v:[]}
  function uniq(v){var out=[],seen={};for(var i=0;i<v.length;i++){var x=s(v[i]);if(!x||seen[x])continue;seen[x]=1;out.push(x)}return out}
  function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
  function slug(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").replace(/-+/g,"-")}
  function abs(url,base){try{return new URL(s(url),base).toString()}catch(_e){return ""}}
  function mdRow(raw){if(raw&&raw.state==="ok"&&raw.metadata)raw=raw.metadata;return raw&&typeof raw==="object"?raw:{}}
  function aliasesFrom(md){
    var alt=md.alternative_titles&&(md.alternative_titles.titles||md.alternative_titles.results||md.alternative_titles),out=[md.title,md.name,md.original_title,md.original_name];
    if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));
    return uniq(out).slice(0,6)
  }
  function requestMeta(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
    try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var md=mdRow((obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||null);
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"tv").toLowerCase();
    if(type==="movie")return null;
    var season=Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode=Number((obj&&obj.episode)!=null?obj.episode:args[3])||1;
    var aliases=aliasesFrom(md);if(!aliases.length)return null;
    var seasonCounts={};if(Array.isArray(md.seasons)){for(var i=0;i<md.seasons.length;i++){var row=md.seasons[i]||{},sn=Number(row.season_number),ec=Number(row.episode_count);if(sn>0&&ec>0)seasonCounts[sn]=ec}}
    return {aliases:aliases,title:aliases[0],season:season,episode:episode,seasonCounts:seasonCounts,type:"tv"}
  }
  function headers(accept){return {"User-Agent":c.userAgent,"Accept":accept||"application/json,text/html,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Referer":c.base+"/"}}
  async function text(url,accept){try{var r=await g.fetch(url,{headers:headers(accept)});if(!r||!r.ok)return "";return await r.text()}catch(_e){return ""}}
  async function json(url){try{var r=await g.fetch(url,{headers:headers("application/json,text/plain,*/*")});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
  function score(title,query){var a=norm(title),b=norm(query);if(!a||!b)return 0;if(a===b)return 100;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 70;var words=b.split(/\s+/),n=0;for(var i=0;i<words.length;i++)if(words[i].length>2&&a.split(/\s+/).indexOf(words[i])>=0)n+=12;return n}
  function lang(label){var x=s(label).toUpperCase();return x.indexOf("VF")===0?"VF":"VOSTFR"}
  function stream(url,name,language,quality,type,extraHeaders){var h={"Referer":c.base+"/"};if(extraHeaders)for(var k in extraHeaders)h[k]=extraHeaders[k];return {url:url,name:name,title:name,language:language||"fr",quality:quality||"HD",type:type||null,provider:c.provider,headers:h}}

  function nekoEpisodes(html){
    var out=[],re=/<a[^>]*href=["']([^"']+)["'][^>]*>[\s\S]{0,1200}?class=["'][^"']*epl-num[^"']*["'][^>]*>\s*(\d+)\s*</gi,m;
    while((m=re.exec(html))&&out.length<500)out.push({url:abs(m[1],c.base),num:Number(m[2])});return out
  }
  async function nekoTry(url){var h=await text(url,"text/html,*/*");if(h.length<500)return [];return nekoEpisodes(h)}
  async function neko(meta){
    var episodes=[],page="";
    for(var i=0;i<meta.aliases.length&&i<4&&!episodes.length;i++){
      var sl=slug(meta.aliases[i]);if(!sl)continue;var paths=["/anime/"+sl+"-saison-"+meta.season+"/","/anime/"+sl+"/"];
      if(meta.season===1)paths.push("/anime/"+sl+"-saison-1/");
      for(var p=0;p<paths.length&&!episodes.length;p++){episodes=await nekoTry(c.base+paths[p]);if(episodes.length)page=c.base+paths[p]}
    }
    if(!episodes.length){
      for(var a=0;a<meta.aliases.length&&a<4&&!episodes.length;a++){
        var sh=await text(c.base+"/?s="+encodeURIComponent(meta.aliases[a]),"text/html,*/*"),links=[],re=/href=["'](https?:\/\/[^"']*\/anime\/[^"']+)["']/gi,m,seen={};
        while((m=re.exec(sh))&&links.length<20){var u=m[1];if(!seen[u]){seen[u]=1;links.push(u)}}
        links.sort(function(x,y){return score(y,meta.aliases[a])-score(x,meta.aliases[a])});
        for(var q=0;q<links.length&&q<3&&!episodes.length;q++){episodes=await nekoTry(links[q]);if(episodes.length)page=links[q]}
      }
    }
    if(!episodes.length)return [];
    var ep=null;for(var e=0;e<episodes.length;e++)if(episodes[e].num===meta.episode){ep=episodes[e];break}if(!ep)return [];
    var eh=await text(ep.url,"text/html,*/*"),buttons=[],br=/loadMi\(\{\s*value:\s*['"]([A-Za-z0-9+/=]+)['"]\s*\}\)/g,bm;
    while((bm=br.exec(eh))&&buttons.length<12){try{var dec=atob(bm[1]),sm=dec.match(/src=["']([^"']+)["']/i);if(sm)buttons.push({url:sm[1].replace(/&#0*38;/g,"&"),label:(eh.slice(bm.index,bm.index+600).match(/>\s*([A-Z]+-?\d*)\s*<\/button>/i)||[])[1]||"VO"})}catch(_e){}}
    var out=[],have={VF:0,VOSTFR:0};
    for(var b=0;b<buttons.length&&out.length<2;b++){var l=lang(buttons[b].label);if(have[l])continue;var ph=await text(buttons[b].url,"text/html,*/*"),im=ph.match(/<iframe[^>]*src=["']([^"']+)["']/i),u=im?abs(im[1].replace(/&#0*38;/g,"&"),buttons[b].url):buttons[b].url;if(!u)continue;out.push(stream(u,c.name+" ["+l+"]",l,"HD",null,{"Referer":page||c.base+"/"}));have[l]=1}
    return out
  }

  function fullEpisodes(html){var out=[],re=/href=["'](\/voir-anime\/[^"']*\/episode\/(\d+))[^"']*["'][^>]*>/gi,m,seen={};while((m=re.exec(html))&&out.length<500){var n=Number(m[2]);if(!seen[n]){seen[n]=1;out.push({url:abs(m[1],c.base),num:n})}}return out}
  function fullEmbeds(html){var out=[],lm=html.match(/var\s+links\s*=\s*\[([\s\S]*?)\]/i);if(lm){var re=/["'](https?:[^"']+)["']/g,m;while((m=re.exec(lm[1]))&&out.length<12){var u=m[1].replace(/\\\//g,"/").replace(/\\/g,"");if(out.indexOf(u)<0)out.push(u)}}if(!out.length){var im=html.match(/<iframe[^>]*src=["'](https?:\/\/[^"']+)["']/i);if(im)out.push(im[1])}return out}
  async function fullanime(meta){
    var episodes=[],page="";
    for(var i=0;i<meta.aliases.length&&i<4&&!episodes.length;i++){var sl=slug(meta.aliases[i]);if(!sl)continue;var paths=[];if(meta.season>1)paths.push("/voir-anime/"+sl+"-saison-"+meta.season+"-vostfr");paths.push("/voir-anime/"+sl+"-vostfr");for(var p=0;p<paths.length&&!episodes.length;p++){var h=await text(c.base+paths[p],"text/html,*/*");episodes=fullEpisodes(h);if(episodes.length)page=c.base+paths[p]}}
    if(!episodes.length){for(var a=0;a<meta.aliases.length&&a<4&&!episodes.length;a++){var sh=await text(c.base+"/search?s="+encodeURIComponent(meta.aliases[a]),"text/html,*/*"),links=[],re=/href=["'](\/voir-anime\/[^"']+)["']/gi,m,seen={};while((m=re.exec(sh))&&links.length<20){var u=abs(m[1],c.base);if(!seen[u]){seen[u]=1;links.push(u)}}links.sort(function(x,y){return score(y,meta.aliases[a])-score(x,meta.aliases[a])});for(var q=0;q<links.length&&q<3&&!episodes.length;q++){var dh=await text(links[q],"text/html,*/*");episodes=fullEpisodes(dh);if(episodes.length)page=links[q]}}}
    if(!episodes.length)return [];var ep=null;for(var e=0;e<episodes.length;e++)if(episodes[e].num===meta.episode){ep=episodes[e];break}if(!ep)return [];
    var eh=await text(ep.url,"text/html,*/*"),embeds=fullEmbeds(eh);embeds.sort(function(a,b){function rank(u){u=u.toLowerCase();if(u.indexOf("vidmoly")>=0)return 0;if(u.indexOf("oneupload")>=0)return 1;if(u.indexOf("sendvid")>=0)return 2;return 9}return rank(a)-rank(b)});var out=[];for(var z=0;z<embeds.length&&z<2;z++)out.push(stream(embeds[z],c.name+" [VOSTFR]","VOSTFR","HD",null,{"Referer":page||c.base+"/"}));return out
  }

  async function animevost(meta){
    var found=null;
    for(var i=0;i<meta.aliases.length&&i<4&&!found;i++){var data=await json(c.base+"/api/animes/search?q="+encodeURIComponent(meta.aliases[i])),rows=arr(data&&data.results);if(rows.length){rows.sort(function(a,b){return score(b.title||b.name||b.slug,meta.aliases[i])-score(a.title||a.name||a.slug,meta.aliases[i])});found=rows[0]}}
    if(!found||!found.slug)return [];var detail=await json(c.base+"/api/animes/"+encodeURIComponent(found.slug)),seasons=arr(detail&&detail.seasons),season=null;for(var a=0;a<seasons.length;a++)if(Number(seasons[a]&&seasons[a].season_number)===meta.season){season=seasons[a];break}if(!season)season=seasons[0]||null;if(!season)return [];
    var eps=arr(season.episodes),ep=null;for(var e=0;e<eps.length;e++)if(Number(eps[e]&&eps[e].episode_number)===meta.episode){ep=eps[e];break}if(!ep)ep=eps[0]||null;if(!ep)return [];
    var streams=arr(ep.streams),out=[];for(var z=0;z<streams.length&&out.length<8;z++){var r=streams[z]||{},u=s(r.video_url);if(!u)continue;out.push(stream(u,c.name+" ["+s(r.quality||"1080p")+"] ["+s(r.language||"VOSTFR")+"]","fr",s(r.quality||"1080p"),null))}return out
  }

  async function wave(meta){
    var chosen=null;
    for(var i=0;i<meta.aliases.length&&i<4&&!chosen;i++){var rows=await json(c.base+"/api/series?query="+encodeURIComponent(meta.aliases[i]));rows=arr(rows).filter(function(r){return r&&(r.format==="serie"||r.format==="kai")});rows.sort(function(a,b){return score(b.title,meta.aliases[i])-score(a.title,meta.aliases[i])});if(rows.length&&score(rows[0].title,meta.aliases[i])>=40)chosen=rows[0]}
    if(!chosen){var cat=arr(await json(c.base+"/api/series?limit=100")),best=0;for(var cidx=0;cidx<cat.length;cidx++){var row=cat[cidx];if(!row||(row.format!=="serie"&&row.format!=="kai"))continue;for(var a=0;a<meta.aliases.length;a++){var sc=score(row.title,meta.aliases[a]);if(sc>best){best=sc;chosen=row}}}if(best<40)chosen=null}
    if(!chosen||chosen.id==null)return [];var detail=await json(c.base+"/api/series/"+encodeURIComponent(String(chosen.id))),eps=arr(detail&&detail.episodes),ep=null;
    for(var e=0;e<eps.length;e++)if(Number(eps[e]&&eps[e].season_number)===meta.season&&Number(eps[e]&&eps[e].number)===meta.episode){ep=eps[e];break}
    if(!ep&&chosen.format==="kai"&&meta.season>1){var offset=0,ok=true;for(var sn=1;sn<meta.season;sn++){var count=Number(meta.seasonCounts[sn]||0);if(!count){ok=false;break}offset+=count}if(ok){var target=offset+meta.episode;for(var q=0;q<eps.length;q++)if(Number(eps[q]&&eps[q].season_number)===1&&Number(eps[q]&&eps[q].number)===target){ep=eps[q];break}}}
    if(!ep||ep.id==null)return [];var u=c.base+"/playback/"+encodeURIComponent(String(ep.id))+"/manifest.mpd",quality="HD",mpd=await text(u,"application/dash+xml,text/xml,*/*"),re=/height=["'](\d+)["']/g,m,max=0;while((m=re.exec(mpd))){var h=Number(m[1]);if(h>max)max=h}if(max)quality=String(max)+"p";return [stream(u,c.name+" [VOSTFR]","VOSTFR",quality,"dash",{"Origin":c.base})]
  }

  async function resolve(args){var meta=requestMeta(args);if(!meta)return [];if(c.mode==="neko_wp")return await neko(meta);if(c.mode==="fullanime_php")return await fullanime(meta);if(c.mode==="animevost_api")return await animevost(meta);if(c.mode==="waveanime_api")return await wave(meta);return []}
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__niakvioAnimeCatalogueRuntimeV1)return false;var wrapped=async function(){try{return await resolve(arguments)}catch(_e){return []}};wrapped.__niakvioAnimeCatalogueRuntimeV1=true;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply_runtime(
    text: str,
    *,
    managed_fix_id: str,
    marker: str,
    defaults: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> str:
    payload = dict(defaults)
    payload.update(dict(options or {}))
    payload["base"] = str(payload.get("base") or "").rstrip("/")
    payload["provider"] = str(payload.get("provider") or "").strip()
    payload["name"] = str(payload.get("name") or payload["provider"]).strip()
    payload["mode"] = str(payload.get("mode") or "").strip()
    payload["userAgent"] = str(
        payload.get("userAgent")
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3"
    )
    if not payload["base"].startswith(("http://", "https://")):
        raise ValueError(f"{managed_fix_id}: base must be http(s)")
    if payload["mode"] not in {"neko_wp", "fullanime_php", "animevost_api", "waveanime_api"}:
        raise ValueError(f"{managed_fix_id}: unsupported mode={payload['mode']!r}")
    wrapper = WRAPPER.replace("MARKER_PLACEHOLDER", marker).replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        managed_fix_id,
        wrapper,
        data={
            "runtime": payload,
            "identity": "core-tmdb-aliases-anime-only",
            "movieAliasAllowed": False,
            "animeTvTransportAliasAllowed": True,
            "legacyExecutableSeed": False,
        },
    )
