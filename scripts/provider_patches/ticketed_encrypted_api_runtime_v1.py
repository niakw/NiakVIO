#!/usr/bin/env python3
'''Reusable Provider Bloc for ticketed encrypted TMDB APIs.

The provider-specific DATA supplies endpoints, server ids and presentation labels.
This Bloc owns only the reusable transport sequence:

request identity -> optional ALTCHA SHA-256 challenge -> single-use ticket ->
server stream request -> optional external decrypt transform -> portable stream.

No ticket, challenge answer, encrypted payload or terminal media URL is persisted.
The JavaScript intentionally avoids WebAssembly and TextEncoder/TextDecoder so it
remains compatible with the current Nuvio TV PluginRuntime contract.
'''
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.GENERIC.TICKETED_ENCRYPTED.API.V1"
GENERIC_REUSABLE = True
MARKER = "NIAKVIO_TICKETED_ENCRYPTED_API_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_TICKETED_ENCRYPTED_API_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function S(v){return String(v==null?"":v).trim()}
function H(extra){var h={"User-Agent":c.userAgent,"Accept":"application/json,*/*","Origin":c.siteBase,"Referer":c.siteBase+"/"};if(extra&&typeof extra==="object")for(var k in extra)if(extra[k]!=null)h[k]=String(extra[k]);return h}
function Q(a){
  var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};
  try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=S((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||a[1]||"movie").toLowerCase();
  if(semantic==="series")semantic="tv";
  if(semantic!=="movie"&&semantic!=="tv"&&semantic!=="anime")return null;
  var id=S((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
  if(!/^\d+$/.test(id))return null;
  var season=Number((o&&(o.season||o.seasonNumber))||ctx.season||a[2]||0);
  var episode=Number((o&&(o.episode||o.episodeNumber))||ctx.episode||a[3]||0);
  var transport=semantic==="tv"||(semantic==="anime"&&season>0&&episode>0)?"tv":"movie";
  if(transport==="tv"&&(!season||!episode))return null;
  return{semanticType:semantic,transport:transport,id:id,season:season,episode:episode}
}
function path(t,q){return S(t).replace(/\{(?:id|tmdbId)\}/g,encodeURIComponent(q.id)).replace(/\{season\}/g,encodeURIComponent(q.season)).replace(/\{episode\}/g,encodeURIComponent(q.episode))}
function addQuery(url,key,value){if(!key)return url;return url+(url.indexOf("?")>=0?"&":"?")+encodeURIComponent(key)+"="+encodeURIComponent(value)}
async function J(url,opt){try{var r=await g.fetch(url,opt||{});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
function rr(x,n){return (x>>>n)|(x<<(32-n))}
function sha256(input){
  var s=unescape(encodeURIComponent(String(input))),bytes=[],i,j;
  for(i=0;i<s.length;i++)bytes.push(s.charCodeAt(i)&255);
  var bitHi=Math.floor((bytes.length*8)/4294967296),bitLo=(bytes.length*8)>>>0;
  bytes.push(128);while(bytes.length%64!==56)bytes.push(0);
  bytes.push((bitHi>>>24)&255,(bitHi>>>16)&255,(bitHi>>>8)&255,bitHi&255,(bitLo>>>24)&255,(bitLo>>>16)&255,(bitLo>>>8)&255,bitLo&255);
  var K=[1116352408,1899447441,3049323471,3921009573,961987163,1508970993,2453635748,2870763221,3624381080,310598401,607225278,1426881987,1925078388,2162078206,2614888103,3248222580,3835390401,4022224774,264347078,604807628,770255983,1249150122,1555081692,1996064986,2554220882,2821834349,2952996808,3210313671,3336571891,3584528711,113926993,338241895,666307205,773529912,1294757372,1396182291,1695183700,1986661051,2177026350,2456956037,2730485921,2820302411,3259730800,3345764771,3516065817,3600352804,4094571909,275423344,430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,1955562222,2024104815,2227730452,2361852424,2428436474,2756734187,3204031479,3329325298];
  var Hh=[1779033703,3144134277,1013904242,2773480762,1359893119,2600822924,528734635,1541459225],w=new Array(64);
  for(i=0;i<bytes.length;i+=64){
    for(j=0;j<16;j++)w[j]=((bytes[i+4*j]<<24)|(bytes[i+4*j+1]<<16)|(bytes[i+4*j+2]<<8)|bytes[i+4*j+3])>>>0;
    for(j=16;j<64;j++){var a0=w[j-15],a1=w[j-2],s0=(rr(a0,7)^rr(a0,18)^(a0>>>3))>>>0,s1=(rr(a1,17)^rr(a1,19)^(a1>>>10))>>>0;w[j]=(w[j-16]+s0+w[j-7]+s1)>>>0}
    var a=Hh[0],b=Hh[1],cc=Hh[2],d=Hh[3],e=Hh[4],f=Hh[5],gg=Hh[6],h=Hh[7];
    for(j=0;j<64;j++){var S1=(rr(e,6)^rr(e,11)^rr(e,25))>>>0,ch=((e&f)^((~e)&gg))>>>0,t1=(h+S1+ch+K[j]+w[j])>>>0,S0=(rr(a,2)^rr(a,13)^rr(a,22))>>>0,maj=((a&b)^(a&cc)^(b&cc))>>>0,t2=(S0+maj)>>>0;h=gg;gg=f;f=e;e=(d+t1)>>>0;d=cc;cc=b;b=a;a=(t1+t2)>>>0}
    Hh[0]=(Hh[0]+a)>>>0;Hh[1]=(Hh[1]+b)>>>0;Hh[2]=(Hh[2]+cc)>>>0;Hh[3]=(Hh[3]+d)>>>0;Hh[4]=(Hh[4]+e)>>>0;Hh[5]=(Hh[5]+f)>>>0;Hh[6]=(Hh[6]+gg)>>>0;Hh[7]=(Hh[7]+h)>>>0
  }
  var out="";for(i=0;i<Hh.length;i++)out+=("00000000"+Hh[i].toString(16)).slice(-8);return out
}
function b64(v){try{return btoa(unescape(encodeURIComponent(String(v))))}catch(_e){return""}}
function solve(ch){
  if(!ch||!ch.challenge||!ch.salt||!ch.signature)return"";
  var algo=S(ch.algorithm||"SHA-256").toUpperCase().replace(/_/g,"-");
  if(algo!=="SHA-256"&&algo!=="SHA256")return"";
  var declared=Number(ch.maxnumber!=null?ch.maxnumber:ch.maxNumber),limit=Math.min(isFinite(declared)&&declared>=0?declared:c.maxPow,c.maxPow);
  for(var n=0;n<=limit;n++)if(sha256(S(ch.salt)+String(n))===S(ch.challenge).toLowerCase())return b64(JSON.stringify({algorithm:ch.algorithm||"SHA-256",challenge:ch.challenge,number:n,salt:ch.salt,signature:ch.signature}));
  return""
}
async function ticket(){
  var body={},challenge="";
  if(c.challengePath){
    var ch=await J(c.apiBase+c.challengePath,{headers:H()});challenge=solve(ch);if(!challenge)return"";
    body[c.challengeBodyField]=challenge
  }
  var opt={method:c.ticketMethod,headers:H({"Content-Type":"application/json"})};
  if(c.challengePath||c.ticketBodyAlways)opt.body=JSON.stringify(body);
  var t=await J(c.apiBase+c.ticketPath,opt);return S(t&&t[c.ticketField])
}
function unwrap(v){if(v==null)return null;if(typeof v==="string"){try{return JSON.parse(v)}catch(_e){return null}}if(typeof v!=="object")return null;if(Number(v.status)===200&&v.result!=null)return unwrap(v.result)||v.result;if(v.result!=null)return unwrap(v.result)||v.result;if(v.data!=null&&Object.keys(v).length<=3)return unwrap(v.data)||v.data;return v}
async function decrypt(enc){
  if(!enc)return null;if(!c.decryptUrl)return unwrap(enc);
  var body={};body[c.decryptBodyField]=enc;
  var d=await J(c.decryptUrl,{method:"POST",headers:H({"Content-Type":"application/json"}),body:JSON.stringify(body)});
  return unwrap(d)
}
function ql(v){var x=S(v);var m=x.match(/\b(2160|1440|1080|720|480|360)p?\b/i);return m?m[1]+"p":/\b4k\b/i.test(x)?"2160p":"Auto"}
function lang(v,fallback){var x=S(v||fallback);return x||"Auto"}
function subRows(v){
  var rows=Array.isArray(v)?v:(v&&Array.isArray(v.subtitles)?v.subtitles:v&&Array.isArray(v.tracks)?v.tracks:[]),out=[],seen={};
  for(var i=0;i<rows.length&&out.length<c.maxSubtitles;i++){var r=rows[i]||{},u=S(r.url||r.file||r.src);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;var l=S(r.language||r.lang||r.label||r.srclang||"Unknown");out.push({url:u,language:l,name:S(r.name||r.label||l)})}
  return out
}
async function subtitles(q){
  var tpl=q.transport==="movie"?c.subtitleMoviePath:c.subtitleTvPath;if(!tpl)return[];
  var j=await J(c.apiBase+path(tpl,q),{headers:H()});return subRows(j)
}
function serverAllowed(s,q){if(s.movieOnly&&q.transport!=="movie")return false;if(s.tvOnly&&q.transport!=="tv")return false;if(s.animeOnly&&q.semanticType!=="anime")return false;return true}
async function one(q,srv,subs){
  var t=await ticket();if(!t)return null;
  var tpl=q.transport==="movie"?c.moviePath:c.tvPath,u=c.apiBase+path(tpl,q);u=addQuery(u,c.serverQueryKey,S(srv.id));
  var extra={};extra[c.ticketHeader]=t;
  var enc=await J(u,{headers:H(extra)});if(!enc)return null;
  var d=await decrypt(enc);if(!d||typeof d!=="object")return null;
  var url=S(d.url||d.file||d.src);if(!/^https?:\/\//i.test(url))return null;
  var ph=H(d.headers&&typeof d.headers==="object"?d.headers:{});delete ph[c.ticketHeader];
  var language=lang(d.language||d.lang,srv.language),quality=ql(d.quality||d.resolution||url),label=S(srv.label||srv.id||language);
  return{name:c.providerName,title:c.providerName+" | "+label+" | "+language+" | "+quality,url:url,quality:quality,language:language,provider:c.providerId,sourceName:label,isDirect:/\.(?:m3u8|mp4|webm)(?:[?#]|$)/i.test(url),headers:ph,subtitles:subs}
}
async function resolve(args){
  var q=Q(args);if(!q)return null;
  var subs=await subtitles(q),out=[],seen={};
  for(var i=0;i<c.servers.length&&out.length<c.maxStreams;i++){
    var srv=c.servers[i]||{};if(!serverAllowed(srv,q))continue;
    var x=await one(q,srv,subs);if(!x)continue;
    var hk=[];for(var k in x.headers)hk.push(k.toLowerCase()+"="+S(x.headers[k]));hk.sort();
    var key=x.url+"\n"+hk.join("&")+"\n"+x.language;if(seen[key])continue;seen[key]=1;out.push(x)
  }
  return out
}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:c.providerId,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def _url(value: Any, *, required: bool = True) -> str:
    text = str(value or "").strip().rstrip("/")
    if required and not text.startswith(("http://", "https://")):
        raise ValueError(f"ticketed encrypted API requires HTTP(S) URL: {value!r}")
    return text

def apply(text: str, options: dict[str, Any] | None = None, context: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    raw = dict(options or {})
    provider_id = str(raw.get("providerId") or (context or {}).get("provider_id") or "").strip().casefold()
    if not provider_id:
        raise ValueError("ticketed encrypted API Bloc requires providerId/context provider_id")
    provider_name = str(raw.get("providerName") or provider_id).strip() or provider_id
    api_base = _url(raw.get("apiBase"))
    site_base = _url(raw.get("siteBase"))
    decrypt_url = _url(raw.get("decryptUrl"), required=False)
    servers = []
    for row in raw.get("servers") or []:
        if not isinstance(row, dict) or not str(row.get("id") or "").strip():
            continue
        servers.append({"id":str(row["id"]).strip(),"label":str(row.get("label") or row["id"]).strip(),"language":str(row.get("language") or "").strip(),"movieOnly":bool(row.get("movieOnly",False)),"tvOnly":bool(row.get("tvOnly",False)),"animeOnly":bool(row.get("animeOnly",False))})
    if not servers:
        raise ValueError("ticketed encrypted API Bloc requires at least one server")
    cfg={"providerId":provider_id,"providerName":provider_name,"apiBase":api_base,"siteBase":site_base,"challengePath":str(raw.get("challengePath") or "").strip(),"challengeBodyField":str(raw.get("challengeBodyField") or "altcha").strip(),"ticketPath":str(raw.get("ticketPath") or "/streams/ticket").strip(),"ticketMethod":str(raw.get("ticketMethod") or "POST").strip().upper(),"ticketField":str(raw.get("ticketField") or "ticket").strip(),"ticketHeader":str(raw.get("ticketHeader") or "X-Stream-Ticket").strip(),"ticketBodyAlways":bool(raw.get("ticketBodyAlways",False)),"moviePath":str(raw.get("moviePath") or "/streams/movie/{id}").strip(),"tvPath":str(raw.get("tvPath") or "/streams/tv/{id}/{season}/{episode}").strip(),"subtitleMoviePath":str(raw.get("subtitleMoviePath") or "").strip(),"subtitleTvPath":str(raw.get("subtitleTvPath") or "").strip(),"serverQueryKey":str(raw.get("serverQueryKey") or "s").strip(),"decryptUrl":decrypt_url,"decryptBodyField":str(raw.get("decryptBodyField") or "data").strip(),"servers":servers[:12],"maxPow":max(1,min(int(raw.get("maxPow") or 500000),2000000)),"maxStreams":max(1,min(int(raw.get("maxStreams") or 8),40)),"maxSubtitles":max(0,min(int(raw.get("maxSubtitles") or 48),96)),"userAgent":str(raw.get("userAgent") or "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36")}
    if not cfg["ticketPath"] or not cfg["moviePath"] or not cfg["tvPath"]:
        raise ValueError("ticketed encrypted API Bloc requires ticket/movie/tv paths")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={"runtimeFamily":"ticketed-encrypted-api-v1","provider":provider_id,"identity":"tmdb-direct","ticketSingleUsePerServer":True,"challenge":bool(cfg["challengePath"]),"decryptExternal":bool(cfg["decryptUrl"]),"webAssemblyRequired":False,"textCodecRequired":False,"terminalMediaPersisted":False,"ticketPersisted":False,"encryptedPayloadPersisted":False})

if __name__ == "__main__":
    raise SystemExit("patch module only")
