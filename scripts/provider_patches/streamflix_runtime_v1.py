#!/usr/bin/env python3
"""StreamFlix clean-v3 HTTP runtime adapter.

The historical provider used a Firebase WebSocket for episodic data. Clean v3
uses the equivalent bounded Firebase REST path, avoiding a non-cooperative
WebSocket in native QuickJS while preserving the same catalogue/config model.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.STREAMFLIX.RUNTIME.V1"
MARKER = "NIAKVIO_STREAMFLIX_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_STREAMFLIX_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function norm(v){
    var x=s(v);
    try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}
    return x.toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  }
  function arr(v){return Array.isArray(v)?v:[]}
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null;
    var ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||null;
    if(md&&md.state==="ok"&&md.metadata)md=md.metadata;
    md=md&&typeof md==="object"?md:{};
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    var date=s(md.release_date||md.first_air_date||md.year);
    return {
      id:s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0],
      type:type==="movie"?"movie":"tv",
      title:s(md.title||md.name||md.original_title||md.original_name),
      year:date.slice(0,4),
      season:Number((obj&&obj.season)!=null?obj.season:args[2])||0,
      episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||0
    };
  }
  async function json(url){
    var response=await g.fetch(url,{headers:{
      "Accept":"application/json,text/plain,*/*",
      "User-Agent":c.userAgent,
      "Referer":c.apiBase+"/"
    },redirect:"follow"});
    if(!response||!response.ok)throw new Error("streamflix_http_"+(response&&response.status||0));
    return await response.json();
  }
  function yearOf(row){
    var raw=s(row&&(row.year||row.movieyear||row.releaseYear||row.release_year||row.date));
    var m=raw.match(/(?:19|20)\d{2}/);return m?m[0]:"";
  }
  function mediaKind(row){
    var raw=s(row&&(row.type||row.mediaType||row.media_type||row.movietype)).toLowerCase();
    if(/tv|series|show/.test(raw))return "tv";
    if(/movie|film/.test(raw))return "movie";
    return "";
  }
  function choose(q,rows){
    var wanted=norm(q.title),best=null,bestScore=-1;
    for(var i=0;i<rows.length;i++){
      var row=rows[i];if(!row||!row.moviename)continue;
      var title=norm(row.moviename),score=0;
      if(title===wanted)score+=300;
      else if(title&&wanted&&(title.indexOf(wanted)>=0||wanted.indexOf(title)>=0))score+=100;
      else continue;
      var kind=mediaKind(row);if(kind&&kind!==q.type)continue;
      if(kind===q.type)score+=40;
      var year=yearOf(row);
      if(q.year&&year&&q.year!==year)continue;
      if(q.year&&year===q.year)score+=30;
      if(score>bestScore){bestScore=score;best=row}
    }
    return bestScore>=100?best:null;
  }
  function absolute(base,path){
    var b=s(base),p=s(path);if(!b||!p)return "";
    if(/^https?:\/\//i.test(p))return p;
    return b.replace(/\/+$/,"/")+p.replace(/^\/+/, "");
  }
  function output(q,label,url,size){
    if(!/^https?:\/\//i.test(s(url)))return null;
    return {
      name:"StreamFlix",
      title:q.title+(q.type==="tv"?" S"+q.season+"E"+q.episode:"")+" - "+label,
      url:url,
      quality:label==="Premium"?"1080p":"720p",
      size:size||"Unknown",
      type:"direct",
      headers:{"Referer":c.apiBase+"/","User-Agent":c.userAgent},
      provider:"streamflix"
    };
  }
  function selectEpisode(value,episode){
    if(!value||typeof value!=="object")return null;
    var keys=[String(Math.max(0,episode-1)),String(episode)];
    for(var i=0;i<keys.length;i++)if(value[keys[i]]&&typeof value[keys[i]]==="object")return value[keys[i]];
    var rows=Array.isArray(value)?value:Object.keys(value).map(function(k){return value[k]});
    for(var j=0;j<rows.length;j++){
      var r=rows[j];if(!r||typeof r!=="object")continue;
      var n=Number(r.episode||r.episode_number||r.number);
      if(n===episode)return r;
    }
    return null;
  }
  async function resolve(args){
    var q=requestArgs(args);
    if(!/^\d+$/.test(q.id)||!q.title)return [];
    if(q.type==="tv"&&(!q.season||!q.episode))return [];
    try{
      var pair=await Promise.all([
        json(c.apiBase+"/data.json"),
        json(c.apiBase+"/config/config-streamflixapp.json")
      ]);
      var catalog=pair[0]&&Array.isArray(pair[0].data)?pair[0].data:arr(pair[0]);
      var config=pair[1]||{},match=choose(q,catalog);
      if(!match)return [];
      var out=[],seen=Object.create(null);
      function push(label,base,path,size){
        var url=absolute(base,path);if(!url||seen[url])return;
        var row=output(q,label,url,size);if(row){seen[url]=1;out.push(row)}
      }
      if(q.type==="movie"){
        if(!match.movielink)return [];
        arr(config.premium).forEach(function(base){push("Premium",base,match.movielink,match.movieduration)});
        arr(config.movies).forEach(function(base){push("Standard",base,match.movielink,match.movieduration)});
        return out.slice(0,20);
      }
      if(!match.moviekey)return [];
      var path="/Data/"+encodeURIComponent(s(match.moviekey))+"/seasons/"+encodeURIComponent(String(q.season))+"/episodes.json";
      var episodeData=await json(c.firebaseBase+path);
      var ep=selectEpisode(episodeData,q.episode);
      if(!ep||!ep.link)return [];
      arr(config.premium).forEach(function(base){push("Premium",base,ep.link,ep.runtime?String(ep.runtime)+"min":"Unknown")});
      return out.slice(0,20);
    }catch(_e){return []}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioStreamFlixRuntimeV1)return false;
    var wrapped=async function(){return await resolve(arguments)};
    wrapped.__niakvioStreamFlixRuntimeV1=true;container[key]=wrapped;return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "apiBase": str(cfg.get("api_base") or "https://api.streamflix.app").rstrip("/"),
        "firebaseBase": str(
            cfg.get("firebase_base")
            or "https://chilflix-410be-default-rtdb.asia-southeast1.firebasedatabase.app"
        ).rstrip("/"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
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
            "identity": "core-tmdb-title-year",
            "transport": "bounded-http-firebase-rest",
            "legacyExecutableSeed": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
