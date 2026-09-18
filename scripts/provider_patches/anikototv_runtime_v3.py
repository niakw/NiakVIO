#!/usr/bin/env python3
"""NiakVIO-owned AniKotoTV runtime v3.

Current clean-room chain:
  AniKoto search AJAX -> exact watch candidate -> episode list -> server list ->
  player URL -> MegaPlay page -> /stream/getSources.

MegaPlay currently exposes an encrypted ``enc`` payload instead of a plaintext
``sources`` array. If plaintext media exists it is returned normally; otherwise
the already identity-correlated and HTTP-verified MegaPlay player is preserved as
an embed for Core/player handling. No fake direct media URL is manufactured.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIKOTOTV.RUNTIME.V3"
MARKER = "NIAKVIO_ANIKOTOTV_RUNTIME_V3"

WRAPPER = r'''
/* NIAKVIO_ANIKOTOTV_RUNTIME_V3 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function q(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||{};if(md&&md.state==="ok"&&md.metadata)md=md.metadata;var type=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||ctx.canonicalMediaType||args[1]||"anime").toLowerCase();if(type==="tv")type="anime";if(type!=="anime")return null;var title=s((o&&o.title)||md.title||md.name||ctx.title),date=s(md.release_date||md.first_air_date||(o&&o.year)||ctx.year);return{type:"anime",title:title,year:Number(date.slice(0,4))||Number(o&&o.year)||0,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
function h(ref,xhr,cookie,origin){var out={"User-Agent":c.userAgent,"Accept":"text/html,application/json,text/plain,*/*"};if(ref)out.Referer=ref;if(xhr)out["X-Requested-With"]="XMLHttpRequest";if(cookie)out.Cookie=cookie;if(origin)out.Origin=origin;return out}
async function get(url,ref,xhr,cookie,origin){var r=await g.fetch(url,{headers:h(ref,xhr,cookie,origin),credentials:"include",redirect:"follow"});if(!r||!r.ok)throw new Error("anikoto_http_"+String(r&&r.status||0));var set="";try{set=s(r.headers&&r.headers.get&&r.headers.get("set-cookie"))}catch(_e){}return{body:await r.text(),url:r.url||url,cookie:set?set.split(";",1)[0]:""}}
function text(v){var src=s(v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return out.replace(/&[^;]+;/g," ")}
function score(a,b,year){var x=norm(a),y=norm(b);if(!x||!y)return 0;var n=x===y?240:(x.indexOf(y)>=0||y.indexOf(x)>=0?120:0);for(var t of y.split(" "))if(t.length>=3&&x.indexOf(t)>=0)n+=16;if(year&&s(a).indexOf(String(year))>=0)n+=20;return n}
function parsed(v){try{return JSON.parse(s(v))}catch(_e){return null}}
function searchHtml(raw){var data=parsed(raw),r=data&&data.result;if(r&&typeof r==="object"&&typeof r.html==="string")return r.html;if(typeof r==="string")return r;return s(raw)}
function results(raw,meta){var html=searchHtml(raw),out=[],re=/<a\b[^>]*href=["']([^"']*\/watch\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html))&&out.length<120){var title=text(m[2]),sc=score(title,meta.title,meta.year);if(sc<32)continue;var tail=s(m[1]).split("/watch/").pop().split(/[?#]/)[0],slug=tail.split("/")[0];if(slug)out.push({slug:slug,score:sc,title:title})}out.sort(function(a,b){return b.score-a.score});var seen={},v=[];for(var i=0;i<out.length&&v.length<6;i++){if(!seen[out[i].slug]){seen[out[i].slug]=1;v.push(out[i])}}return v}
function animeId(html){var m=/<[^>]+id=["']watch-main["'][^>]+data-id=["']([^"']+)/i.exec(html)||/<[^>]+data-id=["']([^"']+)["'][^>]+id=["']watch-main["']/i.exec(html);return s(m&&m[1])}
function episodeRows(raw){var data=parsed(raw),html=data&&data.result?data.result:raw,out=[],re=/<a\b([^>]+)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(s(html)))&&out.length<300){var attrs=m[1],id=(/(?:data-ep-id|data-id)=["']([^"']+)/i.exec(attrs)||[])[1]||"",num=Number(((/data-num=["']([^"']+)/i.exec(attrs)||[])[1]))||out.length+1,ids=(/data-ids=["']([^"']+)/i.exec(attrs)||[])[1]||"",slug=(/data-slug=["']([^"']+)/i.exec(attrs)||[])[1]||"";if(id||ids)out.push({id:id,num:num,ids:ids.replace(/[\\"']/g,""),slug:slug})}return out}
function serverLinks(raw){var data=parsed(raw),html=data&&data.result?data.result:raw,out=[],re=/data-link-id=["']([^"']+)["']/gi,m;while((m=re.exec(s(html)))&&out.length<12){if(m[1]&&!out.includes(m[1]))out.push(m[1])}return out}
function playerUrl(raw){var data=parsed(raw),r=data&&data.result?data.result:data;if(typeof r==="string"){var p=parsed(r);if(p)r=p}if(r&&typeof r==="object"){var u=s(r.url||r.file||r.src);if(/^https?:\/\//i.test(u))return u}if(typeof r==="string"){var m=/(https?:\/\/[^"'<>\s]+)/i.exec(r);if(m)return m[1]}return""}
async function finalSource(raw){var data=parsed(raw),src=data&&data.sources,file="";if(typeof src==="string")file=s(src);if(!file&&src&&typeof src==="object"&&!Array.isArray(src))file=s(src.file||src.url||src.src);if(!file&&Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\/\//i.test(u)){file=u;break}}}if(!file&&data&&data.enc)file=await decryptMega(data.enc);file=normalizeMegaMedia(file,data&&data.tracks);return /^https?:\/\//i.test(file)?file:""}
function utf8Bytes(value){if(typeof TextEncoder!=="undefined")return new TextEncoder().encode(String(value));var encoded=unescape(encodeURIComponent(String(value))),out=new Uint8Array(encoded.length);for(var i=0;i<encoded.length;i++)out[i]=encoded.charCodeAt(i)&255;return out}
function bytesHex(bytes){var out="";for(var i=0;i<bytes.length;i++)out+=bytes[i].toString(16).padStart(2,"0");return out}
function b64urlBytes(value){var x=s(value).replace(/-/g,"+").replace(/_/g,"/");while(x.length%4)x+="=";var raw=atob(x),out=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i)&255;return out}
function bytesText(bytes){if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8").decode(bytes);var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);try{return decodeURIComponent(escape(raw))}catch(_e){return raw}}
function megaDecodedFile(decoded){var data=parsed(decoded);return s(data&&(data.file||(Array.isArray(data)&&data[0]&&data[0].file)))}
function normalizeMegaMedia(file,tracks){var u=s(file);if(u.indexOf("//cdn.imgnex.top")>=0)u=u.replace("//cdn.imgnex.top","//ncdn.imgnex.top");if(u.indexOf("mewstream.buzz")>=0&&Array.isArray(tracks)){for(var i=0;i<tracks.length;i++){var f=s(tracks[i]&&tracks[i].file);if(!/^https?:\/\//i.test(f)||f.indexOf("mewstream.buzz")>=0)continue;try{var src=new URL(u),ref=new URL(f);src.host=ref.host;u=src.toString();break}catch(_e){}}}return u}
async function decryptMega(enc){diag("anikoto_megaplay_enc","enc="+(s(enc)?1:0)+";len="+String(s(enc).length));try{var keyRaw=utf8Bytes("i?LMTAx0Q6,:}50U"),key=new Uint8Array(32),iv=utf8Bytes("W0;27ToaUpl_P%'c"),cipher=b64urlBytes(enc);for(var i=0;i<keyRaw.length&&i<32;i++)key[i]=keyRaw[i];try{if(g&&g.crypto&&g.crypto.subtle&&typeof g.crypto.subtle.importKey==="function"){var cryptoKey=await g.crypto.subtle.importKey("raw",key,{name:"AES-CBC"},false,["decrypt"]),plainBuffer=await g.crypto.subtle.decrypt({name:"AES-CBC",iv:iv},cryptoKey,cipher),webFile=megaDecodedFile(bytesText(new Uint8Array(plainBuffer)));diag("anikoto_megaplay_crypto","webcrypto="+(webFile?1:0));if(/^https?:\/\//i.test(webFile))return webFile}}catch(_e){}try{if(g&&typeof g.__crypto_aes_decrypt_raw==="function"){var plain=g.__crypto_aes_decrypt_raw("AES-CBC",new Int8Array(key.buffer.slice(0)),new Int8Array(iv.buffer.slice(0)),new Int8Array(cipher.buffer.slice(0))),nativeFile=megaDecodedFile(bytesText(plain));diag("anikoto_megaplay_crypto","native="+(nativeFile?1:0));if(/^https?:\/\//i.test(nativeFile))return nativeFile}}catch(_e){}if(typeof require!=="function")return"";var C=require("crypto-js"),keyWord=C.enc.Hex.parse(bytesHex(key)),ivWord=C.enc.Hex.parse(bytesHex(iv)),cipherWord=C.enc.Hex.parse(bytesHex(cipher)),params=C.lib.CipherParams.create({ciphertext:cipherWord}),plainWord=C.AES.decrypt(params,keyWord,{iv:ivWord,mode:C.mode.CBC,padding:C.pad.Pkcs7}),cryptoFile=megaDecodedFile(plainWord.toString(C.enc.Utf8));diag("anikoto_megaplay_crypto","cryptojs="+(cryptoFile?1:0));return /^https?:\/\//i.test(cryptoFile)?cryptoFile:""}catch(_e){diag("anikoto_megaplay_error","decrypt=1");return""}}
function b64std(v){var x=s(v).replace(/-/g,"+").replace(/_/g,"/");while(x.length%4)x+="=";return x}
function b64urlWord(word,C){return C.enc.Base64.stringify(word).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"")}
function diag(stage,detail){try{var row={stage:s(stage).slice(0,64),lane:"anime",providerId:"anikototv",stepIndex:-1,route:s(detail).slice(0,240)};g.__nuvioProviderValueTraceV18=row;var hist=Array.isArray(g.__nuvioProviderValueTraceHistoryV21)?g.__nuvioProviderValueTraceHistoryV21:[];hist.push(row);while(hist.length>48)hist.shift();g.__nuvioProviderValueTraceHistoryV21=hist}catch(_e){}}
function megaFileId(html){var current=/\bdata-id=["'](\d+)["']/i.exec(html);if(current&&current[1])return s(current[1]);var legacy=/<title[^>]*>\s*File\s+(\d+)\s*-\s*MegaPlay/i.exec(html);return s(legacy&&legacy[1])}
function mergeCookies(){var jar={},order=[];for(var a=0;a<arguments.length;a++){for(var part of s(arguments[a]).split(/;\s*/)){var eq=part.indexOf("=");if(eq<=0)continue;var k=s(part.slice(0,eq)),v=s(part.slice(eq+1));if(!k||/^(?:path|domain|expires|max-age|samesite|secure|httponly)$/i.test(k))continue;if(!(k in jar))order.push(k);jar[k]=v}}return order.map(function(k){return k+"="+jar[k]}).join("; ")}
function megaMediaHost(url){try{var host=new URL(s(url)).hostname.toLowerCase(),domains=["megaplay.buzz","mewstream.buzz","lostproject.club","voltara.click","kotocdn.site","shiora.top","akirax.buzz","imgnex.top"];for(var i=0;i<domains.length;i++)if(host===domains[i]||host.endsWith("."+domains[i]))return true}catch(_e){}return false}
function megaPlaybackHeaders(mediaUrl,embedUrl,cookie){var known=megaMediaHost(mediaUrl),out={Referer:known?"https://megaplay.buzz/":embedUrl,"User-Agent":c.userAgent,Origin:"https://megaplay.buzz"};var merged=s(cookie);if(merged&&!known)out.Cookie=merged;return out}
async function resolveMega(url,referer,cookie){if(!/^https?:\/\/(?:www\.)?megaplay\.buzz\//i.test(s(url)))return null;var page=await get(url,referer,false,cookie,"https://megaplay.buzz"),fid=megaFileId(page.body);if(!fid)return null;var api="https://megaplay.buzz/stream/getSources?id="+encodeURIComponent(fid);try{var playerUrl=new URL(page.url||url),sv=playerUrl.searchParams.get("s");if(!sv){var sm=/\/stream\/s-(\d+)\//i.exec(playerUrl.pathname);if(sm)sv=sm[1]}if(sv)api+="&s="+encodeURIComponent(sv)}catch(_e){}var sources=await get(api,page.url||url,true,page.cookie||cookie,"https://megaplay.buzz"),direct=await finalSource(sources.body),data=parsed(sources.body);if(direct){diag("anikoto_megaplay_terminal","direct=1");return{url:direct,direct:true,player:page.url||url}}if(data&&typeof data==="object"&&s(data.enc)){diag("anikoto_megaplay_terminal","direct=0;fallback=1");return{url:page.url||url,direct:false,player:page.url||url}}return null}
function quality(url){var m=s(url).match(/(2160|1440|1080|720|480|360)p?/i);return m?m[1]+"p":""}
async function resolveOn(base,meta){var search=base+"/ajax/anime/search?keyword="+encodeURIComponent(meta.title),page=await get(search,base+"/",true,"",""),cands=results(page.body,meta);for(var i=0;i<cands.length;i++){var slug=cands[i].slug;try{var watch=await get(base+"/watch/"+encodeURIComponent(slug),base+"/",false,page.cookie,""),aid=animeId(watch.body);if(!aid)continue;var epsResp=await get(base+"/ajax/episode/list/"+encodeURIComponent(aid),watch.url,true,watch.cookie||page.cookie,""),episodes=episodeRows(epsResp.body);if(!episodes.length)continue;var wanted=episodes.find(function(e){return Number(e.num)===Number(meta.episode)})||episodes[meta.episode-1];if(!wanted)continue;var ids=s(wanted.ids||wanted.id);if(!ids)continue;var servers=await get(base+"/ajax/server/list?servers="+encodeURIComponent(ids),watch.url,true,watch.cookie||page.cookie,""),links=serverLinks(servers.body);for(var j=0;j<links.length&&j<8;j++){try{var st=await get(base+"/ajax/server?get="+encodeURIComponent(links[j]),watch.url,true,watch.cookie||page.cookie,""),u=playerUrl(st.body);if(!u)continue;var isMega=/^https?:\/\/(?:www\.)?megaplay\.buzz\//i.test(u),resolved=isMega?await resolveMega(u,watch.url,watch.cookie||page.cookie):{url:u,direct:false,player:u};if(!resolved||!resolved.url)continue;var media=resolved.url,ql=quality(media),headers=resolved.headers||{Referer:isMega?"https://megaplay.buzz/":base+"/","User-Agent":c.userAgent};if(isMega&&!headers.Origin)headers.Origin="https://megaplay.buzz";var row={name:c.name,title:c.name,url:media,provider:c.provider,headers:headers,isDirect:!!resolved.direct};if(!resolved.direct)row.__nuvioCorrelatedPlayerFallbackV1={url:media};if(ql)row.quality=ql;return[row]}catch(_e){}}}catch(_e){}}return[]}
async function run(args){var meta=q(args);if(!meta||!meta.title)return[];for(var i=0;i<c.mirrors.length;i++){try{var out=await resolveOn(c.mirrors[i],meta);if(out.length)return out}catch(_e){}}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAnikotoV3)return false;var fn=async function(){try{return await run(arguments)}catch(_e){return[]}};fn.__niakvioAnikotoV3=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    mirrors: list[str] = []
    for raw in cfg.get("mirrors") or [
        "https://anikototv.to",
        "https://anikoto.cz",
        "https://anikoto.me",
        "https://anikoto.net",
        "https://anikototv.se",
    ]:
        value = str(raw or "").strip().rstrip("/")
        if value.startswith(("http://", "https://")) and value not in mirrors:
            mirrors.append(value)
    payload = {
        "mirrors": mirrors[:5],
        "provider": "anikototv",
        "name": "AnikotoTV",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    }
    payload.update({k: v for k, v in cfg.items() if k not in {"mirrors"}})
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtime": payload,
            "runtimeFamily": "anikoto-ajax-megaplay-v3",
            "identity": "catalogue-title-season-episode",
            "encryptedMegaPlayFallback": "correlated-verified-embed",
            "fabricatesDirectMedia": False,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["anime"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
