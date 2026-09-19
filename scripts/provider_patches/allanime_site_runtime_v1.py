#!/usr/bin/env python3
"""NiakVIO-owned AllAnime GraphQL runtime.

Current provider chain:
Core TMDB metadata -> api.allanime.day GraphQL search -> exact show/mode ->
episode sourceUrls -> AllAnime clock JSON / direct source / bounded embed crawler.

No upstream JavaScript is embedded or executed. Encrypted `tobeparsed` responses
are decoded with the browser/Node WebCrypto contract when available; otherwise
the runtime fails closed instead of manufacturing a stream.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLANIME.SITE.RUNTIME.V1"
MARKER = "NIAKVIO_ALLANIME_GRAPHQL_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_ALLANIME_GRAPHQL_RUNTIME_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[’'`]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function uniq(v){var out=[],seen={};for(var i=0;i<(v||[]).length;i++){var x=s(v[i]),k=norm(x);if(x&&k&&!seen[k]){seen[k]=1;out.push(x)}}return out}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||x.semanticType||x.canonicalMediaType||x.mediaType||a[1]||"").toLowerCase();
  if(semantic==="tv")semantic="anime";if(semantic!=="anime")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
  if(!/^\d+$/.test(id))return[];
  return{tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||x.tmdbMetadata||x.fixtureMetadata||null}
}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var m=projected(q.metadata);if(!m)try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:"tv",tmdbNamespace:"tv"});m=projected(z)}}catch(_e){}if(!m)return null;
  var vals=[m.name,m.title,m.original_name,m.original_title],alt=m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);
  if(Array.isArray(alt))for(var i=0;i<alt.length;i++)vals.push(alt[i]&&(alt[i].title||alt[i].name));
  var counts={};if(Array.isArray(m.seasons))for(var j=0;j<m.seasons.length;j++){var r=m.seasons[j]||{},sn=Number(r.season_number),ec=Number(r.episode_count);if(sn>0&&ec>0)counts[sn]=ec}
  return{title:s(m.name||m.title||m.original_name||m.original_title),aliases:uniq(vals).slice(0,8),seasonCounts:counts}
}
function headers(json){return{"User-Agent":c.ua,"Accept":"application/json, text/plain, */*","Content-Type":json?"application/json":"text/plain","Referer":c.referer,"Origin":c.origin}}
async function jsonPost(query,variables){try{var r=await g.fetch(c.api,{method:"POST",headers:headers(true),body:JSON.stringify({query:query,variables:variables}),redirect:"follow"});if(!r||!r.ok)return null;var raw=await r.text();try{return JSON.parse(raw)}catch(_e){return null}}catch(_e){return null}}
function similarity(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 100;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 78;var aa=a.split(" ").filter(function(x){return x.length>=3}),bb=b.split(" ").filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<aa.length;i++)if(bb.indexOf(aa[i])>=0)hit++;return Math.round(100*hit/Math.max(aa.length,bb.length,1))}
var SEARCH_GQL='query( $search: SearchInput $limit: Int $page: Int $translationType: VaildTranslationTypeEnumType $countryOrigin: VaildCountryOriginEnumType ) { shows( search: $search limit: $limit page: $page translationType: $translationType countryOrigin: $countryOrigin ) { edges { _id name englishName availableEpisodes __typename } }}';
var SOURCE_GQL='query ($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) { episode( showId: $showId translationType: $translationType episodeString: $episodeString ) { episodeString sourceUrls }}';
async function searchOne(title,mode,q){var j=await jsonPost(SEARCH_GQL,{search:{allowAdult:false,allowUnknown:false,query:title},limit:40,page:1,translationType:mode,countryOrigin:"ALL"}),rows=j&&j.data&&j.data.shows&&j.data.shows.edges||[],best=null,bestScore=0;
  for(var i=0;i<rows.length;i++){var r=rows[i]||{},label=s(r.name||r.englishName),sc=similarity(label,title),sm=label.match(/(?:season|saison|\bs)\s*(\d+)/i);if(sm&&q.season)sc+=Number(sm[1])===q.season?25:-20;if(sc>bestScore){bestScore=sc;best=r}}
  return best&&best._id&&bestScore>=48?best:null
}
async function findShow(meta,q,mode){var names=meta.aliases||[meta.title];for(var i=0;i<names.length&&i<6;i++){var r=await searchOne(names[i],mode,q);if(r)return r}if(q.season>1){for(var j=0;j<names.length&&j<3;j++){var r2=await searchOne(names[j]+" Season "+q.season,mode,q);if(r2)return r2}}return null}
function absoluteEpisode(q,meta){var n=q.episode,ok=true;for(var sn=1;sn<q.season;sn++){var ec=Number(meta&&meta.seasonCounts&&meta.seasonCounts[sn]);if(!ec){ok=false;break}n+=ec}return ok?n:q.episode}
function b64Bytes(v){try{var raw=typeof atob==="function"?atob(v):(typeof Buffer!=="undefined"?Buffer.from(v,"base64").toString("binary"):""),a=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)a[i]=raw.charCodeAt(i)&255;return a}catch(_e){return null}}
async function decryptParsed(v){try{var subtle=g&&g.crypto&&g.crypto.subtle;if(!subtle&&typeof crypto!=="undefined")subtle=crypto.subtle;if(!subtle)return null;var bytes=b64Bytes(v);if(!bytes||bytes.length<30)return null;var seed=new TextEncoder().encode("Xot36i3lK3:v1"),keyBytes=await subtle.digest("SHA-256",seed),key=await subtle.importKey("raw",keyBytes,{name:"AES-CTR"},false,["decrypt"]),counter=new Uint8Array(16);counter.set(bytes.slice(1,13),0);counter[15]=2;var ct=bytes.slice(13,bytes.length-16),plain=await subtle.decrypt({name:"AES-CTR",counter:counter,length:32},key,ct),raw=new TextDecoder().decode(plain),j=JSON.parse(raw);return j&&j.episode&&j.episode.sourceUrls||j&&j.sourceUrls||null}catch(_e){return null}}
async function sourceRows(showId,mode,ep){var j=await jsonPost(SOURCE_GQL,{showId:showId,translationType:mode,episodeString:String(ep)}),data=j&&j.data;if(data&&data.episode&&Array.isArray(data.episode.sourceUrls))return data.episode.sourceUrls;if(data&&data.tobeparsed)return await decryptParsed(data.tobeparsed)||[];return[]}
var HEX={"79":"A","7a":"B","7b":"C","7c":"D","7d":"E","7e":"F","7f":"G","70":"H","71":"I","72":"J","73":"K","74":"L","75":"M","76":"N","77":"O","68":"P","69":"Q","6a":"R","6b":"S","6c":"T","6d":"U","6e":"V","6f":"W","60":"X","61":"Y","62":"Z","59":"a","5a":"b","5b":"c","5c":"d","5d":"e","5e":"f","5f":"g","50":"h","51":"i","52":"j","53":"k","54":"l","55":"m","56":"n","57":"o","48":"p","49":"q","4a":"r","4b":"s","4c":"t","4d":"u","4e":"v","4f":"w","40":"x","41":"y","42":"z","08":"0","09":"1","0a":"2","0b":"3","0c":"4","0d":"5","0e":"6","0f":"7","00":"8","01":"9","15":"-","16":".","67":"_","46":"~","02":":","17":"/","07":"?","1b":"#","63":"[","65":"]","78":"@","19":"!","1c":"$","1e":"&","10":"(","11":")","12":"*","13":"+","14":",","03":";","05":"=","1d":"%"};
function decodeSource(v){var x=s(v);if(x.indexOf("--")!==0)return x;var body=x.slice(2),out="";for(var i=0;i+1<body.length;i+=2)out+=HEX[body.slice(i,i+2)]||"";return out.replace(/([^:])\/\//g,"$1/").replace("/clock","/clock.json")}
function quality(v){var m=s(v).match(/\b(2160|1080|720|480)p\b/i);return m?m[1]+"p":"HD"}
function isDirect(u){return /\.(?:m3u8|mp4|mkv|webm|mpd)(?:[?#]|$)/i.test(s(u))||/repackager\.wixmp\.com/i.test(s(u))}
async function clockLinks(path){var u=path;if(!/^https?:/i.test(u))u=c.clockBase+(u.charAt(0)==="/"?u:"/"+u);try{var r=await g.fetch(u,{headers:{"User-Agent":c.ua,"Referer":c.referer,"Accept":"application/json,*/*"},redirect:"follow"});if(!r||!r.ok)return[];var raw=await r.text(),j=JSON.parse(raw),links=j&&j.links||[];return links.map(function(x){return{url:s(x&&(x.link||x.url)),quality:s(x&&(x.resolutionStr||x.quality))}}).filter(function(x){return /^https?:/i.test(x.url)})}catch(_e){return[]}}
async function directPlayable(u,ref){try{var r=await g.fetch(u,{headers:{"User-Agent":c.ua,"Referer":ref||c.referer,"Range":"bytes=0-2047"},redirect:"follow"});if(!r||!r.ok)return"";var ct="";try{ct=s(r.headers&&r.headers.get&&r.headers.get("content-type")).toLowerCase()}catch(_e){}if(Number(r.status)===206||/^(?:video|audio)\//.test(ct)||/application\/(?:octet-stream|x-matroska)/.test(ct))return r.url||u;if(/\.m3u8(?:[?#]|$)/i.test(r.url||u)){var body=await r.text();if(/^#EXTM3U/m.test(body))return r.url||u}return""}catch(_e){return""}}
async function resolveRows(rows,mode,meta,q){var out=[],seen={},lang=mode==="dub"?"English Dub":"VOSTA";for(var i=0;i<rows.length&&out.length<c.maxStreams;i++){var row=rows[i]||{},raw=decodeSource(row.sourceUrl||row.url||""),cand=[];if(!raw)continue;if(/clock(?:\.json)?/i.test(raw)){cand=await clockLinks(raw)}else cand=[{url:raw,quality:row.quality||row.resolutionStr||""}];
    for(var j=0;j<cand.length&&out.length<c.maxStreams;j++){var u=s(cand[j].url);if(!u||seen[u])continue;var final="";if(isDirect(u))final=await directPlayable(u,c.referer);if(!final&&/^https?:/i.test(u))try{if(typeof _crawlDirectMedia==="function"){var crawled=await _crawlDirectMedia([u],c.referer,2);if(Array.isArray(crawled)&&crawled.length){for(var k=0;k<crawled.length&&out.length<c.maxStreams;k++){var cr=crawled[k];if(!cr||!/^https?:/i.test(s(cr.url))||seen[cr.url])continue;seen[cr.url]=1;var x=Object.assign({},cr);x.provider="allanime";x.name="AllAnime | "+lang;x.title=meta.title+" | S"+q.season+"E"+q.episode+" | "+lang;x.language=lang;out.push(x)}}}}catch(_e){}
      if(final&&!seen[final]){seen[final]=1;out.push({name:"AllAnime | "+lang,title:meta.title+" | S"+q.season+"E"+q.episode+" | "+lang,url:final,quality:quality(cand[j].quality||row.sourceName||""),language:lang,provider:"allanime",isDirect:true,headers:{"Referer":c.referer,"User-Agent":c.ua}})}
    }
  }return out
}
async function resolve(a){var q=req(a);if(q===null)return null;if(!q||!q.tmdbId)return[];var meta=await metadata(q);if(!meta||!meta.title)return[];var modes=["sub","dub"],episodes=[q.episode],abs=absoluteEpisode(q,meta);if(abs!==q.episode)episodes.push(abs),out=[];
  for(var mi=0;mi<modes.length&&out.length<c.maxStreams;mi++){var mode=modes[mi],show=await findShow(meta,q,mode);if(!show)continue;for(var ei=0;ei<episodes.length&&out.length<c.maxStreams;ei++){var rows=await sourceRows(show._id,mode,episodes[ei]);if(!rows.length)continue;var got=await resolveRows(rows,mode,meta,q);for(var gi=0;gi<got.length&&out.length<c.maxStreams;gi++)out.push(got[gi]);if(got.length)break}}
  return out
}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"allanime",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg={
        "api":"https://api.allanime.day/api",
        "clockBase":"https://allanime.day",
        "referer":"https://youtu-chan.com/",
        "origin":"https://youtu-chan.com",
        "maxStreams":6,
        "ua":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0",
    }
    cfg.update(dict(options or {}))
    cfg["maxStreams"]=max(1,min(int(cfg.get("maxStreams") or 6),10))
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"allanime-graphql-source-clock-v2",
        "identity":"core-tmdb-aliases-season-episode",
        "semanticLanes":["anime"],
        "runtimeResolverRegistration":True,
        "coreFinalOutputOwnership":True,
        "encryptedSourceSupport":"webcrypto-aes-ctr-fail-closed",
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
