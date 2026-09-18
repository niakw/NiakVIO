#!/usr/bin/env python3
"""AllWish current runtime v2: VRF episode API + direct MegaPlay resolution."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLWISH.CURRENT.RUNTIME.V2"
MARKER = "NIAKVIO_ALLWISH_CURRENT_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_ALLWISH_CURRENT_RUNTIME_V2 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioAllWishCurrentV2)return;
    var original=_spv4GetStreams,BASE="https://all-wish.me",UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36";
    function s(v){return String(v==null?"":v).trim()}
    function hdr(ref,json){var h={"User-Agent":UA,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7","Accept":json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,text/plain,*/*"};if(ref)h.Referer=ref;if(json)h["X-Requested-With"]="XMLHttpRequest";return h}
    function attr(raw,name){var m=new RegExp("(?:^|\\s)"+name+"\\s*=\\s*[\\\"']([^\\\"']*)[\\\"']","i").exec(String(raw||""));return m?m[1]:""}
    function visible(v){var src=String(v==null?"":v),out="",tag=false;for(var i=0;i<src.length;i++){var ch=src.charAt(i);if(ch==="<"){tag=true;out+=" ";continue}if(ch===">"){tag=false;continue}if(!tag)out+=ch}return out.replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\s+/g," ").trim()}
    function b64(bytes){var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",out="",i=0;while(i<bytes.length){var a=bytes[i++]&255,b=i<bytes.length?bytes[i++]&255:-1,c=i<bytes.length?bytes[i++]&255:-1;out+=chars.charAt(a>>2);out+=chars.charAt(((a&3)<<4)|(b<0?0:b>>4));out+=b<0?"=":chars.charAt(((b&15)<<2)|(c<0?0:c>>6));out+=c<0?"=":chars.charAt(c&63)}return out}
    function b64url(bytes){return b64(bytes).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"")}
    function vrf(id){var key="ysJhV6U27FVIjjuk",input=encodeURIComponent(s(id)),box=[],j=0,i;for(i=0;i<256;i++)box[i]=i;for(i=0;i<256;i++){j=(j+box[i]+key.charCodeAt(i%key.length))&255;var t=box[i];box[i]=box[j];box[j]=t}var x=0,y=0,raw=[];for(i=0;i<input.length;i++){x=(x+1)&255;y=(y+box[x])&255;var q=box[x];box[x]=box[y];box[y]=q;raw.push(input.charCodeAt(i)^box[(box[x]+box[y])&255])}var first=b64url(raw),delta=[-3,3,-4,2,-2,5,4,5],stage=[];for(i=0;i<first.length;i++)stage.push((first.charCodeAt(i)+delta[i%8])&255);var second=b64url(stage);return second.replace(/[A-Za-z]/g,function(ch){var z=ch.charCodeAt(0),base=z<=90?65:97;return String.fromCharCode(((z-base+13)%26)+base)})}
    function metaTitles(meta){return _uniq([meta&&meta.title,meta&&meta.name,meta&&meta.original_title,meta&&meta.original_name].concat(meta&&Array.isArray(meta.aliases)?meta.aliases:[])).map(function(v){return _slug(s(v))}).filter(Boolean)}
    function candidates(html,meta){var out=[],seen={},expect=metaTitles(meta),re=/<a\b([^>]*)href=["']([^"']*\/watch\/[^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(String(html||"")))&&out.length<100){var u=_absolute(m[2],BASE),hay=_slug(visible(m[4])+" "+m[2]),score=0;if(!u||seen[u])continue;for(var i=0;i<expect.length;i++){var e=expect[i];if(hay===e)score=Math.max(score,300);else if(e.length>=4&&hay.indexOf(e)>=0)score=Math.max(score,100)}if(score>0){seen[u]=1;out.push({url:u,score:score,tip:attr((m[1]||"")+" "+(m[3]||""),"data-tip")})}}out.sort(function(a,b){return b.score-a.score});return out}
    function showId(html,fallback){var src=String(html||""),patterns=[/id=["']watch-page["'][^>]*\bdata-id=["'](\d+)["']/i,/\bdata-id=["'](\d+)["'][^>]*\bid=["']watch-page["']/i,/<main\b[^>]*\bdata-id=["'](\d+)["']/i,/<div\b[^>]*class=["'][^"']*container[^"']*["'][^>]*\bdata-id=["'](\d+)["']/i],m;for(var i=0;i<patterns.length;i++){m=patterns[i].exec(src);if(m)return m[1]}return /^\d+$/.test(s(fallback))?s(fallback):""}
    function episodeIds(markup,episode){var wanted=Number(episode)||1,re=/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(String(markup||"")))){var attrs=m[1]||"",slug=Number(attr(attrs,"data-slug")||0),num=Number(attr(attrs,"data-num")||0);if(slug!==wanted&&num!==wanted)continue;var ids=attr(attrs,"data-ids");if(ids)return ids}return""}
    function serverRows(markup){var out=[],seen={},re=/<(?:div|a)\b([^>]*)>/gi,m;while((m=re.exec(String(markup||"")))&&out.length<12){var id=attr(m[1],"data-link-id");if(!id||seen[id])continue;seen[id]=1;out.push({id:id,type:attr(m[1],"data-type")})}if(out.length)return out;re=/data-link-id=["']([^"']+)["']/gi;while((m=re.exec(String(markup||"")))&&out.length<12){if(!seen[m[1]]){seen[m[1]]=1;out.push({id:m[1],type:""})}}return out}
    function sourceUrl(data){var src=data&&data.sources;if(typeof src==="string"&&/^https?:\/\//i.test(s(src)))return s(src);if(src&&typeof src==="object"&&!Array.isArray(src)){var u=s(src.file||src.url||src.src);if(/^https?:\/\//i.test(u))return u}if(Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\/\//i.test(u))return u}}return""}
    function subtitles(data){var rows=Array.isArray(data&&data.tracks)?data.tracks:[],out=[];for(var i=0;i<rows.length;i++){var r=rows[i]||{},u=s(r.file||r.url);if(!/^https?:\/\//i.test(u))continue;out.push({url:u,language:s(r.label||r.lang||""),name:s(r.label||r.lang||"")})}return out}
    async function mega(embed,watch,label,meta){try{var page=await _fetch(embed,{headers:hdr(watch,false)});if(!page||!page.ok)return[];var html=await page.text(),id=(/\bdata-id=["']([^"']+)["']/i.exec(html)||[])[1]||"";if(!id)return[];var origin="";try{origin=new URL(page.url||embed).origin}catch(_e){origin="https://megaplay.buzz"}var api=origin+"/stream/getSources?id="+encodeURIComponent(id),res=await _fetch(api,{headers:Object.assign(hdr(page.url||embed,true),{Origin:origin})});if(!res||!res.ok)return[];var data=await res.json(),u=sourceUrl(data);if(!u)return[];return[{name:NIAKVIO_PROVIDER_MODEL.displayName,title:s(meta&&meta.title)||NIAKVIO_PROVIDER_MODEL.displayName,url:u,provider:"allwish",language:s(label),isDirect:true,headers:{Referer:origin+"/",Origin:origin,"User-Agent":UA},subtitles:subtitles(data)}]}catch(_e){return[]}}
    async function current(tmdbId,mediaType,season,episode){if(_mediaNamespace(mediaType)==="movie")return[];var ep=Math.floor(Number(episode)||0);if(ep<=0)return[];var meta;try{meta=await _tmdb(tmdbId,mediaType)}catch(_e){meta=null}if(!meta||!meta.title)return[];var search=BASE+"/filter?keyword="+encodeURIComponent(meta.title),sr;try{sr=await _fetch(search,{headers:hdr(BASE+"/",false)})}catch(_e){return[]}if(!sr||!sr.ok)return[];var rows=candidates(await sr.text(),meta);for(var ci=0;ci<Math.min(rows.length,4);ci++){try{var wr=await _fetch(rows[ci].url,{headers:hdr(search,false)});if(!wr||!wr.ok)continue;var watch=wr.url||rows[ci].url,html=await wr.text(),id=showId(html,rows[ci].tip);if(!id)continue;var lr=await _fetch(BASE+"/ajax/episode/list/"+encodeURIComponent(id)+"?vrf="+encodeURIComponent(vrf(id)),{headers:hdr(watch,true)});if(!lr||!lr.ok)continue;var lv=await lr.json(),ids=episodeIds(lv&&lv.result,ep);if(!ids)continue;var sl=await _fetch(BASE+"/ajax/server/list?servers="+encodeURIComponent(ids),{headers:hdr(watch,true)});if(!sl||!sl.ok)continue;var sv=await sl.json(),servers=serverRows(sv&&sv.result),out=[];for(var i=0;i<servers.length&&out.length<8;i++){try{var rr=await _fetch(BASE+"/ajax/server?get="+encodeURIComponent(servers[i].id),{headers:hdr(watch,true)});if(!rr||!rr.ok)continue;var rv=await rr.json(),u=s(rv&&rv.result&&rv.result.url);if(!/^https?:\/\//i.test(u))continue;if(/(?:megaplay|rapid-cloud)/i.test(u)){var direct=await mega(u,watch,servers[i].type,meta);if(direct.length){out.push.apply(out,direct);continue}}out.push({name:NIAKVIO_PROVIDER_MODEL.displayName,title:s(meta.title),url:u,provider:"allwish",headers:{Referer:watch,Origin:BASE},__nuvioCorrelatedPlayerFallbackV1:{url:u}})}catch(_e){}}if(out.length)return out}catch(_e){}}return[]}
    var wrapped=async function(tmdbId,mediaType,season,episode){try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return[]}};
    wrapped.__niakvioAllWishCurrentV2=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;try{if(typeof module!=="undefined"&&module.exports&&typeof module.exports==="object")module.exports.getStreams=wrapped}catch(_e){}
  }catch(_e){}
})();
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(text, MANAGED_FIX_ID, WRAPPER, data={
        "scope": "provider-local-current-search-vrf-episode-server-megaplay-v2",
        "providerBaseModified": False,
        "fixtureIdsHardcoded": False,
        "identityRequired": True,
        "episodeVrfRequired": True,
        "megaPlayDirectWhenPlainSource": True,
        "encryptedMegaPlayFailsClosed": True,
    })


if __name__ == "__main__":
    raise SystemExit("patch module only")
