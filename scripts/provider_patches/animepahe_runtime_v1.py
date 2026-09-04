#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMEPAHE.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMEPAHE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMEPAHE_RUNTIME_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function arr(v){return Array.isArray(v)?v:[]}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g,"")}
function abs(u,b){try{return new URL(s(u),b).toString()}catch(_e){return""}}
function origin(u){try{return new URL(s(u)).origin}catch(_e){return""}}
function aliases(md){var out=[md&&md.title,md&&md.name,md&&md.original_title,md&&md.original_name],a=md&&md.alternative_titles&&(md.alternative_titles.results||md.alternative_titles.titles);if(Array.isArray(a))for(var i=0;i<a.length;i++)out.push(a[i]&&(a[i].title||a[i].name));var seen={},r=[];for(var j=0;j<out.length;j++){var x=s(out[j]);if(!x||seen[x])continue;seen[x]=1;r.push(x)}return r.slice(0,10)}
function req(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||{};var canonical=s((obj&&obj.canonicalMediaType)||ctx.canonicalMediaType||(obj&&obj.mediaType)||args[1]).toLowerCase();if(canonical!=="anime")return null;var ns=s((obj&&obj.tmdbNamespace)||ctx.tmdbNamespace).toLowerCase();if(ns!=="movie"&&ns!=="tv")ns="tv";var season=Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode=Number((obj&&obj.episode)!=null?obj.episode:args[3])||1;var imdb=s((obj&&(obj.imdbId||obj.imdb_id))||ctx.imdbId||(md.external_ids&&md.external_ids.imdb_id));return{md:md,namespace:ns,season:season,episode:episode,imdbId:imdb,aliases:aliases(md)}}
function headers(ref,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"text/html,application/json,*/*","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function jsonGet(url,ref){try{var r=await g.fetch(url,{headers:headers(ref||c.base+"/","application/json,text/plain,*/*")});if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function textPayload(url,ref){try{var r=await g.fetch(url,{headers:headers(ref||c.base+"/")});if(!r||!r.ok)return null;return{body:await r.text(),url:r.url||url}}catch(_e){return null}}
function titleScore(row,titles){var t=norm(row&&row.title),best=-1;if(!t)return best;for(var i=0;i<titles.length;i++){var q=norm(titles[i]);if(!q)continue;if(t===q)best=Math.max(best,300);else if(t.indexOf(q)>=0||q.indexOf(t)>=0)best=Math.max(best,170);else{var words=s(titles[i]).toLowerCase().split(/[^a-z0-9]+/),hits=0;for(var j=0;j<words.length;j++){var w=norm(words[j]);if(w.length>=3&&t.indexOf(w)>=0)hits++}best=Math.max(best,hits*18)}}return best}
function chooseAnime(data,titles){var rows=arr(data&&data.data).map(function(row){return{row:row,score:titleScore(row,titles)}}).filter(function(x){return x.score>=36&&s(x.row&&x.row.session)});rows.sort(function(a,b){return b.score-a.score});return rows.length?rows[0].row:null}
function chooseEpisode(data,target){var rows=arr(data&&data.data),want=Number(target);for(var i=0;i<rows.length;i++){if(Number(rows[i]&&rows[i].episode)===want&&s(rows[i]&&rows[i].session))return rows[i]}return null}
function pageHint(data,target){var per=Number(data&&(data.per_page||data.perPage))||0,last=Number(data&&(data.last_page||data.lastPage))||0;if(!per)return 0;var page=Math.max(1,Math.ceil(Number(target)/per));if(last)page=Math.min(page,last);return page}
async function resolveEpisode(animeSession,target){var seen={},pages=[1],page=1;while(pages.length&&Object.keys(seen).length<Math.max(1,Number(c.maxPages)||4)){page=pages.shift();if(seen[page])continue;seen[page]=1;var url=c.base+"/api?m=release&id="+encodeURIComponent(animeSession)+"&sort=episode_asc&page="+encodeURIComponent(String(page)),data=await jsonGet(url,c.base+"/");if(!data)continue;var hit=chooseEpisode(data,target);if(hit)return hit;var hinted=pageHint(data,target);if(hinted&&!seen[hinted])pages.unshift(hinted);var cur=Number(data.current_page||data.currentPage||page)||page,last=Number(data.last_page||data.lastPage)||0;if((!last||cur<last)&&!seen[cur+1])pages.push(cur+1)}return null}
function iframeUrls(html,base){var out=[],seen={},re=/<(?:iframe|source|video)\b[^>]*(?:data-src|src)\s*=\s*["']([^"']+)["'][^>]*>/gi,m;while((m=re.exec(s(html)))&&out.length<12){var u=abs(m[1],base);if(u&&/^https?:/i.test(u)&&!seen[u]){seen[u]=1;out.push(u)}}var re2=/\bdata-src\s*=\s*["']([^"']+)["']/gi;while((m=re2.exec(s(html)))&&out.length<12){var u2=abs(m[1],base);if(u2&&/^https?:/i.test(u2)&&!seen[u2]){seen[u2]=1;out.push(u2)}}return out}
function decodeEscapes(v){return s(v).replace(/\\u00([0-9a-fA-F]{2})/g,function(_m,h){return String.fromCharCode(parseInt(h,16))}).replace(/\\x([0-9a-fA-F]{2})/g,function(_m,h){return String.fromCharCode(parseInt(h,16))}).replace(/\\\//g,"/")}
function directHls(text){var body=decodeEscapes(text),m=body.match(/https?:\/\/[^"'\\\s<>]+\.m3u8(?:\?[^"'\\\s<>]*)?/i);return m?s(m[0]):""}
function quoted(src,pos){while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;var q=src.charAt(pos);if(q!=="'"&&q!=='"')return null;var out="",i=pos+1;while(i<src.length){var ch=src.charAt(i++);if(ch===q)return{value:out,end:i};if(ch!=="\\"){out+=ch;continue}if(i>=src.length)return null;var e=src.charAt(i++);if(e==="x"&&/^[0-9a-fA-F]{2}$/.test(src.slice(i,i+2))){out+=String.fromCharCode(parseInt(src.slice(i,i+2),16));i+=2;continue}if(e==="u"&&/^[0-9a-fA-F]{4}$/.test(src.slice(i,i+4))){out+=String.fromCharCode(parseInt(src.slice(i,i+4),16));i+=4;continue}var map={n:"\n",r:"\r",t:"\t",b:"\b",f:"\f",v:"\v","0":"\0"};out+=Object.prototype.hasOwnProperty.call(map,e)?map[e]:e}return null}
function integer(src,pos){while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;var m=src.slice(pos).match(/^\d+/);return m?{value:Number(m[0]),end:pos+m[0].length}:null}
function comma(src,pos){while(pos<src.length&&/\s/.test(src.charAt(pos)))pos++;return src.charAt(pos)===","?pos+1:-1}
function enc(n,base){var chars="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",out="";if(n===0)return"0";while(n>0){out=chars.charAt(n%base)+out;n=Math.floor(n/base)}return out}
function reEscape(v){return s(v).replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}
function unpackOne(src){var marker="eval(function(p,a,c,k,e",at=src.indexOf(marker);if(at<0)return"";var call=src.indexOf("}(",at);if(call<0||call-at>12000)return"";var p=quoted(src,call+2);if(!p||p.value.length>200000)return"";var pos=comma(src,p.end);if(pos<0)return"";var radix=integer(src,pos);if(!radix||radix.value<2||radix.value>62)return"";pos=comma(src,radix.end);if(pos<0)return"";var count=integer(src,pos);if(!count||count.value<1||count.value>4096)return"";pos=comma(src,count.end);if(pos<0)return"";var table=quoted(src,pos);if(!table)return"";var tail=src.slice(table.end,table.end+80);if(!/^\s*\.split\(\s*["']\|["']\s*\)/.test(tail))return"";var words=table.value.split("|"),decoded=p.value;for(var i=Math.min(count.value,words.length)-1;i>=0;i--){if(!words[i])continue;var token=enc(i,radix.value);decoded=decoded.replace(new RegExp("\\b"+reEscape(token)+"\\b","g"),words[i])}return decoded}
function unpackHls(html){var body=s(html),direct=directHls(body);if(direct)return direct;for(var layer=0;layer<3;layer++){body=unpackOne(body);if(!body)break;direct=directHls(body);if(direct)return direct}return""}
async function resolveEmbed(url,referer){var payload=await textPayload(url,referer);if(!payload)return null;var hls=unpackHls(payload.body);if(!hls){var nested=iframeUrls(payload.body,payload.url);for(var i=0;i<Math.min(nested.length,2);i++){var next=await textPayload(nested[i],payload.url);if(!next)continue;hls=unpackHls(next.body);if(hls)return{url:hls,referer:next.url}}return null}return{url:hls,referer:payload.url}}
async function mappedIdentity(q){var title="",episode=q.episode;if(q.namespace==="tv"){if(!/^tt\d+$/i.test(q.imdbId))return null;var map=await jsonGet(c.mapping+"?id="+encodeURIComponent(q.imdbId)+"&s="+encodeURIComponent(String(q.season))+"&e="+encodeURIComponent(String(q.episode)),c.base+"/");if(!map||!map.mal_id)return null;episode=Number(map.mal_episode)||q.episode;title=s(map.anime_title);if(!title){var mal=await jsonGet(c.jikan+encodeURIComponent(String(map.mal_id)),c.base+"/");title=s(mal&&mal.data&&(mal.data.title_english||mal.data.title||mal.data.title_japanese))}return{title:title,episode:episode,malId:Number(map.mal_id)||0}}title=s(q.md.title||q.md.original_title||q.aliases[0]);return title?{title:title,episode:1,malId:0}:null}
async function resolve(args){var q=req(args);if(!q)return null;var mapped=await mappedIdentity(q);if(!mapped||!mapped.title)return[];var titles=[mapped.title].concat(q.aliases),queries=[],seen={};for(var i=0;i<titles.length&&queries.length<4;i++){var x=s(titles[i]);if(!x||seen[x])continue;seen[x]=1;queries.push(x)}var anime=null,searchRef=c.base+"/";for(var j=0;j<queries.length;j++){var searchUrl=c.base+"/api?m=search&l=8&q="+encodeURIComponent(queries[j]),data=await jsonGet(searchUrl,searchRef);anime=chooseAnime(data,titles);if(anime){searchRef=searchUrl;break}}if(!anime)return[];var animeSession=s(anime.session),episode=await resolveEpisode(animeSession,mapped.episode);if(!episode)return[];var episodeSession=s(episode.session),playUrl=c.base+"/play/"+encodeURIComponent(animeSession)+"/"+encodeURIComponent(episodeSession),play=await textPayload(playUrl,searchRef);if(!play)return[];var embeds=iframeUrls(play.body,play.url);for(var k=0;k<embeds.length;k++){var media=await resolveEmbed(embeds[k],play.url);if(!media||!media.url)continue;var ref=media.referer||embeds[k],h=headers(ref,"*/*"),o=origin(ref);if(o)h.Origin=o;return[{name:c.name,title:c.name+" · "+mapped.title+" · E"+mapped.episode,url:media.url,quality:"Multi",type:"m3u8",provider:c.provider,headers:h}]}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAnimePaheRuntimeV1)return false;var next=o[k],fn=async function(){var q=req(arguments);if(!q)return await next.apply(this,arguments);try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioAnimePaheRuntimeV1=true;fn.__niakvioPrevious=next;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://animepahe.pw",
        "mapping": "https://id-mapping-api-malid.hf.space/api/resolve",
        "jikan": "https://api.jikan.moe/v4/anime/",
        "provider": "animepahe",
        "name": "AnimePahe",
        "maxPages": 4,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3",
    }
    cfg.update(dict(options or {}))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtime": cfg,
            "identity": "core-tmdb-external-id-to-mal-to-animepahe-session-episode-session-kwik-hls",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "packedJavascriptExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
