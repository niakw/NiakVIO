#!/usr/bin/env python3
"""Castle clean-v3 runtime adapter as one provider-owned Lego.

The legacy Castle bundle is knowledge-only. This adapter re-implements the
documented Castle API flow in clear source and owns exactly one
PROVIDER.CASTLE.* STARTFIX/CLOSEFIX rectangle.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.CASTLE.RUNTIME.V1"
MARKER = "NIAKVIO_CASTLE_RUNTIME_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://api.hlowb.com").rstrip("/"),
        "channel": str(cfg.get("channel") or "IndiaA"),
        "clientType": str(cfg.get("client_type") or "1"),
        "lang": str(cfg.get("lang") or "en-US"),
        "packageName": str(cfg.get("package_name") or "com.external.castle"),
        "appMarket": str(cfg.get("app_market") or "GuanWang"),
        "apkSignKey": str(
            cfg.get("apk_sign_key")
            or "ED0955EB04E67A1D9F3305B95454FED485261475"
        ),
        "androidVersion": str(cfg.get("android_version") or "13"),
        "keySuffix": str(cfg.get("key_suffix") or "T!BgJB"),
        "resolution": max(1, min(int(cfg.get("resolution") or 2), 3)),
    }
    if not payload["base"].startswith(("http://", "https://")):
        raise ValueError("castle runtime base must be http(s)")
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    wrapper = r'''
/* NIAKVIO_CASTLE_RUNTIME_V1 */
;(function(g,c){
  "use strict";

  function s(v){return String(v==null?"":v).trim()}
  function rows(v){return Array.isArray(v)?v:[]}
  function dataBlock(v){
    if(v&&typeof v==="object"&&v.data&&typeof v.data==="object")return v.data;
    return v&&typeof v==="object"?v:{};
  }
  function normalized(v){
    var x=s(v);
    try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}
    return x.toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  }
  function contextMeta(args){
    var ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null;
    var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||null;
    if(md&&md.state==="ok"&&md.metadata)md=md.metadata;
    if(!md||typeof md!=="object")return null;
    var title=s(md.title||md.name||md.original_title||md.original_name);
    if(!title)return null;
    var date=s(md.release_date||md.first_air_date||md.year);
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    return {
      title:title,
      year:Number(date.slice(0,4))||0,
      tmdbId:s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||args[0]),
      type:type==="movie"?"movie":"tv",
      season:Number((obj&&obj.season)!=null?obj.season:args[2])||0,
      episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||0
    };
  }
  function apiHeaders(){
    return {
      "User-Agent":"okhttp/4.9.3",
      "Accept":"application/json",
      "Accept-Language":"en-US,en;q=0.9",
      "Connection":"Keep-Alive",
      "Referer":c.base
    };
  }
  function playbackHeaders(){
    return {
      "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
      "Accept":"video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
      "Accept-Language":"en-US,en;q=0.9",
      "Connection":"keep-alive",
      "DNT":"1"
    };
  }
  async function request(url,init){
    var opts=Object.assign({},init||{});
    opts.headers=Object.assign({},apiHeaders(),opts.headers||{});
    var response=await g.fetch(url,opts);
    if(!response||!response.ok)throw new Error("castle_http_"+String(response&&response.status||0));
    return response;
  }
  async function cipherText(response){
    var raw=s(await response.text());
    if(!raw)throw new Error("castle_empty_response");
    try{
      var parsed=JSON.parse(raw);
      if(parsed&&typeof parsed.data==="string"&&s(parsed.data))return s(parsed.data);
    }catch(_e){}
    return raw;
  }
  function utf8Bytes(value){
    if(typeof TextEncoder!=="undefined")return new TextEncoder().encode(String(value));
    var encoded=unescape(encodeURIComponent(String(value))),out=new Uint8Array(encoded.length);
    for(var i=0;i<encoded.length;i++)out[i]=encoded.charCodeAt(i)&255;
    return out;
  }
  function base64Bytes(value){
    var raw=atob(s(value)),out=new Uint8Array(raw.length);
    for(var i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i)&255;
    return out;
  }
  function keyBytes(secKey){
    var primary;
    try{primary=base64Bytes(secKey)}catch(_e){primary=utf8Bytes(s(secKey))}
    var suffix=utf8Bytes(c.keySuffix),out=new Uint8Array(16),offset=0;
    for(var i=0;i<primary.length&&offset<16;i++)out[offset++]=primary[i];
    for(var j=0;j<suffix.length&&offset<16;j++)out[offset++]=suffix[j];
    return out;
  }
  function bytesToText(value){
    var bytes;
    if(value instanceof Uint8Array)bytes=value;
    else if(typeof ArrayBuffer!=="undefined"&&value instanceof ArrayBuffer)bytes=new Uint8Array(value);
    else if(value&&value.buffer)bytes=new Uint8Array(value.buffer,value.byteOffset||0,value.byteLength||value.length||0);
    else bytes=new Uint8Array(0);
    if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8").decode(bytes);
    var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);
    try{return decodeURIComponent(escape(raw))}catch(_e){return raw}
  }
  function bytesHex(bytes){
    var out="";for(var i=0;i<bytes.length;i++)out+=bytes[i].toString(16).padStart(2,"0");
    return out;
  }
  function decrypt(cipher,secKey){
    var key=keyBytes(secKey),encrypted=base64Bytes(cipher);
    try{
      if(g&&typeof g.__crypto_aes_decrypt_raw==="function"){
        var plain=g.__crypto_aes_decrypt_raw(
          "AES-CBC",
          new Int8Array(key.buffer.slice(0)),
          new Int8Array(key.buffer.slice(0)),
          new Int8Array(encrypted.buffer.slice(0))
        );
        var nativeText=s(bytesToText(plain));
        if(nativeText)return nativeText;
      }
    }catch(_e){}
    if(typeof require!=="function")throw new Error("castle_crypto_unavailable");
    var CryptoJS=require("crypto-js");
    var keyWord=CryptoJS.enc.Hex.parse(bytesHex(key));
    var cipherWord=CryptoJS.enc.Base64.parse(s(cipher));
    var params=CryptoJS.lib.CipherParams.create({ciphertext:cipherWord});
    var plainWord=CryptoJS.AES.decrypt(params,keyWord,{
      iv:keyWord,
      mode:CryptoJS.mode.CBC,
      padding:CryptoJS.pad.Pkcs7
    });
    var decoded=s(plainWord.toString(CryptoJS.enc.Utf8));
    if(!decoded)throw new Error("castle_decrypt_empty");
    return decoded;
  }
  async function securityKey(){
    var q=new URLSearchParams({
      channel:c.channel,
      clientType:c.clientType,
      lang:c.lang
    });
    var response=await request(c.base+"/v0.1/system/getSecurityKey/1?"+q.toString());
    var value=await response.json();
    if(!value||Number(value.code)!==200||!value.data)throw new Error("castle_security_key");
    return s(value.data);
  }
  function safeJson(text){
    var value=String(text==null?"":text).replace(/([:{[,]\s*)(\d{16,})/g,'$1"$2"');
    return JSON.parse(value);
  }
  async function encryptedJson(url,secKey,init){
    var response=await request(url,init);
    return safeJson(decrypt(await cipherText(response),secKey));
  }
  async function search(secKey,keyword){
    var q=new URLSearchParams({
      channel:c.channel,
      clientType:c.clientType,
      keyword:s(keyword),
      lang:c.lang,
      mode:"1",
      packageName:c.packageName,
      page:"1",
      size:"30"
    });
    return await encryptedJson(
      c.base+"/film-api/v1.1.0/movie/searchByKeyword?"+q.toString(),
      secKey
    );
  }
  function strictMovieId(value,meta){
    var data=dataBlock(value),list=rows(data.rows||data.results||data.list);
    if(!list.length)return "";
    var target=normalized(meta.title),best=null,bestScore=0;
    for(var i=0;i<list.length;i++){
      var row=list[i]||{},candidate=normalized(row.title||row.name);
      if(!candidate)continue;
      var score=0;
      if(candidate===target)score=100;
      else if(candidate.length>=4&&target.length>=4&&(candidate.indexOf(target)>=0||target.indexOf(candidate)>=0)){
        var ratio=Math.min(candidate.length,target.length)/Math.max(candidate.length,target.length);
        if(ratio>=0.72)score=80+Math.round(ratio*10);
      }
      var expectedYear=Number(meta.year||0),rowYear=Number(row.year||row.releaseYear||row.release_year||0);
      if(expectedYear&&rowYear)score+=expectedYear===rowYear?10:-30;
      if(score>bestScore){bestScore=score;best=row}
    }
    if(!best||bestScore<80)return "";
    return s(best.id||best.redirectId||best.redirectIdStr);
  }
  async function details(secKey,movieId){
    var q=new URLSearchParams({
      channel:c.channel,
      clientType:c.clientType,
      lang:c.lang,
      movieId:s(movieId),
      packageName:c.packageName
    });
    return await encryptedJson(c.base+"/film-api/v1.9.9/movie?"+q.toString(),secKey);
  }
  async function video(secKey,movieId,episodeId,languageId){
    var q=new URLSearchParams({
      clientType:c.clientType,
      packageName:c.packageName,
      channel:c.channel,
      lang:c.lang
    });
    var body={
      mode:"1",
      appMarket:c.appMarket,
      clientType:c.clientType,
      woolUser:"false",
      apkSignKey:c.apkSignKey,
      androidVersion:c.androidVersion,
      movieId:s(movieId),
      episodeId:s(episodeId),
      isNewUser:"true",
      resolution:String(c.resolution),
      packageName:c.packageName
    };
    if(languageId!=null&&s(languageId))body.languageId=s(languageId);
    return await encryptedJson(
      c.base+"/film-api/v2.0.1/movie/getVideo2?"+q.toString(),
      secKey,
      {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(body)
      }
    );
  }
  function qualityValue(value){
    var raw=s(value).toLowerCase().replace(/^(sd|hd|fhd|uhd|4k)\s*/i,"").replace(/p$/,"");
    if(raw==="4k")return 2160;
    var n=parseInt(raw,10);return Number.isFinite(n)?n:0;
  }
  function outputRows(value,meta,label){
    var data=dataBlock(value),fallback=s(data.videoUrl);
    if(!fallback)return [];
    var subtitles=rows(data.subtitles).filter(function(x){return x&&x.url}).map(function(x){
      return {
        url:s(x.url),
        language:s(x.abbreviate||""),
        name:s(x.title||x.abbreviate||""),
        headers:playbackHeaders()
      };
    });
    var videos=rows(data.videos),out=[];
    if(videos.length){
      for(var i=0;i<videos.length;i++){
        var row=videos[i]||{},url=s(row.url||fallback);if(!url)continue;
        var quality=s(row.resolutionDescription||row.resolution||String(c.resolution));
        quality=quality.replace(/^(SD|HD|FHD)\s+/i,"");
        out.push({
          name:"Castle "+label+" - "+quality,
          title:meta.title+(meta.type==="tv"&&meta.season&&meta.episode?" S"+String(meta.season).padStart(2,"0")+"E"+String(meta.episode).padStart(2,"0"):(meta.year?" ("+meta.year+")":"")),
          url:url,
          quality:quality,
          headers:playbackHeaders(),
          provider:"castle",
          subtitles:subtitles
        });
      }
    }else{
      out.push({
        name:"Castle "+label,
        title:meta.title,
        url:fallback,
        quality:String(c.resolution===3?"1080p":c.resolution===1?"480p":"720p"),
        headers:playbackHeaders(),
        provider:"castle",
        subtitles:subtitles
      });
    }
    return out;
  }
  async function castleStreams(args){
    var meta=contextMeta(args);if(!meta)return [];
    var sec=await securityKey();
    var found=await search(sec,meta.year?meta.title+" "+meta.year:meta.title);
    var movieId=strictMovieId(found,meta);if(!movieId)return [];
    var detail=await details(sec,movieId),activeMovieId=movieId;
    if(meta.type==="tv"&&meta.season&&meta.episode){
      var root=dataBlock(detail),season=rows(root.seasons).find(function(x){return Number(x&&x.number)===meta.season});
      if(season&&season.movieId&&s(season.movieId)!==movieId){
        activeMovieId=s(season.movieId);
        detail=await details(sec,activeMovieId);
      }
    }
    var data=dataBlock(detail),episodes=rows(data.episodes),episodeRow=null;
    if(meta.type==="tv"&&meta.episode){
      episodeRow=episodes.find(function(x){return Number(x&&x.number)===meta.episode})||null;
    }else{
      episodeRow=episodes.length?episodes[0]:null;
    }
    var episodeId=s(episodeRow&&episodeRow.id);if(!episodeId)return [];
    var tracks=rows(episodeRow&&episodeRow.tracks),streams=[];
    for(var i=0;i<tracks.length;i++){
      var track=tracks[i]||{};
      if(!track.existIndividualVideo||!track.languageId)continue;
      try{
        var label="["+s(track.languageName||track.abbreviate||"Unknown")+"]";
        streams.push.apply(streams,outputRows(
          await video(sec,activeMovieId,episodeId,track.languageId),
          meta,
          label
        ));
      }catch(_e){}
    }
    if(!streams.length){
      try{
        streams.push.apply(streams,outputRows(
          await video(sec,activeMovieId,episodeId,null),
          meta,
          "[Shared]"
        ));
      }catch(_e){}
    }
    streams.sort(function(a,b){return qualityValue(b.quality)-qualityValue(a.quality)});
    return streams;
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioCastleRuntimeV1)return false;
    var wrapped=async function(){
      try{return await castleStreams(arguments)}catch(_e){return []}
    };
    wrapped.__niakvioCastleRuntimeV1=true;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER", serialized)
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "identity": "strict-title-year",
            "tmdbSource": "core-context-only",
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
