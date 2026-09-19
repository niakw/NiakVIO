#!/usr/bin/env python3
"""Peachify clean-v3 encrypted multi-server runtime adapter.

Only statically recovered endpoint/key DATA is retained. The historical
node-forge bundle is not embedded or executed; AES-256-GCM is implemented as a
small deterministic pure-JS primitive suitable for native provider runtimes.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.PEACHIFY.RUNTIME.V1"
MARKER = "NIAKVIO_PEACHIFY_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_PEACHIFY_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  var SBOX=[99,124,119,123,242,107,111,197,48,1,103,43,254,215,171,118,202,130,201,125,250,89,71,240,173,212,162,175,156,164,114,192,183,253,147,38,54,63,247,204,52,165,229,241,113,216,49,21,4,199,35,195,24,150,5,154,7,18,128,226,235,39,178,117,9,131,44,26,27,110,90,160,82,59,214,179,41,227,47,132,83,209,0,237,32,252,177,91,106,203,190,57,74,76,88,207,208,239,170,251,67,77,51,133,69,249,2,127,80,60,159,168,81,163,64,143,146,157,56,245,188,182,218,33,16,255,243,210,205,12,19,236,95,151,68,23,196,167,126,61,100,93,25,115,96,129,79,220,34,42,144,136,70,238,184,20,222,94,11,219,224,50,58,10,73,6,36,92,194,211,172,98,145,149,228,121,231,200,55,109,141,213,78,169,108,86,244,234,101,122,174,8,186,120,37,46,28,166,180,198,232,221,116,31,75,189,139,138,112,62,181,102,72,3,246,14,97,53,87,185,134,193,29,158,225,248,152,17,105,217,142,148,155,30,135,233,206,85,40,223,140,161,137,13,191,230,66,104,65,153,45,15,176,84,187,22];
  function hex(v){var out=[];for(var i=0;i<v.length;i+=2)out.push(parseInt(v.slice(i,i+2),16));return new Uint8Array(out)}
  function b64url(v){
    var x=s(v).replace(/-/g,"+").replace(/_/g,"/");while(x.length%4)x+="=";
    var raw="";try{raw=typeof atob==="function"?atob(x):""}catch(_e){raw=""}
    if(!raw)return new Uint8Array(0);
    var out=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i)&255;return out;
  }
  function cat(a,b){var o=new Uint8Array(a.length+b.length);o.set(a,0);o.set(b,a.length);return o}
  function xtime(a){return ((a<<1)^((a&128)?0x11b:0))&255}
  function expand(key){
    var w=new Uint8Array(240);w.set(key);var n=32,rcon=1,t=[0,0,0,0];
    while(n<240){
      for(var i=0;i<4;i++)t[i]=w[n-4+i];
      if(n%32===0){
        var z=t[0];t[0]=SBOX[t[1]]^rcon;t[1]=SBOX[t[2]];t[2]=SBOX[t[3]];t[3]=SBOX[z];rcon=xtime(rcon);
      }else if(n%32===16){for(var j=0;j<4;j++)t[j]=SBOX[t[j]]}
      for(var k=0;k<4;k++){w[n]=w[n-32]^t[k];n++}
    }
    return w;
  }
  function addKey(st,w,round){var o=round*16;for(var i=0;i<16;i++)st[i]^=w[o+i]}
  function sub(st){for(var i=0;i<16;i++)st[i]=SBOX[st[i]]}
  function shift(st){
    var t=new Uint8Array(st);
    for(var r=0;r<4;r++)for(var col=0;col<4;col++)st[4*col+r]=t[4*((col+r)%4)+r];
  }
  function mix(st){
    for(var c0=0;c0<4;c0++){
      var i=4*c0,a=st[i],b=st[i+1],d=st[i+2],e=st[i+3],x=a^b^d^e;
      st[i]=a^x^xtime(a^b);st[i+1]=b^x^xtime(b^d);st[i+2]=d^x^xtime(d^e);st[i+3]=e^x^xtime(e^a);
    }
  }
  function aes(block,w){
    var st=new Uint8Array(block);addKey(st,w,0);
    for(var r=1;r<14;r++){sub(st);shift(st);mix(st);addKey(st,w,r)}
    sub(st);shift(st);addKey(st,w,14);return st;
  }
  function xor(a,b){var o=new Uint8Array(a.length);for(var i=0;i<a.length;i++)o[i]=a[i]^b[i];return o}
  function gfMul(x,y){
    var z=new Uint8Array(16),v=new Uint8Array(y);
    for(var i=0;i<128;i++){
      if((x[Math.floor(i/8)]>>(7-(i%8)))&1)for(var j=0;j<16;j++)z[j]^=v[j];
      var lsb=v[15]&1;
      for(var k=15;k>=0;k--)v[k]=(v[k]>>>1)|(k?v[k-1]<<7:0);
      if(lsb)v[0]^=0xe1;
    }
    return z;
  }
  function u64bits(n){
    var o=new Uint8Array(8),bits=n*8;
    for(var i=7;i>=0;i--){o[i]=bits&255;bits=Math.floor(bits/256)}
    return o;
  }
  function ghash(h,data){
    var y=new Uint8Array(16);
    for(var off=0;off<data.length;off+=16){var b=new Uint8Array(16);b.set(data.slice(off,off+16));y=gfMul(xor(y,b),h)}
    return y;
  }
  function j0(h,iv){
    if(iv.length===12){var j=new Uint8Array(16);j.set(iv);j[15]=1;return j}
    var rem=iv.length%16,pad=rem?16-rem:0,buf=new Uint8Array(iv.length+pad+16);buf.set(iv);buf.set(u64bits(iv.length),buf.length-8);return ghash(h,buf);
  }
  function inc32(v){
    var o=new Uint8Array(v);
    for(var i=15;i>=12;i--){o[i]=(o[i]+1)&255;if(o[i]!==0)break}
    return o;
  }
  function equal(a,b){if(a.length!==b.length)return false;var d=0;for(var i=0;i<a.length;i++)d|=a[i]^b[i];return d===0}
  function utf8(bytes){
    try{if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8",{fatal:true}).decode(bytes)}catch(_e){}
    var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);
    try{return decodeURIComponent(escape(raw))}catch(_e){return raw}
  }
  function decryptToken(token){
    var parts=s(token).split(".");if(parts.length<3)return null;
    var iv=b64url(parts[0]),joined=cat(b64url(parts[1]),b64url(parts[2]));if(iv.length<8||joined.length<=16)return null;
    var ct=joined.slice(0,joined.length-16),tag=joined.slice(joined.length-16),w=expand(hex(c.keyHex));
    var h=aes(new Uint8Array(16),w),j=j0(h,iv),ctr=new Uint8Array(j),plain=new Uint8Array(ct.length);
    for(var off=0;off<ct.length;off+=16){ctr=inc32(ctr);var ks=aes(ctr,w);for(var n=0;n<Math.min(16,ct.length-off);n++)plain[off+n]=ct[off+n]^ks[n]}
    var pad=ct.length%16?16-(ct.length%16):0,lenBlock=new Uint8Array(16);lenBlock.set(u64bits(0),0);lenBlock.set(u64bits(ct.length),8);
    var auth=new Uint8Array(ct.length+pad+16);auth.set(ct);auth.set(lenBlock,ct.length+pad);
    var expected=xor(aes(j,w),ghash(h,auth));
    if(!equal(expected.slice(0,16),tag))return null;
    try{return JSON.parse(utf8(plain))}catch(_e){return null}
  }
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null;
    var ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    return {
      id:s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0],
      type:type==="movie"?"movie":"tv",
      season:Number((obj&&obj.season)!=null?obj.season:args[2])||0,
      episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||0
    };
  }
  function headers(){return {"User-Agent":c.userAgent,"Origin":c.origin,"Referer":c.referer,"Accept":"application/json,text/plain,*/*"}}
  function sourceUrl(row){return s(row&&(row.url||row.src||row.file||row.stream||row.streamUrl))}
  async function one(server,q){
    var url=server.base.replace(/\/+$/,"")+"/"+server.path+"/"+q.type+"/"+encodeURIComponent(q.id);
    if(q.type==="tv")url+="/"+encodeURIComponent(String(q.season))+"/"+encodeURIComponent(String(q.episode));
    try{
      var response=await g.fetch(url,{headers:headers(),redirect:"follow"});if(!response||!response.ok)return [];
      var data=await response.json();if(!data||data.isEncrypted===false||!data.data)return [];
      var plain=decryptToken(data.data);if(!plain||!Array.isArray(plain.sources))return [];
      var out=[],seen=Object.create(null);
      for(var i=0;i<plain.sources.length;i++){
        var row=plain.sources[i]||{},media=sourceUrl(row);if(!/^https?:\/\//i.test(media)||seen[media])continue;
        seen[media]=1;out.push({
          name:"Peachify | "+server.label,
          title:"Peachify | "+server.label,
          url:media,
          quality:s(row.quality||row.label||"HD"),
          language:s(row.dub||row.audio||row.language||row.name||"Original"),
          headers:Object.assign({},headers(),row.headers||{}),
          provider:"peachify"
        });
      }
      return out;
    }catch(_e){return []}
  }
  async function resolve(args){
    var q=requestArgs(args);if(!/^\d+$/.test(q.id))return [];
    if(q.type==="tv"&&(!q.season||!q.episode))return [];
    var rows=await Promise.all(c.servers.map(function(server){return one(server,q)})),out=[],seen=Object.create(null);
    for(var i=0;i<rows.length;i++)for(var j=0;j<rows[i].length;j++){var r=rows[i][j];if(!seen[r.url]){seen[r.url]=1;out.push(r)}}
    return out.slice(0,40);
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioPeachifyRuntimeV1)return false;
    var wrapped=async function(){return await resolve(arguments)};
    wrapped.__niakvioPeachifyRuntimeV1=true;container[key]=wrapped;return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "keyHex": str(
            cfg.get("key_hex")
            or "a8f2a1b5e9c470814f6b2c3a5d8e7f9c1a2b3c4d5e3f7a8b8cad1e2d0a4d5c5d"
        ),
        "origin": str(cfg.get("origin") or "https://peachify.top"),
        "referer": str(cfg.get("referer") or "https://peachify.top/"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36"
        ),
        "servers": cfg.get("servers")
        or [
            {"label": "Iron", "base": "https://uwu.eat-peach.sbs", "path": "moviebox"},
            {"label": "Wolf", "base": "https://usa.eat-peach.sbs", "path": "air"},
            {"label": "Spider", "base": "https://usa.eat-peach.sbs", "path": "holly"},
            {"label": "Multi", "base": "https://usa.eat-peach.sbs", "path": "multi"},
            {"label": "Dark", "base": "https://uwu.eat-peach.sbs", "path": "net"},
        ],
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
            "crypto": "pure-js-aes-256-gcm",
            "identity": "tmdb-direct",
            "legacyExecutableSeed": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
