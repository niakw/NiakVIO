#!/usr/bin/env python3
"""CineVibe clean-v3 API runtime adapter.

The historical CineVibe bundle is knowledge-only. This Lego re-implements the
documented tokenized API call in clear source, consumes Core-provided TMDB
metadata, and owns exactly one PROVIDER.CINEVIBE.* STARTFIX/CLOSEFIX rectangle.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.CINEVIBE.RUNTIME.V1"
MARKER = "NIAKVIO_CINEVIBE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_CINEVIBE_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function b64(value){
    var text=s(value);
    try{if(typeof btoa==="function")return btoa(unescape(encodeURIComponent(text)))}catch(_e){}
    var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    var bytes=[];
    for(var i=0;i<text.length;i++){var code=text.charCodeAt(i);if(code<128)bytes.push(code);else return ""}
    var out="";
    for(var p=0;p<bytes.length;p+=3){
      var a=bytes[p],b=p+1<bytes.length?bytes[p+1]:0,d=p+2<bytes.length?bytes[p+2]:0;
      var n=(a<<16)|(b<<8)|d;
      out+=chars[(n>>18)&63]+chars[(n>>12)&63]+(p+1<bytes.length?chars[(n>>6)&63]:"=")+(p+2<bytes.length?chars[n&63]:"=");
    }
    return out;
  }
  function rot13(v){return s(v).replace(/[A-Za-z]/g,function(ch){var x=ch.charCodeAt(0),b=x<=90?65:97;return String.fromCharCode(((x-b+13)%26)+b)})}
  function encodeToken(v){
    var x=b64(v); if(!x)return "";
    x=x.split("").reverse().join("");
    x=rot13(x);
    x=b64(x);
    return x.replace(/\+/g,"-").replace(/\//g,"_").replace(/=/g,"");
  }
  function fnv1a32(v){
    var h=2166136261>>>0,txt=s(v);
    for(var i=0;i<txt.length;i++){
      h^=txt.charCodeAt(i);
      h=(h+(h<<1)+(h<<4)+(h<<7)+(h<<8)+(h<<24))>>>0;
    }
    return ("00000000"+h.toString(16)).slice(-8);
  }
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null;
    var ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||null;
    if(md&&md.state==="ok"&&md.metadata)md=md.metadata;
    md=md&&typeof md==="object"?md:{};
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0];
    var title=s(md.title||md.name||md.original_title||md.original_name);
    var date=s(md.release_date||md.first_air_date||md.year);
    return {tmdbId:id,type:type==="movie"?"movie":"tv",title:title,year:date.slice(0,4)};
  }
  function headers(){
    return {
      "Referer":c.base+"/",
      "User-Agent":c.userAgent,
      "X-CV-Fingerprint":c.fingerprint,
      "X-CV-Session":c.session,
      "X-Requested-With":"XMLHttpRequest",
      "Accept":"application/json,text/plain,*/*"
    };
  }
  function token(q){
    var clean=q.title.toLowerCase().replace(/[^a-z0-9]/g,"");
    var five=Math.floor(Date.now()/300000);
    var hashed=fnv1a32(String(five)+"_"+c.fingerprint+"_cinevibe_2025");
    var ten=Math.floor(Date.now()/1000/600);
    return encodeToken(c.session+"|"+q.tmdbId+"|"+clean+"|"+q.year+"||"+hashed+"|"+ten+"|"+c.fingerprint);
  }
  async function resolve(args){
    var q=requestArgs(args);
    if(q.type!=="movie"||!/^\d+$/.test(q.tmdbId)||!q.title||!/^\d{4}$/.test(q.year))return [];
    var t=token(q);if(!t)return [];
    var url=c.base+"/api/stream/fetch?server=cinebox-1&type=movie&mediaId="+encodeURIComponent(q.tmdbId)
      +"&title="+encodeURIComponent(q.title)+"&releaseYear="+encodeURIComponent(q.year)
      +"&_token="+encodeURIComponent(t)+"&_ts="+Date.now();
    try{
      var response=await g.fetch(url,{method:"GET",headers:headers(),redirect:"follow"});
      if(!response||!response.ok)return [];
      var data=await response.json();
      var rows=data&&Array.isArray(data.sources)?data.sources:[];
      var seen=Object.create(null),out=[];
      for(var i=0;i<rows.length;i++){
        var row=rows[i]||{},media=s(row.url||row.src||row.file||row.streamUrl);
        if(!/^https?:\/\//i.test(media)||seen[media])continue;
        seen[media]=1;
        var quality=s(row.label||row.quality||"Auto");
        out.push({name:"CineVibe - "+quality,title:q.title+" ("+q.year+")",url:media,quality:quality,headers:headers(),provider:"cinevibe"});
      }
      return out.slice(0,20);
    }catch(_e){return []}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioCineVibeRuntimeV1)return false;
    var wrapped=async function(){return await resolve(arguments)};
    wrapped.__niakvioCineVibeRuntimeV1=true;container[key]=wrapped;return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://cinevibe.asia").rstrip("/"),
        "fingerprint": str(cfg.get("fingerprint") or "eyJzY3JlZW4iOiIzNjB4ODA2eDI0Iiwi"),
        "session": str(cfg.get("session") or "pjght152dw2rb.ssst4bzleDI0Iiwibv78"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"),
    }
    if not payload["base"].startswith(("http://", "https://")):
        raise ValueError("cinevibe runtime base must be http(s)")
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={"runtime": payload, "identity": "core-tmdb-title-year", "legacyExecutableSeed": False},
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
