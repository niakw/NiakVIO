#!/usr/bin/env python3
"""Frenchstream exact TMDB movie + TV runtime.

Provider-owned transport only. Movies use the site's exact f-{TMDB} identity
and film_api.php; TV uses s-{TMDB}, get_seasons.php and eps_{id}.txt. Player
pages are decoded structurally (Dean-Edwards packer, never eval), terminal HLS
is accepted only after a 2xx response whose body starts with #EXTM3U, and the
known Vidzy troll playlist is always rejected. Core retains ownership of final
facts/identity/media-type/presentation/branding/sanitization.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.FRENCHSTREAM.TV.RUNTIME.V2"
MARKER = "NIAKVIO_FRENCHSTREAM_TV_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_FRENCHSTREAM_TV_RUNTIME_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
  function s(v){return String(v==null?"":v).trim()}
  function argsOf(a){
    var first=a[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g.__nuvioMediaContext||{}}catch(_e){}
    var type=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();
    if(type==="series")type="tv";
    if(type!=="movie"&&type!=="tv")return null;
    return {
      type:type,
      tmdbId:s((obj&&(obj.tmdbId||obj.id))||first),
      season:Number((obj&&obj.season)||a[2]||ctx.season)||1,
      episode:Number((obj&&obj.episode)||a[3]||ctx.episode)||1
    };
  }
  function hdr(ref,accept){return {"User-Agent":c.ua,"Accept":accept||"*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7","Referer":ref||c.bases[0]+"/"}}
  async function text(url,ref,accept){try{var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:hdr(ref,accept)});if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url,status:r.status}}catch(_e){return null}}
  function key(n,radix){var chars="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";if(n<radix)return chars.charAt(n);return key(Math.floor(n/radix),radix)+chars.charAt(n%radix)}
  function jsstr(src,pos){while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;var q=src.charAt(pos);if(q!=="'"&&q!=='"')return null;var out="",i=pos+1;for(;i<src.length;i++){var ch=src.charAt(i);if(ch===q)return {v:out,p:i+1};if(ch==="\\"&&i+1<src.length){i++;var e=src.charAt(i);out+=e==="n"?"\n":e==="r"?"\r":e==="t"?"\t":e}else out+=ch}return null}
  function unpackOne(src,offset){
    var mark="eval(function(p,a,c,k,e,d)",st=src.indexOf(mark,offset||0);if(st<0)return null;
    var call=src.indexOf("}(",st);if(call<0)return null;var p=jsstr(src,call+2);if(!p)return null;
    var pos=p.p;while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;if(src.charAt(pos)!==",")return null;
    var mm=/^\s*(\d+)\s*,\s*(\d+)\s*,/.exec(src.slice(pos+1));if(!mm)return null;var radix=Number(mm[1]),count=Number(mm[2]);if(radix<2||radix>62||count>10000)return null;pos=pos+1+mm[0].length;
    var w=jsstr(src,pos);if(!w)return null;var vals=w.v.split("|"),dict={};for(var n=count-1;n>=0;n--){var k=key(n,radix);dict[k]=(n<vals.length&&vals[n])?vals[n]:k}
    return {decoded:p.v.replace(/\b\w+\b/g,function(x){return Object.prototype.hasOwnProperty.call(dict,x)?dict[x]:x}),next:call+2};
  }
  function media(src){
    var full=s(src),pos=0;for(var i=0;i<8;i++){var row=unpackOne(full,pos);if(!row)break;full+="\n"+row.decoded;pos=row.next}
    full=full.replace(/\\\//g,"/").replace(/&amp;/g,"&").replace(/&quot;/g,'"');
    var out=[],seen={},re=/https?:\/\/[^\s"'<>\\]+(?:\.m3u8|\/hls2\/|\/master\.m3u8)[^\s"'<>\\]*/gi,m;
    while((m=re.exec(full))!==null){var u=m[0].replace(/[),\];}]+$/g,"");if(/\/troll\/master\.m3u8/i.test(u)||seen[u])continue;seen[u]=1;out.push(u)}return out;
  }
  function langLabel(v){var x=s(v).toLowerCase();if(x==="vf"||x==="vff"||x==="vfq"||x==="default")return "VF";if(x==="vostfr")return "VOSTFR";if(x==="vo")return "VO";return x?x.toUpperCase():"VF"}
  function hostRank(v){var x=s(v).toLowerCase();if(x==="premium"||x.indexOf("fsvid")>=0)return 0;if(x.indexOf("uqload")>=0)return 1;if(x.indexOf("vidzy")>=0)return 2;if(x.indexOf("voe")>=0)return 3;if(x.indexOf("filemoon")>=0||x.indexOf("filmoon")>=0)return 4;if(x.indexOf("netu")>=0)return 20;if(x.indexOf("dood")>=0||x.indexOf("streamtape")>=0||x.indexOf("kakaflix")>=0)return 100;return 10}
  async function validateHls(u,player,lang,host){
    if(!u||/\/troll\/master\.m3u8/i.test(u))return null;try{var r=await g.fetch(u,{method:"GET",redirect:"follow",headers:hdr(player,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")});if(!r||!r.ok)return null;var b=await r.text();if(!/^#EXTM3U/m.test(b))return null;var h=s(host||"PLAYER").toUpperCase();return {name:"Frenchstream | "+h,title:"Frenchstream | "+h,url:u,quality:"HD",language:langLabel(lang),headers:hdr(player,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"frenchstream",isDirect:true}}catch(_e){return null}
  }
  async function player(row,detailRef){
    if(/\.m3u8(?:[?#]|$)/i.test(row.url)||/\/hls2\//i.test(row.url)){var direct=await validateHls(row.url,detailRef,row.lang,row.host);if(direct)return direct}
    var p=await text(row.url,detailRef,"text/html,*/*");if(!p)return null;var xs=media(p.text);for(var i=0;i<xs.length&&i<8;i++){var ok=await validateHls(xs[i],p.url,row.lang,row.host);if(ok)return ok}return null;
  }
  async function resolveRows(rows,detailRef){
    rows.sort(function(a,b){return hostRank(a.host)-hostRank(b.host)});var streams=[],seen={};
    for(var i=0;i<rows.length&&i<12;i++){if(hostRank(rows[i].host)>=100)continue;var st=await player(rows[i],detailRef);if(st&&!seen[st.url]){seen[st.url]=1;streams.push(st)}if(streams.length>=4)break}
    return streams;
  }
  function seasonId(rows,n){
    if(!Array.isArray(rows)||!rows.length)return "";for(var i=0;i<rows.length;i++){var t=s(rows[i]&&rows[i].title),m=/saison\s*(\d+)/i.exec(t);if(m&&Number(m[1])===n)return s(rows[i].id)}
    return s(rows[Math.max(0,Math.min(rows.length-1,n-1))]&&rows[Math.max(0,Math.min(rows.length-1,n-1))].id);
  }
  function tvCandidates(epData,ep){
    var out=[],langs=["vf","vostfr","vo"],priority=["premium","uqload","vidzy"];
    for(var li=0;li<langs.length;li++){var lang=langs[li],per=epData&&epData[lang],players=per&&(per[String(ep)]||per[ep]);if(!players||typeof players!=="object")continue;
      var used={};for(var pi=0;pi<priority.length;pi++){var h=priority[pi],u=s(players[h]);if(/^https?:\/\//i.test(u)){out.push({url:u,lang:lang,host:h});used[h]=1}}
      var keys=Object.keys(players);for(var ki=0;ki<keys.length;ki++){var k=keys[ki],v=s(players[k]);if(!used[k]&&/^https?:\/\//i.test(v))out.push({url:v,lang:lang,host:k})}
    }return out;
  }
  function newsIds(html){
    var out=[],seen={},patterns=[/openModal\(["']?(\d+)/gi,/data-id=["']?(\d+)/gi,/[?&]newsid=(\d+)/gi,/href=["'][^"']*\/(\d+)-[^"']+["']/gi],m;
    for(var p=0;p<patterns.length;p++){patterns[p].lastIndex=0;while((m=patterns[p].exec(html))!==null){if(!seen[m[1]]){seen[m[1]]=1;out.push(m[1])}}}return out.slice(0,12);
  }
  function movieRows(data){
    var out=[],players=data&&data.players;if(!players||typeof players!=="object")return out;var hosts=Object.keys(players);
    for(var hi=0;hi<hosts.length;hi++){var host=hosts[hi],versions=players[host];if(typeof versions==="string"){if(/^https?:\/\//i.test(versions))out.push({url:versions,lang:"default",host:host});continue}if(!versions||typeof versions!=="object")continue;var langs=Object.keys(versions);for(var li=0;li<langs.length;li++){var u=s(versions[langs[li]]);if(/^https?:\/\//i.test(u))out.push({url:u,lang:langs[li],host:host})}}
    return out;
  }
  async function movie(base,q){
    var tag="f-"+q.tmdbId,search=await text(base+"/index.php?do=xfsearch&xfname=tagz&xf="+encodeURIComponent(tag),base+"/","text/html,*/*");if(!search)return [];
    var ids=newsIds(search.text);for(var i=0;i<ids.length;i++){
      var api=await text(base+"/engine/ajax/film_api.php?id="+encodeURIComponent(ids[i]),search.url,"application/json,text/plain,*/*");if(!api)continue;var data=null;try{data=JSON.parse(api.text)}catch(_e){};if(!data||s(data.meta&&data.meta.tagz)!==tag)continue;
      var streams=await resolveRows(movieRows(data),api.url);if(streams.length)return streams;
    }return [];
  }
  async function tv(base,q){
    var sr=await text(base+"/engine/ajax/get_seasons.php?serie_tag="+encodeURIComponent("s-"+q.tmdbId)+"&news_id=0",base+"/","application/json,text/plain,*/*");if(!sr)return [];
    var seasons=[];try{seasons=JSON.parse(sr.text)}catch(_e){};var sid=seasonId(seasons,q.season);if(!sid)return [];
    var ep=await text(base+"/data/eps_"+encodeURIComponent(sid)+".txt?v="+Math.floor(Date.now()/30000),base+"/index.php?newsid="+encodeURIComponent(sid),"application/json,text/plain,*/*");if(!ep)return [];
    var data=null;try{data=JSON.parse(ep.text)}catch(_e2){};if(!data)return [];return await resolveRows(tvCandidates(data,q.episode),ep.url);
  }
  async function resolve(a){
    var q=argsOf(a);if(!q||!q.tmdbId)return q===null?null:[];
    for(var bi=0;bi<c.bases.length;bi++){
      var base=c.bases[bi].replace(/\/$/,""),streams=q.type==="movie"?await movie(base,q):await tv(base,q);if(streams.length)return streams;
    }
    return [];
  }
  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"frenchstream",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    bases=cfg.get("bases") if isinstance(cfg.get("bases"),list) else ["https://french-stream.one","https://fs23.lol","https://fs16.lol"]
    payload={
        "bases":[str(v).rstrip("/") for v in bases if str(v).strip()],
        "ua":str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"),
    }
    wrapper=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,wrapper,data={"semanticLanes":["movie","tv"],"movieIdentity":"f-{tmdbId}","movieApi":"film_api.php?id={newsId}","tvIdentity":"s-{tmdbId}","seasonApi":"get_seasons.php","episodeApi":"eps_{seasonNewsId}.txt","packedDecodeNoEval":True,"terminal":"2xx + EXTM3U","rejectTrollHls":True,"runtimeResolverRegistration":True,"fixtureHardcodes":False})


if __name__ == "__main__":
    raise SystemExit("patch module only")
