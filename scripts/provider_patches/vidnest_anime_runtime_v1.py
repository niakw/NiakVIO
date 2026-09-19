#!/usr/bin/env python3
"""Vidnest-Anime clean-v3 AniList/API runtime adapter."""
from __future__ import annotations
import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.VIDNEST-ANIME.RUNTIME.V1"
MARKER = "NIAKVIO_VIDNEST_ANIME_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_VIDNEST_ANIME_RUNTIME_V1 */
;(function(g,c){
"use strict";
function s(v){return String(v==null?"":v).trim()}
function req(a){
 var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
 var md=(o&&(o.tmdbMetadata||o.metadata))||ctx.tmdbMetadata||null;if(md&&md.state==="ok"&&md.metadata)md=md.metadata;md=md&&typeof md==="object"?md:{};
 var date=s(md.first_air_date||md.release_date||md.year),season=Number((o&&o.season)!=null?o.season:a[2])||1,episode=Number((o&&o.episode)!=null?o.episode:a[3])||1;
 var prev=0,seasons=Array.isArray(md.seasons)?md.seasons:[];if(season>1){for(var i=0;i<seasons.length;i++){var row=seasons[i]||{};if(Number(row.season_number)>0&&Number(row.season_number)<season)prev+=Number(row.episode_count)||0}}
 return {id:s((o&&(o.tmdbId||o.tmdb_id||o.id))||ctx.tmdbId||f).replace(/^tmdb:/i,"").split(":")[0],title:s(md.name||md.title||md.original_name||md.original_title),year:Number(date.slice(0,4))||0,season:season,episode:episode,absolute:prev+episode,hasPreviousProof:season<=1||prev>0};
}
function headers(){return {"Accept":"application/json,text/plain,*/*","Referer":"https://vidnest.fun/","Origin":"https://vidnest.fun","User-Agent":c.userAgent}}
async function anilist(q){
 var query="query ($search: String, $year: Int) { Media(search: $search, seasonYear: $year, type: ANIME, format_in: [TV, TV_SHORT, MOVIE, OVA, ONA, SPECIAL]) { id title { romaji english native } seasonYear } }";
 try{var r=await g.fetch("https://graphql.anilist.co",{method:"POST",headers:{"Content-Type":"application/json","Accept":"application/json"},body:JSON.stringify({query:query,variables:{search:q.title,year:q.year||null}})});if(!r||!r.ok)return 0;var d=await r.json();return Number(d&&d.data&&d.data.Media&&d.data.Media.id)||0}catch(_e){return 0}
}
async function decrypt(payload){try{var r=await g.fetch(c.decryptUrl,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({encryptedData:payload,passphrase:c.passphrase})});if(!r||!r.ok)return null;var d=await r.json();return d&&!d.error&&d.decrypted?s(d.decrypted):null}catch(_e){return null}}
function sourceRows(data,server,lang,q){
 var ss=data&&Array.isArray(data.sources)?data.sources:data&&Array.isArray(data.streams)?data.streams:[],subs=data&&Array.isArray(data.subtitles)?data.subtitles:[],out=[],seen=Object.create(null);
 for(var i=0;i<ss.length;i++){var row=ss[i]||{},url=s(row.file||row.url||row.src||row.link);if(!/^https?:\/\//i.test(url)||seen[url])continue;seen[url]=1;
   out.push({name:"VidnestAnime "+server+" ["+lang+"]",title:q.title+" - Episode "+q.absolute,url:url,quality:s(row.quality||"Adaptive"),subtitles:subs,headers:row.headers&&typeof row.headers==="object"?row.headers:headers(),provider:"vidnest-anime"});
 }return out;
}
function endpoint(server,id,ep,lang){
 var base=c.apiBase;
 if(server==="hindi")return base+"/animeworld/"+id+"/"+ep+"/server/my%20server";
 if(server==="satoru")return base+"/satoru/"+id+"/"+ep;
 if(server==="miko")return base+"/aniwave/"+id+"/"+ep+"/"+lang+"/wave";
 if(server==="pahe")return base+"/aniwave/"+id+"/"+ep+"/"+lang+"/pahe";
 if(server==="anya")return base+"/aniwave/"+id+"/"+ep+"/"+lang+"/anya";
 return "";
}
async function one(server,id,q,lang){var url=endpoint(server,id,q.absolute,lang);if(!url)return [];try{var r=await g.fetch(url,{headers:headers(),redirect:"follow"});if(!r||!r.ok)return [];var txt=await r.text(),d;try{d=JSON.parse(txt)}catch(_e){return []}
 if(d&&d.encrypted&&d.data){var clear=await decrypt(d.data);if(!clear)return [];try{d=JSON.parse(clear)}catch(_e){return []}}
 return sourceRows(d,server,lang,q);}catch(_e){return []}}
async function resolve(a){
 var q=req(a);if(!/^\d+$/.test(q.id)||!q.title||!q.hasPreviousProof)return [];var aid=await anilist(q);if(!aid)return [];
 var jobs=[one("hindi",aid,q,"sub"),one("satoru",aid,q,"sub")];["miko","pahe","anya"].forEach(function(x){jobs.push(one(x,aid,q,"sub"));jobs.push(one(x,aid,q,"dub"))});
 var all=await Promise.all(jobs),out=[],seen=Object.create(null);for(var i=0;i<all.length;i++)for(var j=0;j<all[i].length;j++){var r=all[i][j];if(!seen[r.url]){seen[r.url]=1;out.push(r)}}return out.slice(0,40);
}
function install(x,k){if(!x||typeof x[k]!=="function"||x[k].__niakvioVidnestAnimeRuntimeV1)return false;var w=async function(){return await resolve(arguments)};w.__niakvioVidnestAnimeRuntimeV1=true;x[k]=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")||ok}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''
def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    payload={
      "apiBase":str(cfg.get("api_base") or "https://backend.vidnest.fun").rstrip("/"),
      "decryptUrl":str(cfg.get("decrypt_url") or "https://aesdec.nuvioapp.space/decrypt"),
      "passphrase":str(cfg.get("passphrase") or "A7kP9mQeXU2BWcD4fRZV+Sg8yN0/M5tLbC1HJQwYe6o="),
      "userAgent":str(cfg.get("user_agent") or "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/137 Mobile Safari/537.36")
    }
    return replace_managed_fix(text,MANAGED_FIX_ID,WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(payload,ensure_ascii=False,separators=(",",":"))),data={"runtime":payload,"identity":"core-title-year-to-anilist","legacyExecutableSeed":False})
if __name__ == "__main__": raise SystemExit("patch module only")
