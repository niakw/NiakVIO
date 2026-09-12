#!/usr/bin/env python3
"""MugiwaraStream anime + anime-film transport resolver.

Native discovery is preserved. Anime episodes reuse the observable Next.js
``animeServer`` data and structurally decode packed Smoothpre players. Anime
movies follow the site's current two-step contract: the parent ``/films`` page
identifies a film leaf from chronology/FILM_OPTIONS, then the exact leaf exposes
VF/VOSTFR player URLs. No site JavaScript is executed and no fixture URL is
hardcoded. Terminal media still flows through the shared Core guards.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MUGIWARASTREAM.PACKED.RUNTIME.V1"
MARKER = "NIAKVIO_MUGIWARASTREAM_PACKED_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MUGIWARASTREAM_PACKED_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
  function s(v){return String(v==null?"":v).trim()}
  function parseValue(v){var x=v;for(var i=0;i<3&&typeof x==="string";i++){var t=s(x);if(!t||t==="$undefined")break;try{x=JSON.parse(t)}catch(_e){break}}return x}
  function norm(v){return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
  function requestArgs(a){
    var first=a[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g.__nuvioMediaContext||{}}catch(_e){}
    var type=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||"").toLowerCase();
    if(type==="series")type="tv";/* NIAKVIO_MUGIWARA_TV_TRANSPORT_IS_ANIME_V1 */if(type==="tv")type="anime";if(type!=="anime"&&type!=="movie")return null;
    return {type:type,tmdbId:s((obj&&(obj.tmdbId||obj.id))||first||ctx.tmdbId),season:Number((obj&&obj.season)||a[2]||ctx.season)||1,episode:Number((obj&&obj.episode)||a[3]||ctx.episode)||1};
  }
  function isMugi(u){try{var h=new URL(String(u||"")).hostname.toLowerCase();return h==="mugiwara-no-streaming.com"||h==="www.mugiwara-no-streaming.com"}catch(_e){return false}}
  function headers(ref,accept){return {"User-Agent":c.ua,"Accept":accept||"text/html,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7","Referer":ref||c.base+"/"}}
  async function getText(url,ref,accept){try{var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:headers(ref,accept)});if(!r||!r.ok)return null;return {text:await r.text(),url:r.url||url,status:r.status}}catch(_e){return null}}
  function pushContent(html){var marker='self.__next_f.push([1,"',chunks=[],pos=0;while(true){var start=html.indexOf(marker,pos);if(start<0)break;var i=start+marker.length,out="",esc=false;while(i<html.length){var ch=html.charAt(i);if(esc){if(ch==="n")out+="\n";else if(ch==="t")out+="\t";else if(ch==="r")out+="\r";else if(ch==="\\")out+="\\";else if(ch==='"')out+='"';else if(ch==="/")out+="/";else if(ch==="u"&&i+4<html.length){var hex=html.slice(i+1,i+5);out+=String.fromCharCode(parseInt(hex,16));i+=4}else out+=ch;esc=false;i++;continue}if(ch==="\\"){esc=true;i++;continue}if(ch==='"'&&html.slice(i+1,i+3)==="])" )break;out+=ch;i++}if(out)chunks.push(out);pos=i+1}return chunks.join("")}
  function animeServer(html){var all=pushContent(html),mark='"animeServer":',idx=all.indexOf(mark);if(idx<0)return null;var start=all.indexOf("{",idx+mark.length);if(start<0)return null;var depth=0,inStr=false,esc=false,end=-1;for(var i=start;i<all.length;i++){var ch=all.charAt(i);if(esc){esc=false;continue}if(ch==="\\"&&inStr){esc=true;continue}if(ch==='"'){inStr=!inStr;continue}if(inStr)continue;if(ch==="{")depth++;else if(ch==="}"){depth--;if(depth===0){end=i+1;break}}}if(end<0)return null;try{return JSON.parse(all.slice(start,end))}catch(_e){return null}}
  function epCount(season){if(!season||!season.lang)return 0;var keys=Object.keys(season.lang),max=0;for(var i=0;i<keys.length;i++){var d=season.lang[keys[i]];if(!Array.isArray(d))continue;for(var j=0;j<d.length;j++)if(Array.isArray(d[j])&&d[j].length>max)max=d[j].length}return max}
  function matchSeason(rows,season,episode){if(!Array.isArray(rows))return null;var ss=String(season),i;for(i=0;i<rows.length;i++){var row=rows[i];if(!row||row.notASeason)continue;if(String(row.id)===ss&&episode<=epCount(row))return {row:row,index:episode-1}}var parts=[];for(i=0;i<rows.length;i++){var r=rows[i];if(r&&!r.notASeason&&String(r.id||"").split("-")[0]===ss)parts.push(r)}parts.sort(function(a,b){var aa=String(a.id).split("-"),bb=String(b.id).split("-");return (Number(aa[1])||0)-(Number(bb[1])||0)});if(parts.length){var start=0;for(i=0;i<parts.length;i++){var n=epCount(parts[i]);if(episode>start&&episode<=start+n)return {row:parts[i],index:episode-start-1};start+=n}}var ordered=rows.filter(function(r){return r&&!r.notASeason});if(season-1>=0&&season-1<ordered.length&&episode<=epCount(ordered[season-1]))return {row:ordered[season-1],index:episode-1};return null}
  function episodeSources(row,lang,index){var out=[],data=row&&row.lang&&row.lang[lang];if(!Array.isArray(data))return out;for(var i=0;i<data.length;i++){var arr=data[i];if(Array.isArray(arr)&&index>=0&&index<arr.length){var u=s(arr[index]);if(u.indexOf("//")===0)u="https:"+u;if(/^https?:\/\//i.test(u))out.push({url:u,lang:lang})}}return out}
  function filmSources(raw){var fo=parseValue(raw),out=[];if(!fo||typeof fo!=="object")return out;var langMap=parseValue(fo.lang);if(!langMap||typeof langMap!=="object")return out;var names=parseValue(fo.names),filmCount=Array.isArray(names)&&names.length?names.length:1,langs=["vostfr","vf"];for(var li=0;li<langs.length;li++){var lang=langs[li],data=parseValue(langMap[lang]);if(!Array.isArray(data))continue;for(var si=0;si<data.length;si++){var arr=parseValue(data[si]);if(!Array.isArray(arr))continue;for(var fi=0;fi<filmCount&&fi<arr.length;fi++){var u=s(arr[fi]);if(u.indexOf("//")===0)u="https:"+u;if(/^https?:\/\//i.test(u))out.push({url:u,lang:lang})}}}return out}
  function rank(u){var x=s(u).toLowerCase();if(x.indexOf("smoothpre")>=0)return 0;if(x.indexOf("vidmoly")>=0||x.indexOf("voembed")>=0||x.indexOf("ansembed")>=0)return 1;if(x.indexOf("sibnet")>=0)return 2;return 20}
  function key(n,radix){var chars="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";if(n<radix)return chars.charAt(n);return key(Math.floor(n/radix),radix)+chars.charAt(n%radix)}
  function jsstr(src,pos){while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;var q=src.charAt(pos);if(q!=="'"&&q!=='"')return null;var out="",i=pos+1;for(;i<src.length;i++){var ch=src.charAt(i);if(ch===q)return {v:out,p:i+1};if(ch==="\\"&&i+1<src.length){i++;var e=src.charAt(i);out+=e==="n"?"\n":e==="r"?"\r":e==="t"?"\t":e}else out+=ch}return null}
  function unpackOne(src,offset){var mark="eval(function(p,a,c,k,e,d)",st=src.indexOf(mark,offset||0);if(st<0)return null;var call=src.indexOf("}(",st);if(call<0)return null;var p=jsstr(src,call+2);if(!p)return null;var pos=p.p;while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;if(src.charAt(pos)!==",")return null;var mm=/^\s*(\d+)\s*,\s*(\d+)\s*,/.exec(src.slice(pos+1));if(!mm)return null;var radix=Number(mm[1]),count=Number(mm[2]);if(radix<2||radix>62||count>10000)return null;pos=pos+1+mm[0].length;var w=jsstr(src,pos);if(!w)return null;var vals=w.v.split("|"),dict={};for(var n=count-1;n>=0;n--){var k=key(n,radix);dict[k]=(n<vals.length&&vals[n])?vals[n]:k}return {decoded:p.v.replace(/\b\w+\b/g,function(x){return Object.prototype.hasOwnProperty.call(dict,x)?dict[x]:x}),next:call+2}}
  /* NIAKVIO_MUGIWARA_RELATIVE_PACKED_MEDIA_V1 */
  function media(src,base){var full=s(src),pos=0;for(var i=0;i<8;i++){var r=unpackOne(full,pos);if(!r)break;full+="\n"+r.decoded;pos=r.next}full=full.replace(/\\\//g,"/").replace(/&amp;/g,"&").replace(/&quot;/g,'"');var out=[],seen={};function add(raw){var u=s(raw).replace(/[),\];}]+$/g,"");if(!u)return;if(u.indexOf("//")===0)u="https:"+u;else if(u.charAt(0)==="/"&&base){try{u=new URL(u,base).toString()}catch(_e){return}}if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u)}var m,re=/https?:\/\/[^\s"'<>\\]+(?:\.m3u8|\/hls2\/|\/master\.m3u8)[^\s"'<>\\]*/gi;while((m=re.exec(full))!==null)add(m[0]);var rel=/["'](\/[^\s"'<>\\]+(?:\.m3u8|\/hls2\/|\/master\.m3u8)[^\s"'<>\\]*)["']/gi;while((m=rel.exec(full))!==null)add(m[1]);return out}
  async function proveHls(url,player,lang){try{var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:headers(player,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*")});if(!r||!r.ok)return null;var body=await r.text();if(!/^#EXTM3U/m.test(body))return null;var label=lang==="vf"?"VF":"VOSTFR";return {name:"Mugiwara | "+label,title:"Mugiwara",url:url,quality:"HD",language:label,headers:headers(player,"application/vnd.apple.mpegurl,application/x-mpegURL,*/*"),provider:"mugiwarastream",isDirect:true}}catch(_e){return null}}
  async function genericPlayer(row){try{if(typeof _crawlDirectMedia==="function"){var rows=await _crawlDirectMedia([row.url],c.base+"/",2);if(Array.isArray(rows)&&rows.length){var x=rows[0];if(x&&typeof x==="object"){x.name=x.name||"Mugiwara";x.title=x.title||"Mugiwara";x.language=x.language||(row.lang==="vf"?"VF":"VOSTFR");return x}}}}catch(_e){}return null}
  async function resolvePlayer(row){var rk=rank(row.url);if(rk===0){var p=await getText(row.url,c.base+"/","text/html,*/*");if(!p)return null;var urls=media(p.text,p.url);for(var i=0;i<urls.length&&i<6;i++){var ok=await proveHls(urls[i],p.url,row.lang);if(ok)return ok}}if(rk<=2)return await genericPlayer(row);return null}
  async function resolveRows(rows){rows.sort(function(a,b){return rank(a.url)-rank(b.url)});var streams=[],seen={};for(var i=0;i<rows.length&&i<10;i++){var st=await resolvePlayer(rows[i]);if(st&&st.url&&!seen[st.url]){seen[st.url]=1;streams.push(st)}if(streams.length>=3)break}return streams}
  async function tmdbTitle(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn!=="function"||!q.tmdbId)return"";var z=await fn({tmdbId:String(q.tmdbId),mediaType:"movie",tmdbNamespace:"movie"}),m=z&&z.metadata;if(!m)return"";return s(m.title||m.name||m.original_title||m.original_name)}catch(_e){return""}}
  async function filmLeafId(data,q){var options=data&&data.options||{},chron=Array.isArray(options.chronologie)?options.chronologie:[],films=chron.filter(function(x){return x&&x.type==="film"&&s(x.id)});if(films.length===1)return s(films[0].id);var title=norm(await tmdbTitle(q));if(title){for(var i=0;i<films.length;i++){var n=norm(films[i].name),id=norm(films[i].id);if(n===title||id===title||n.indexOf(title)>=0||title.indexOf(n)>=0)return s(films[i].id)}}var names=parseValue(options.FILM_OPTIONS&&options.FILM_OPTIONS.names);if(Array.isArray(names)&&names.length===1){var one=norm(names[0]&&names[0].name);for(var j=0;j<films.length;j++)if(norm(films[j].name)===one)return s(films[j].id)}return films.length?s(films[0].id):""}
  async function movieFallback(pageUrl,data,q){var direct=filmSources(data&&data.options&&data.options.FILM_OPTIONS);if(direct.length)return await resolveRows(direct);var id=await filmLeafId(data,q);if(!id)return[];var root=pageUrl.replace(/\/films(?:\/[^/?#]+)?(?:[?#].*)?$/i,"/films");var leaf=await getText(root+"/"+encodeURIComponent(id),pageUrl,"text/html,*/*");if(!leaf)return[];var exact=animeServer(leaf.text);if(!exact||!exact.options)return[];return await resolveRows(filmSources(exact.options.FILM_OPTIONS))}
  async function fallback(pageUrl,q){var page=await getText(pageUrl,c.base+"/","text/html,*/*");if(!page)return[];var data=animeServer(page.text);if(!data||!data.options)return[];if(q.type==="movie")return await movieFallback(page.url,data,q);var seasons=parseValue(data.options.saisons);if(!Array.isArray(seasons))return[];var matched=matchSeason(seasons,q.season,q.episode);if(!matched)return[];var rows=[];["vostfr","vf"].forEach(function(lang){var a=episodeSources(matched.row,lang,matched.index);for(var i=0;i<a.length;i++)rows.push(a[i])});return await resolveRows(rows)}
  async function resolve(a,ctx){var q=requestArgs(a);if(!q||!ctx||typeof ctx.native!=="function"||typeof g.fetch!=="function")return q===null?null:[];var nativeFetch=g.fetch,pageUrl="";g.fetch=async function(url,opt){var u=s(url);if(isMugi(u)&&/\/catalogue\/[^/?#]+\/(?:episodes\/saison\d+|films)(?:[/?#]|$)/i.test(u))pageUrl=u;var o=opt&&typeof opt==="object"?Object.assign({},opt):{};if(isMugi(u)){var h=Object.assign({},o.headers||{});h["User-Agent"]=c.ua;if(!h["Accept-Language"]&&!h["accept-language"])h["Accept-Language"]="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7";o.headers=h}return nativeFetch.call(this,url,o)};var nativeResult=[];try{nativeResult=await ctx.native.apply(ctx.receiver,a)}catch(_e){}finally{g.fetch=nativeFetch}/* NIAKVIO_MUGIWARA_SPECIALIZED_FALLBACK_PRIORITY_V1 */if(pageUrl){var specialized=await fallback(pageUrl,q);if(Array.isArray(specialized)&&specialized.length)return specialized;/* NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2 */if(q.type!=="movie")return[]}if(Array.isArray(nativeResult)&&nativeResult.length)return nativeResult;return[]}
  try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"mugiwarastream",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    payload={"base":str(cfg.get("base") or "https://www.mugiwara-no-streaming.com").rstrip("/"),"ua":str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")}
    wrapper=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,wrapper,data={"semanticLanes":["movie","anime"],"nativeDiscoveryReuse":True,"nextFlightAnimeServer":True,"movieLeafFromChronology":True,"animeFilmOptions":True,"playerResolvers":["smoothpre-packed","shared-crawl"],"packedDecodeNoEval":True,"runtimeResolverRegistration":True,"fixtureHardcodes":False})


if __name__ == "__main__":
    raise SystemExit("patch module only")
