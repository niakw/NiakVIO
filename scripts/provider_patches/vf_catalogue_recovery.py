#!/usr/bin/env python3
"""Append a conservative VF catalogue recovery wrapper.

The wrapper is provider-configured and only runs after the native provider has
returned no usable stream.  It follows the normal public catalogue flow:
TMDb metadata -> official terminal site/API -> content page -> embedded player.
It does not bypass access controls, solve CAPTCHAs, or fabricate direct media.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_VF_CATALOGUE_RECOVERY_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    strategy = str(cfg.get("strategy") or "html").strip().lower()
    base_url = str(cfg.get("base_url") or "").rstrip("/")
    api_url = str(cfg.get("api_url") or "").rstrip("/")
    supported_types = [str(v) for v in cfg.get("types", ["movie"]) if str(v) in {"movie", "tv", "anime"}]
    search_paths = [str(v) for v in cfg.get("search_paths", []) if str(v).strip()]
    direct_paths = [str(v) for v in cfg.get("direct_paths", []) if str(v).strip()]
    blocked_hosts = sorted({str(v).lower().strip().lstrip(".") for v in cfg.get("blocked_hosts", []) if str(v).strip()})
    blocked_paths = sorted({str(v).lower().strip() for v in cfg.get("blocked_path_patterns", []) if str(v).strip()})
    preferred_groups = [str(v) for v in cfg.get("preferred_player_groups", ["VFF", "VFQ", "VF", "Default", "VOSTFR"])]
    max_players = max(1, min(int(cfg.get("max_players", 8)), 20))
    timeout_ms = max(1500, min(int(cfg.get("timeout_ms", 7000)), 15000))
    if strategy not in {"html", "streamzo", "api_discovery"}:
        raise ValueError(f"vf_catalogue_recovery: unsupported strategy {strategy!r}")
    if strategy != "api_discovery" and not base_url:
        raise ValueError("vf_catalogue_recovery: base_url is required")
    if strategy == "api_discovery" and not api_url:
        raise ValueError("vf_catalogue_recovery: api_url is required")

    payload = {
        "strategy": strategy,
        "baseUrl": base_url,
        "apiUrl": api_url,
        "types": supported_types,
        "searchPaths": search_paths,
        "directPaths": direct_paths,
        "blockedHosts": blocked_hosts,
        "blockedPathPatterns": blocked_paths,
        "preferredPlayerGroups": preferred_groups,
        "maxPlayers": max_players,
        "timeoutMs": timeout_ms,
        "providerName": str(cfg.get("provider_name") or "VF source"),
        "recoveryFirst": bool(cfg.get("recovery_first", True)),
        "skipNativeWhenUnresolved": bool(cfg.get("skip_native_when_unresolved", False)),
        "obsoleteRouteTokens": [str(v).lower() for v in cfg.get("obsolete_route_tokens", []) if str(v).strip()],
        "maxDiscoveryScripts": max(1, min(int(cfg.get("max_discovery_scripts", 8)), 20)),
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text
    old = text.find(f"/* {MARKER}:")
    if old >= 0:
        call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', old)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated VF catalogue recovery wrapper")
        text = (text[:old] + text[end + 2 :]).rstrip()

    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,config){
  "use strict";
  var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
  function clean(v){return String(v==null?"":v).replace(/&amp;/gi,"&").trim()}
  function stripHtml(v){return clean(v).replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim()}
  function normalize(v){try{return String(v||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return String(v||"").toLowerCase()}}
  function slug(v){return normalize(v).replace(/\s+/g,"-").replace(/-+/g,"-").replace(/^-|-$/g,"")}
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function blocked(raw){
    try{
      var u=new URL(String(raw)); var h=u.hostname.toLowerCase(),p=u.pathname.toLowerCase();
      for(var i=0;i<config.blockedHosts.length;i++){var x=config.blockedHosts[i];if(h===x||h.endsWith("."+x))return true}
      for(var j=0;j<config.blockedPathPatterns.length;j++)if(p.indexOf(config.blockedPathPatterns[j])>=0)return true;
      if(/(?:youtube\.com|youtu\.be|googlevideo\.com)$/.test(h)||/(?:trailer|bande-annonce)/i.test(p))return true;
      return false;
    }catch(_e){return true}
  }
  function usable(raw){var u=clean(raw);return /^https?:\/\//i.test(u)&&!blocked(u)&&!/(?:\.jpg|\.jpeg|\.png|\.webp|\.gif|\.css|\.js|favicon)(?:[?#]|$)/i.test(u)}
  function headers(base){try{var u=new URL(base);return {Referer:u.origin+"/",Origin:u.origin,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.6"}}catch(_e){return {"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.6"}}}
  async function request(url,asJson){
    var c=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{c.abort()}catch(_e){}},config.timeoutMs);
    try{
      var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:{"Accept":asJson?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*;q=0.8","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.6"},signal:c.signal});
      if(!r||!r.ok)return null;
      return asJson?await r.json():await r.text();
    }catch(_e){return null}finally{clearTimeout(timer);try{c.abort()}catch(_e){}}
  }
  function argumentsOf(args){
    var first=args[0],out={};
    if(first&&typeof first==="object"&&!Array.isArray(first))out=Object.assign({},first);
    else{out.tmdbId=String(first||"");out.mediaType=String(args[1]||"movie");out.season=args[2];out.episode=args[3];out.settings=args[4]||{}}
    out.tmdbId=String(out.tmdbId||out.id||"");out.mediaType=String(out.mediaType||out.type||out.category||"movie").toLowerCase();
    return out;
  }
  async function metadata(req){
    var title=clean(req.title||req.name||req.label||req.settings&&req.settings.title),year=Number(req.year||req.settings&&req.settings.year)||0,original="";
    if(title)title=title.replace(/\s*\(\d{4}\)\s*$/,"");
    if(!title&&req.tmdbId){
      var kind=req.mediaType==="tv"?"tv":"movie",data=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(req.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR",true);
      if(data){title=clean(data.title||data.name);original=clean(data.original_title||data.original_name);var date=clean(data.release_date||data.first_air_date);year=Number(date.slice(0,4))||year}
    }
    return {title:title,original:original,year:year};
  }
  function score(label,meta,url){
    var a=normalize(label),wanted=normalize(meta.title),original=normalize(meta.original),s=0;
    if(!a)return -100;
    if(a===wanted||original&&a===original)s+=100;else if(a.indexOf(wanted)>=0||wanted.indexOf(a)>=0)s+=65;else{
      var words=wanted.split(" ").filter(function(x){return x.length>2}),hit=words.filter(function(x){return a.indexOf(x)>=0}).length;s+=words.length?Math.round(hit/words.length*50):0;
    }
    if(meta.year&&String(label+" "+url).indexOf(String(meta.year))>=0)s+=20;
    if(/(?:film|movie|streaming|watch|voir)/i.test(url))s+=8;
    return s;
  }
  function links(html,base,meta){
    var rows=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;
    while((m=re.exec(String(html||"")))!==null){var url=absolute(m[1],base),label=stripHtml(m[2]);if(!url||seen[url])continue;seen[url]=1;var s=score(label,meta,url);if(s>=38)rows.push({url:url,label:label,score:s})}
    return rows.sort(function(a,b){return b.score-a.score}).slice(0,8);
  }
  function players(html,base){
    var found=[],seen=Object.create(null),text=String(html||"").replace(/\\\//g,"/");
    var patterns=[
      /(?:data-embed|data-src|data-player|data-url|data-video)=["']([^"']+)["']/gi,
      /<iframe\b[^>]*src=["']([^"']+)["']/gi,
      /<(?:source|video)\b[^>]*src=["']([^"']+)["']/gi,
      /(?:file|src|url)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,
      /(https?:\/\/[^"'<>\s]+(?:\.m3u8|\/embed[-/]|\/e\/|\/player\/)[^"'<>\s]*)/gi
    ];
    for(var p=0;p<patterns.length;p++){var re=patterns[p],m;while((m=re.exec(text))!==null){var u=absolute(m[1],base);if(!usable(u)||seen[u])continue;seen[u]=1;found.push(u);if(found.length>=config.maxPlayers)return found}}
    return found;
  }
  function streamRows(urls,base,label){return urls.slice(0,config.maxPlayers).map(function(url,index){return {name:config.providerName+(urls.length>1?" #"+(index+1):""),title:config.providerName+" - "+label,url:url,quality:"HD",language:"fr",headers:headers(base),isDirect:/(?:\.m3u8|\.mp4|\.mpd)(?:[?#]|$)/i.test(url)}})}
  function episodePlayers(html,base,req){
    if(!req||req.mediaType!=="tv")return [];
    var season=Number(req.season)||1,episode=Number(req.episode)||1,text=String(html||"").replace(/\\\//g,"/"),urls=[],seen=Object.create(null);
    var blocks=text.match(/<[^>]+(?:data-season|data-saison)=["'][^"']+["'][^>]*(?:data-episode|data-ep)=["'][^"']+["'][^>]*>/gi)||[];
    blocks.forEach(function(tag){
      var sm=tag.match(/(?:data-season|data-saison)=["'](\d+)["']/i),em=tag.match(/(?:data-episode|data-ep)=["'](\d+)["']/i);
      if(!sm||!em||Number(sm[1])!==season||Number(em[1])!==episode)return;
      var um=tag.match(/(?:data-embed|data-src|data-player|data-url|data-video|src)=["']([^"']+)["']/i),u=um&&absolute(um[1],base);
      if(usable(u)&&!seen[u]){seen[u]=1;urls.push(u)}
    });
    var jsonRe=/[\{,]\s*["']?(?:season|saison)["']?\s*:\s*(\d+)[\s\S]{0,500}?["']?(?:episode|ep)["']?\s*:\s*(\d+)[\s\S]{0,700}?["']?(?:url|src|embedUrl|embed_url|player)["']?\s*:\s*["'](https?:\\?\/\\?\/[^"']+)["']/gi,m;
    while((m=jsonRe.exec(text))!==null){if(Number(m[1])!==season||Number(m[2])!==episode)continue;var u=absolute(m[3].replace(/\\\//g,"/"),base);if(usable(u)&&!seen[u]){seen[u]=1;urls.push(u)}}
    return urls;
  }
  function episodeLinks(html,base,req){
    if(!req||req.mediaType!=="tv")return [];
    var season=Number(req.season)||1,episode=Number(req.episode)||1,out=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;
    var patterns=[new RegExp("s(?:aison)?[ ._-]*0?"+season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+episode,"i"),new RegExp("saison[ ._-]*0?"+season+"[\s\S]{0,40}(?:episode|ep)[ ._-]*0?"+episode,"i")];
    while((m=re.exec(String(html||"")))!==null){var u=absolute(m[1],base),label=stripHtml(m[2])+" "+m[1];if(!u||seen[u]||!patterns.some(function(p){return p.test(label)}))continue;seen[u]=1;out.push(u)}
    return out.slice(0,8);
  }
  var discoveredApiRoute=null,discoveryComplete=false;
  function routeFromText(text,req){
    var raw=String(text||""),matches=[],re=/["'`]([^"'`]{0,180}\/api\/[^"'`]{1,220})["'`]/g,m;
    while((m=re.exec(raw))!==null){
      var value=clean(m[1]);if(!/(?:movie|tv|film|season|episode)/i.test(value))continue;
      var low=value.toLowerCase(),obsolete=false;
      for(var i=0;i<config.obsoleteRouteTokens.length;i++)if(low.indexOf(config.obsoleteRouteTokens[i])>=0){obsolete=true;break}
      if(obsolete)continue;
      value=value.replace(/\$\{[^}]+\}|:[a-z_][a-z0-9_]*|\{(?:id|tmdbid|tmdb_id)\}/ig,"{id}")
                 .replace(/\{(?:type|media_type|mediatype)\}/ig,"{type}")
                 .replace(/\{season\}/ig,"{season}").replace(/\{episode\}/ig,"{episode}");
      if(value.indexOf("{id}")<0){
        if(/\/(?:movie|film|tv)(?:\/|$)/i.test(value))value=value.replace(/\/?$/,"/{id}");else continue;
      }
      matches.push(value);
    }
    return Array.from(new Set(matches));
  }
  function materializeRoute(tpl,req){
    var type=req.mediaType==="tv"?"tv":"movie";
    return tpl.replace(/\{id\}/g,encodeURIComponent(req.tmdbId)).replace(/\{type\}/g,type)
      .replace(/\{season\}/g,String(Number(req.season)||1)).replace(/\{episode\}/g,String(Number(req.episode)||1));
  }
  async function discoverApiRoutes(req){
    if(discoveryComplete)return discoveredApiRoute?[discoveredApiRoute]:[];
    discoveryComplete=true;var documents=[],home=await request(config.baseUrl||config.apiUrl,false);if(home)documents.push(home);
    if(home){
      var scripts=[],re=/<script\b[^>]*src=["']([^"']+)["']/gi,m;
      while((m=re.exec(home))!==null&&scripts.length<config.maxDiscoveryScripts){var u=absolute(m[1],config.baseUrl||config.apiUrl);if(u&&!blocked(u))scripts.push(u)}
      for(var i=0;i<scripts.length;i++){var body=await request(scripts[i],false);if(body)documents.push(body)}
    }
    var candidates=[];documents.forEach(function(doc){candidates=candidates.concat(routeFromText(doc,req))});
    candidates=Array.from(new Set(candidates)).slice(0,24);
    for(var j=0;j<candidates.length;j++){
      var endpoint=absolute(materializeRoute(candidates[j],req),config.apiUrl+"/");if(!endpoint)continue;
      try{if(new URL(endpoint).origin!==new URL(config.apiUrl).origin)continue}catch(_e){continue}
      var data=await request(endpoint,true);if(data&&data.success!==false){discoveredApiRoute=candidates[j];return [discoveredApiRoute]}
    }
    return [];
  }
  function collectRows(rows,urls){if(Array.isArray(rows))rows.forEach(function(row){var u=clean(row&&row.url||row&&row.src||row&&row.embedUrl||row);if(usable(u))urls.push(u)})}
  function apiPlayers(data,req){
    var groups=data&&data.players||data&&data.links||{},urls=[];
    if(req&&req.mediaType==="tv"&&data&&data.episodes){
      var season=String(Number(req.season)||1),episode=String(Number(req.episode)||1),root=data.episodes;
      var selected=root[episode]||root[Number(episode)]||root[season]&&root[season][episode]||root[season]&&root[season][Number(episode)];
      if(selected){
        if(selected.languages&&typeof selected.languages==="object")Object.keys(selected.languages).forEach(function(k){collectRows(selected.languages[k],urls)});
        ["vf","vff","vfq","vostfr","vo","default","players","links"].forEach(function(k){collectRows(selected[k],urls)});
        if(Array.isArray(selected))collectRows(selected,urls);
      }
    }
    config.preferredPlayerGroups.forEach(function(group){collectRows(groups[group],urls)});
    if(!urls.length&&groups&&typeof groups==="object")Object.keys(groups).forEach(function(group){collectRows(groups[group],urls)});
    return Array.from(new Set(urls));
  }
  async function apiDiscovery(req,meta){
    var routes=await discoverApiRoutes(req);if(!routes.length)return [];
    var endpoint=absolute(materializeRoute(routes[0],req),config.apiUrl+"/"),data=await request(endpoint,true);if(!data||data.success===false)return [];
    return streamRows(apiPlayers(data,req),config.baseUrl||config.apiUrl,meta.title||(req.mediaType==="tv"?"Série":"Film"));
  }
  async function htmlRecovery(req,meta){
    var bases=[config.baseUrl],candidates=[];
    var slugs=[slug(meta.title),slug(meta.original)].filter(Boolean); if(meta.year)slugs=slugs.concat(slugs.map(function(s){return s+"-"+meta.year}));
    for(var i=0;i<config.directPaths.length;i++)for(var j=0;j<slugs.length;j++)candidates.push(absolute(config.directPaths[i].replace(/\{slug\}/g,slugs[j]).replace(/\{id\}/g,req.tmdbId).replace(/\{year\}/g,String(meta.year||"")),config.baseUrl+"/"));
    for(var k=0;k<config.searchPaths.length;k++){
      var search=absolute(config.searchPaths[k].replace(/\{query\}/g,encodeURIComponent(meta.title)).replace(/\{slug\}/g,slug(meta.title)).replace(/\{id\}/g,req.tmdbId),config.baseUrl+"/");
      var page=await request(search,false);if(!page)continue;
      var episodic=episodePlayers(page,search,req);if(episodic.length)return streamRows(episodic,search,meta.title);
      var direct=req.mediaType==="tv"?[]:players(page,search);if(direct.length)return streamRows(direct,search,meta.title);
      episodeLinks(page,search,req).forEach(function(url){candidates.push(url)});
      links(page,search,meta).forEach(function(row){candidates.push(row.url)});
    }
    var unique=Array.from(new Set(candidates.filter(Boolean))).slice(0,12);
    for(var n=0;n<unique.length;n++){var detail=await request(unique[n],false);if(!detail)continue;var urls=episodePlayers(detail,unique[n],req);if(!urls.length&&req.mediaType!=="tv")urls=players(detail,unique[n]);if(urls.length)return streamRows(urls,unique[n],meta.title)}
    return [];
  }
  async function recover(req){if(config.types.indexOf(req.mediaType)<0)return [];var meta=await metadata(req);if(!meta.title&&config.strategy!=="api_discovery")return [];return config.strategy==="api_discovery"?apiDiscovery(req,meta):htmlRecovery(req,meta)}
  function filterNative(rows){if(!Array.isArray(rows))return rows;var seen=Object.create(null);return rows.filter(function(row){var u=clean(row&&row.url);if(!usable(u)||seen[u])return false;seen[u]=1;return true})}
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioVfRecovery)return false;
    var original=container[key];
    var wrapped=async function(){var req=argumentsOf(arguments),fallback=[];if(config.recoveryFirst){fallback=await recover(req);if(fallback.length)return fallback;if(config.skipNativeWhenUnresolved&&config.strategy==="api_discovery"&&!discoveredApiRoute)return []}var native=[],nativeError=null;try{native=filterNative(await original.apply(this,arguments))}catch(error){nativeError=error}if(Array.isArray(native)&&native.length)return native;if(!config.recoveryFirst){fallback=await recover(req);if(fallback.length)return fallback}if(nativeError)throw nativeError;return Array.isArray(native)?native:[]};
    wrapped.__nuvioVfRecovery=true;wrapped.__nuvioOriginal=original;container[key]=wrapped;return true;
  }
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER", serialized).replace("MARKER_PLACEHOLDER", marker)
    return text.rstrip() + "\n" + wrapper.lstrip()
