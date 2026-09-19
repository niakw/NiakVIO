#!/usr/bin/env python3
"""Shared clean-v3 Wings/speedracelight runtime renderer.

This module is build-time Python only. Provider bundles receive clear NiakVIO
JavaScript implementing the shared seed -> deterministic keystream -> XOR ->
'mvm1' JSON contract. Historical provider JavaScript is never embedded or
executed.
"""
from __future__ import annotations

import json
from typing import Any

WINGS_WRAPPER = r'''
/* CONFIG_MARKER */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  var K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174];
  var GOLD=0x9e3779b9,MAGIC=[0x6d,0x76,0x6d,0x31];
  function fmix(x){x=x>>>0;x^=x>>>16;x=Math.imul(x,0x85ebca6b)>>>0;x^=x>>>13;x=Math.imul(x,0xc2b2ae35)>>>0;x^=x>>>16;return x>>>0}
  function rot(x,n){x=x>>>0;n&=31;return n===0?x:((x<<n)|(x>>>(32-n)))>>>0}
  function fnv(text){var h=0x811c9dc5,t=s(text);for(var i=0;i<t.length;i++)h=Math.imul(h^t.charCodeAt(i),0x1000193)>>>0;return fmix(h)}
  function state(seed,id){
    var slots=new Array(61),acc=fmix(fnv(seed)^fmix((id>>>0)^GOLD))>>>0;
    for(var i=0;i<8;i++){
      var idx=acc%61;
      acc=rot((acc+GOLD)>>>0,7+(i&7));
      slots[idx]=(acc^fmix(acc))>>>0;
      acc=fmix((acc+idx)>>>0);
    }
    return {S:slots,acc:fmix(acc^0xa5a5a5a5)>>>0};
  }
  function word(st,n){
    var slots=st.S,acc=st.acc,idx=acc%61,exists=(idx in slots),mask=exists?-1:0,slot=(slots[idx]>>>0),mix=Math.imul(GOLD,n+1)>>>0;
    var v=(((acc^((slot^mix)>>>0))>>>0)|((acc&((slot^mix)>>>0)&mask)>>>0))>>>0;
    v=(rot((v+acc)>>>0,idx&31)^rot(acc,Math.imul(idx,7)&31))>>>0;
    acc=fmix((v+GOLD)>>>0);slots[idx]=acc;st.acc=acc;return acc>>>0;
  }
  function stream(seed,id,len){
    var st=state(seed,id),out=new Uint8Array(len),p=0,n=0;
    while(p<len){var w=word(st,n++);out[p++]=w&255;if(p<len)out[p++]=(w>>>8)&255;if(p<len)out[p++]=(w>>>16)&255;if(p<len)out[p++]=(w>>>24)&255}
    return out;
  }
  function b64url(input){
    var text=s(input).replace(/-/g,"+").replace(/_/g,"/").replace(/=+$/,""),raw="";
    try{if(typeof atob==="function")raw=atob(text+"===".slice((text.length+3)%4))}catch(_e){raw=""}
    if(!raw){
      var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",bytes=[],acc=0,bits=0;
      for(var i=0;i<text.length;i++){var v=chars.indexOf(text.charAt(i));if(v<0)continue;acc=(acc<<6)|v;bits+=6;if(bits>=8){bits-=8;bytes.push((acc>>>bits)&255)}}
      return new Uint8Array(bytes);
    }
    var out=new Uint8Array(raw.length);for(var j=0;j<raw.length;j++)out[j]=raw.charCodeAt(j)&255;return out;
  }
  function utf8(bytes){
    try{if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8",{fatal:true}).decode(bytes)}catch(_e){}
    var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);
    try{return decodeURIComponent(escape(raw))}catch(_e){return raw}
  }
  function decrypt(payload,seed,id){
    var enc=b64url(payload),ks=stream(seed,Number(id)||0,enc.length),plain=new Uint8Array(enc.length);
    for(var i=0;i<enc.length;i++)plain[i]=enc[i]^ks[i];
    if(plain.length<MAGIC.length)return null;
    for(var j=0;j<MAGIC.length;j++)if(plain[j]!==MAGIC[j])return null;
    try{return JSON.parse(utf8(plain.slice(MAGIC.length)))}catch(_e){return null}
  }
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};
    try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||null;
    if(md&&md.state==="ok"&&md.metadata)md=md.metadata;
    md=md&&typeof md==="object"?md:{};
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    var date=s(md.release_date||md.first_air_date||md.year),external=md.external_ids&&typeof md.external_ids==="object"?md.external_ids:{};
    return {
      id:s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0],
      type:type==="movie"?"movie":"tv",
      season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,
      episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1,
      title:s(md.title||md.name||md.original_title||md.original_name),
      year:date.slice(0,4),
      imdbId:s(md.imdb_id||external.imdb_id||"")
    };
  }
  function headers(){return {"User-Agent":c.userAgent,"Accept":"*/*","Origin":c.origin,"Referer":c.referer,"Cache-Control":"no-cache, no-store, must-revalidate","Pragma":"no-cache"}}
  function query(q,seed){
    var values={title:q.title,mediaType:q.type,year:q.year||"",episodeId:String(q.type==="tv"?q.episode:1),seasonId:String(q.type==="tv"?q.season:1),tmdbId:String(q.id),imdbId:q.imdbId||"",enc:"2",seed:seed};
    return Object.keys(values).map(function(k){return encodeURIComponent(k)+"="+encodeURIComponent(values[k])}).join("&");
  }
  function sources(data){
    if(!data||typeof data!=="object")return [];
    if(Array.isArray(data.sources))return data.sources;
    if(Array.isArray(data.streams))return data.streams;
    return [];
  }
  function subtitles(data){
    var rows=data&&Array.isArray(data.subtitles)?data.subtitles:[],out=[];
    for(var i=0;i<rows.length;i++){var r=rows[i]||{},url=s(r.url||r.file);if(!url)continue;out.push({url:url,lang:s(r.lang||r.language||r.label||"Unknown")})}
    return out;
  }
  function format(data,label,q){
    var rows=sources(data),subs=subtitles(data),out=[],seen=Object.create(null);
    for(var i=0;i<rows.length;i++){
      var row=rows[i]||{},url=s(row.url||row.file||row.src||row.link);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;
      out.push({name:c.providerName+" ["+label+"]",title:q.title+(q.type==="tv"?" S"+q.season+"E"+q.episode:(q.year?" ("+q.year+")":"")),url:url,quality:s(row.quality||row.label||"Auto"),language:s(row.language||row.lang||""),headers:headers(),subtitles:subs,provider:c.providerId});
    }
    return out;
  }
  async function resolve(args){
    var q=requestArgs(args);if(!/^\d+$/.test(q.id)||!q.title)return [];if(q.type==="tv"&&(!q.season||!q.episode))return [];
    try{
      var seedResponse=await g.fetch(c.apiBase+"/seed?mediaId="+encodeURIComponent(q.id),{headers:headers(),redirect:"follow"});
      if(!seedResponse||!seedResponse.ok)return [];
      var seedJson=await seedResponse.json(),seed=s(seedJson&&seedJson.seed);if(!seed)return [];
      var jobs=c.endpoints.map(async function(ep){
        var url=c.apiBase+"/"+s(ep.path).replace(/^\/+/, "")+"?"+query(q,seed);
        try{
          var r=await g.fetch(url,{headers:headers(),redirect:"follow"});if(!r||!r.ok)return [];
          var encrypted=await r.text();if(!s(encrypted))return [];
          var data=decrypt(encrypted,seed,Number(q.id));if(!data)return [];
          return format(data,s(ep.label||ep.path),q);
        }catch(_e){return []}
      });
      var all=await Promise.all(jobs),out=[],seen=Object.create(null);
      for(var i=0;i<all.length;i++)for(var j=0;j<all[i].length;j++){var row=all[i][j];if(!seen[row.url]){seen[row.url]=1;out.push(row)}}
      return out.slice(0,40);
    }catch(_e){return []}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key][c.installMarker])return false;
    var wrapped=async function(){return await resolve(arguments)};wrapped[c.installMarker]=true;container[key]=wrapped;return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def render_wings_runtime(*, marker: str, config: dict[str, Any]) -> str:
    payload = {
        "apiBase": str(config["apiBase"]).rstrip("/"),
        "origin": str(config["origin"]).rstrip("/"),
        "referer": str(config["referer"]),
        "userAgent": str(config["userAgent"]),
        "providerId": str(config["providerId"]),
        "providerName": str(config["providerName"]),
        "installMarker": str(config["installMarker"]),
        "endpoints": [
            {"label": str(row["label"]), "path": str(row["path"]).lstrip("/")}
            for row in config.get("endpoints") or []
        ],
    }
    if not payload["apiBase"].startswith(("http://", "https://")):
        raise ValueError("Wings apiBase must be http(s)")
    if not payload["endpoints"]:
        raise ValueError("Wings endpoints required")
    return (
        WINGS_WRAPPER.replace("CONFIG_MARKER", marker)
        .replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    )
