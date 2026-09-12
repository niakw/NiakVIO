#!/usr/bin/env python3
"""VidRock clean-v3 runtime adapter.

The current VidRock contract is represented as NiakVIO-owned DATA/runtime logic:
- TMDB-direct movie/tv API on the current live base;
- server URLs are AES-256-GCM tokens containing a 12-byte IV, ciphertext and
  a 16-byte authentication tag, encoded as base64url;
- decrypted outputs are accepted only when they are HTTP(S) HLS manifests.

Historical/upstream JavaScript is knowledge-only and is not embedded or executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDROCK.RUNTIME.V1"
MARKER = "NIAKVIO_VIDROCK_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VIDROCK_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  var SBOX=[99,124,119,123,242,107,111,197,48,1,103,43,254,215,171,118,202,130,201,125,250,89,71,240,173,212,162,175,156,164,114,192,183,253,147,38,54,63,247,204,52,165,229,241,113,216,49,21,4,199,35,195,24,150,5,154,7,18,128,226,235,39,178,117,9,131,44,26,27,110,90,160,82,59,214,179,41,227,47,132,83,209,0,237,32,252,177,91,106,203,190,57,74,76,88,207,208,239,170,251,67,77,51,133,69,249,2,127,80,60,159,168,81,163,64,143,146,157,56,245,188,182,218,33,16,255,243,210,205,12,19,236,95,151,68,23,196,167,126,61,100,93,25,115,96,129,79,220,34,42,144,136,70,238,184,20,222,94,11,219,224,50,58,10,73,6,36,92,194,211,172,98,145,149,228,121,231,200,55,109,141,213,78,169,108,86,244,234,101,122,174,8,186,120,37,46,28,166,180,198,232,221,116,31,75,189,139,138,112,62,181,102,72,3,246,14,97,53,87,185,134,193,29,158,225,248,152,17,105,217,142,148,155,30,135,233,206,85,40,223,140,161,137,13,191,230,66,104,65,153,45,15,176,84,187,22];
  function hex(v){var out=[];for(var i=0;i<v.length;i+=2)out.push(parseInt(v.slice(i,i+2),16));return new Uint8Array(out)}
  function b64url(v){
    var x=s(v).replace(/-/g,"+").replace(/_/g,"/");while(x.length%4)x+="=";
    if(typeof atob==="function"){
      try{var raw=atob(x),o=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)o[i]=raw.charCodeAt(i)&255;return o}catch(_e){}
    }
    var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",clean=x.replace(/=+$/g,""),bytes=[],acc=0,bits=0;
    for(var j=0;j<clean.length;j++){
      var n=chars.indexOf(clean.charAt(j));if(n<0)return new Uint8Array(0);acc=(acc<<6)|n;bits+=6;
      if(bits>=8){bits-=8;bytes.push((acc>>bits)&255)}
    }
    return new Uint8Array(bytes);
  }
  function xtime(a){return ((a<<1)^((a&128)?0x11b:0))&255}
  function expand(key){
    var w=new Uint8Array(240);w.set(key);var n=32,rcon=1,t=[0,0,0,0];
    while(n<240){
      for(var i=0;i<4;i++)t[i]=w[n-4+i];
      if(n%32===0){var z=t[0];t[0]=SBOX[t[1]]^rcon;t[1]=SBOX[t[2]];t[2]=SBOX[t[3]];t[3]=SBOX[z];rcon=xtime(rcon)}
      else if(n%32===16){for(var j=0;j<4;j++)t[j]=SBOX[t[j]]}
      for(var k=0;k<4;k++){w[n]=w[n-32]^t[k];n++}
    }
    return w;
  }
  function addKey(st,w,round){var o=round*16;for(var i=0;i<16;i++)st[i]^=w[o+i]}
  function sub(st){for(var i=0;i<16;i++)st[i]=SBOX[st[i]]}
  function shift(st){var t=new Uint8Array(st);for(var r=0;r<4;r++)for(var c0=0;c0<4;c0++)st[4*c0+r]=t[4*((c0+r)%4)+r]}
  function mix(st){
    for(var c0=0;c0<4;c0++){
      var i=4*c0,a=st[i],b=st[i+1],d=st[i+2],e=st[i+3],x=a^b^d^e;
      st[i]=a^x^xtime(a^b);st[i+1]=b^x^xtime(b^d);st[i+2]=d^x^xtime(d^e);st[i+3]=e^x^xtime(e^a);
    }
  }
  function aes(block,w){var st=new Uint8Array(block);addKey(st,w,0);for(var r=1;r<14;r++){sub(st);shift(st);mix(st);addKey(st,w,r)}sub(st);shift(st);addKey(st,w,14);return st}
  function xor(a,b){var o=new Uint8Array(a.length);for(var i=0;i<a.length;i++)o[i]=a[i]^b[i];return o}
  function gfMul(x,y){
    var z=new Uint8Array(16),v=new Uint8Array(y);
    for(var i=0;i<128;i++){
      if((x[Math.floor(i/8)]>>(7-(i%8)))&1)for(var j=0;j<16;j++)z[j]^=v[j];
      var lsb=v[15]&1;for(var k=15;k>=0;k--)v[k]=(v[k]>>>1)|(k?v[k-1]<<7:0);if(lsb)v[0]^=0xe1;
    }
    return z;
  }
  function u64bits(n){var o=new Uint8Array(8),bits=n*8;for(var i=7;i>=0;i--){o[i]=bits&255;bits=Math.floor(bits/256)}return o}
  function ghash(h,data){var y=new Uint8Array(16);for(var off=0;off<data.length;off+=16){var b=new Uint8Array(16);b.set(data.slice(off,off+16));y=gfMul(xor(y,b),h)}return y}
  function j0(iv){var j=new Uint8Array(16);j.set(iv.slice(0,12),0);j[15]=1;return j}
  function inc32(v){var o=new Uint8Array(v);for(var i=15;i>=12;i--){o[i]=(o[i]+1)&255;if(o[i]!==0)break}return o}
  function equal(a,b){if(a.length!==b.length)return false;var d=0;for(var i=0;i<a.length;i++)d|=a[i]^b[i];return d===0}
  function utf8(bytes){
    try{if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8",{fatal:true}).decode(bytes)}catch(_e){}
    var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);try{return decodeURIComponent(escape(raw))}catch(_e){return raw}
  }
  function decryptToken(token){
    var raw=b64url(token);if(raw.length<=28)return null;
    var iv=raw.slice(0,12),ct=raw.slice(12,raw.length-16),tag=raw.slice(raw.length-16),w=expand(hex(c.keyHex));
    var h=aes(new Uint8Array(16),w),j=j0(iv),ctr=new Uint8Array(j),plain=new Uint8Array(ct.length);
    for(var off=0;off<ct.length;off+=16){ctr=inc32(ctr);var ks=aes(ctr,w);for(var n=0;n<Math.min(16,ct.length-off);n++)plain[off+n]=ct[off+n]^ks[n]}
    var pad=ct.length%16?16-(ct.length%16):0,lenBlock=new Uint8Array(16);lenBlock.set(u64bits(0),0);lenBlock.set(u64bits(ct.length),8);
    var auth=new Uint8Array(ct.length+pad+16);auth.set(ct);auth.set(lenBlock,ct.length+pad);
    var expected=xor(aes(j,w),ghash(h,auth));if(!equal(expected.slice(0,16),tag))return null;
    var out=s(utf8(plain));return /^https?:\/\//i.test(out)?out:null;
  }
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var rawType=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"movie").toLowerCase();
    return {
      id:s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||first||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0],
      type:rawType==="movie"?"movie":"tv",
      season:Number((obj&&obj.season)!=null?obj.season:(args[2]!=null?args[2]:ctx.season))||0,
      episode:Number((obj&&obj.episode)!=null?obj.episode:(args[3]!=null?args[3]:ctx.episode))||0
    };
  }
  function headers(){return {"User-Agent":c.userAgent,"Origin":c.origin,"Referer":c.referer,"Accept":"application/json,text/plain,*/*"}}
  function qualityFromManifest(text){
    var best=0,re=/RESOLUTION=\d+x(\d+)/gi,m;while((m=re.exec(text||""))!==null){var h=parseInt(m[1],10)||0;if(h>best)best=h}return best?String(best)+"p":"HD";
  }
  async function resolve(args){
    var q=requestArgs(args);if(!/^\d+$/.test(q.id))return [];if(q.type==="tv"&&(!q.season||!q.episode))return [];
    var base=s(c.base).replace(/\/+$/,"");if(!/^https?:\/\//i.test(base))return [];
    var url=base+"/api/"+q.type+"/"+encodeURIComponent(q.id);if(q.type==="tv")url+="/"+q.season+"/"+q.episode;
    var response,data;try{response=await g.fetch(url,{headers:headers(),redirect:"follow"});if(!response||!response.ok)return [];data=await response.json()}catch(_e){return []}
    if(!data||typeof data!=="object"||Array.isArray(data))return [];
    var ordered=[],seenName=Object.create(null),preferred=q.type==="movie"&&Array.isArray(c.movieServerOrder)?c.movieServerOrder:(Array.isArray(c.serverOrder)?c.serverOrder:[]);
    for(var pi=0;pi<preferred.length;pi++){var pn=s(preferred[pi]);if(pn&&data[pn]&&!seenName[pn]){seenName[pn]=1;ordered.push(pn)}}
    /* NIAKVIO_VIDROCK_LUNA_ALL_LANES_EXCLUSION_V1 */
    Object.keys(data).forEach(function(name){if(!seenName[name]&&!(Array.isArray(c.excludedServers)&&c.excludedServers.indexOf(name)>=0)){seenName[name]=1;ordered.push(name)}});
    var out=[],seenUrl=Object.create(null);
    for(var i=0;i<ordered.length;i++){
      var name=ordered[i],row=data[name];if(Array.isArray(c.excludedServers)&&c.excludedServers.indexOf(name)>=0)continue;if(!row||typeof row!=="object")continue;
      var token=s(row.url);if(!token)continue;
      var media=decryptToken(token);if(!media||seenUrl[media])continue;
      var probe,text="";try{probe=await g.fetch(media,{headers:headers(),redirect:"follow"});if(!probe||!probe.ok)continue;text=await probe.text()}catch(_e){continue}
      if(!/^#EXTM3U/m.test(text))continue;
      seenUrl[media]=1;out.push({
        name:"VidRock | "+name,
        title:"VidRock | "+name,
        url:media,
        quality:qualityFromManifest(text),
        language:"Original",
        headers:headers(),
        provider:"vidrock"
      });
      if(out.length>=c.maxStreams)break;
    }
    return out;
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioVidrockRuntimeV1)return false;
    var wrapped=async function(){return await resolve(arguments)};wrapped.__niakvioVidrockRuntimeV1=true;container[key]=wrapped;return true;
  }
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    server_order = cfg.get("server_order") or ["Atlas", "Luna", "Orion", "Astra", "Nova"]
    excluded_all = cfg.get("excluded_servers") or ["Luna"]
    movie_excluded = cfg.get("movie_excluded_servers") or list(excluded_all)
    movie_order = cfg.get("movie_server_order") or [x for x in server_order if x not in movie_excluded and x not in excluded_all]
    payload = {
        "base": str(cfg.get("base") or "https://vidrock.ru"),
        "keyHex": str(
            cfg.get("key_hex")
            or "7f3e9c2a8b5d1f4e6a9c3b7d2e5f8a1c4b6d9e2f5a8c1b4d7e9f2a5c8b1d4e7f"
        ),
        "origin": str(cfg.get("origin") or "https://vidrock.net"),
        "referer": str(cfg.get("referer") or "https://vidrock.net/"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        ),
        "serverOrder": server_order,
        "movieServerOrder": movie_order,
        "movieExcludedServers": movie_excluded,
        "excludedServers": excluded_all,
        "maxStreams": int(cfg.get("max_streams") or 5),
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
            "crypto": "pure-js-aes-256-gcm-authenticated",
            "identity": "tmdb-direct",
            "api": "plain-tmdb-id",
            "movieServerEvidence": {"Luna": "excluded only on movie after repeat media_filename_title_mismatch; retained on tv"},
            "argumentAuthority": "explicit-getStreams-args-before-global-context",
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
