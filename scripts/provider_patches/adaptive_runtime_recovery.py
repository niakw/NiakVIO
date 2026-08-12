#!/usr/bin/env python3
"""Append a bounded adaptive recovery wrapper driven by runtime observations."""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "providerName": str(cfg.get("provider_name") or "Provider"),
        "baseUrl": str(cfg.get("base_url") or "").rstrip("/"),
        "types": [
            value
            for value in cfg.get("types", ["movie", "tv", "anime"])
            if value in {"movie", "tv", "anime"}
        ],
        "searchPaths": [str(value) for value in cfg.get("search_paths", []) if str(value).strip()],
        "directPaths": [str(value) for value in cfg.get("direct_paths", []) if str(value).strip()],
        "maxPages": max(2, min(int(cfg.get("max_pages", 10)), 24)),
        "maxEmbeds": max(2, min(int(cfg.get("max_embeds", 10)), 24)),
        "maxDepth": max(1, min(int(cfg.get("max_depth", 3)), 4)),
        "timeoutMs": max(2000, min(int(cfg.get("timeout_ms", 9000)), 20000)),
        "blockedHosts": [str(value).lower().lstrip(".") for value in cfg.get("blocked_hosts", [])],
        "blockedPaths": [str(value).lower() for value in cfg.get("blocked_path_patterns", [])],
    }
    if not payload["baseUrl"]:
        raise ValueError("adaptive_runtime_recovery: base_url required")

    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    legacy_index = text.find("/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V")
    if legacy_index >= 0:
        call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', legacy_index)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper")
        text = (text[:legacy_index] + text[end + 2 :]).rstrip()

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var K="8265bd1679663a7ea12ac168da84d2e8";
var J={},C={};
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function n(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return n(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return ""}}
function origin(v){try{return new URL(v).origin}catch(_){return ""}}
function bad(u){try{var x=new URL(u),h=x.hostname.toLowerCase(),p=x.pathname.toLowerCase();if(!/^https?:$/.test(x.protocol))return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;for(var j=0;j<c.blockedPaths.length;j++)if(p.indexOf(c.blockedPaths[j])>=0)return true;return /(?:google-analytics|googletagmanager|cloudflareinsights|telegram\.org\/img|datatracker\.ietf\.org)/i.test(u)||/\.(?:js|css|woff2?|ttf|png|jpe?g|gif|svg)(?:[?#]|$)/i.test(p)}catch(_){return true}}
function mediaType(t){return /(?:application\/(?:vnd\.apple\.mpegurl|x-mpegurl|dash\+xml)|audio\/(?:mpegurl|x-mpegurl)|video\/)/i.test(s(t))}
function media(u,t,b){return !bad(u)&&(/\.(?:m3u8|mp4|mpd|mkv|webm)(?:[?#]|$)/i.test(u)||mediaType(t)||/^\s*#EXTM3U/i.test(s(b)))}
function parseCookies(values){var out={};for(var i=0;i<values.length;i++){var line=s(values[i]),pair=line.split(";",1)[0],p=pair.indexOf("=");if(p>0)out[pair.slice(0,p).trim()]=pair.slice(p+1).trim()}return out}
function saveCookies(u,h){try{var o=origin(u),values=[];if(h&&typeof h.getSetCookie==="function")values=h.getSetCookie()||[];if(!values.length&&h&&typeof h.get==="function"){var one=h.get("set-cookie");if(one)values=[one]}var next=parseCookies(values),cur=J[o]||{};Object.keys(next).forEach(function(k){cur[k]=next[k]});J[o]=cur}catch(_){}}
function cookieHeader(u,ref){var bag=Object.assign({},J[origin(ref)]||{},J[origin(u)]||{}),parts=[];Object.keys(bag).forEach(function(k){parts.push(k+"="+bag[k])});return parts.join("; ")}
function hdr(ref,target){var h={Referer:ref,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5"};try{h.Origin=new URL(ref).origin}catch(_){}var ck=cookieHeader(target||ref,ref);if(ck)h.Cookie=ck;return h}
function wait(ms){return new Promise(function(resolve){setTimeout(resolve,ms)})}
async function req(u,json,ref,attempt){attempt=attempt||0;var key=(json?"j":"t")+"|"+u+"|"+s(ref);if(C[key])return C[key];var a=new AbortController(),t=setTimeout(function(){a.abort()},c.timeoutMs),headers=Object.assign({Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,video/*,*/*"},ref?hdr(ref,u):{}),r=null;try{try{r=await g.fetch(u,{redirect:"follow",headers:headers,signal:a.signal})}catch(e){if(headers.Cookie){delete headers.Cookie;r=await g.fetch(u,{redirect:"follow",headers:headers,signal:a.signal})}else throw e}if(!r)return null;saveCookies(r.url||u,r.headers);if(r.status===429&&attempt<1){clearTimeout(t);await wait(900);return req(u,json,ref,attempt+1)}if(!r.ok)return null;var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",body=null;if(json){body=await r.json()}else if(media(finalUrl,type,"")){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,status:r.status};C[key]=result;return result}catch(_){return null}finally{clearTimeout(t)}}
function args(a){var q=a[0]&&typeof a[0]==="object"?Object.assign({},a[0]):{tmdbId:a[0],mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||"movie").toLowerCase();return q}
async function meta(q){var title=s(q.title||q.name||q.label),year=Number(q.year)||0;if(!title&&q.tmdbId){var k=q.mediaType==="tv"?"tv":"movie",d=await req("https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+K+"&language=fr-FR",true);if(d&&d.body){title=s(d.body.title||d.body.name);year=Number(s(d.body.release_date||d.body.first_air_date).slice(0,4))||year}}return {title:title.replace(/\s*\(\d{4}\)\s*$/,"") ,year:year}}
function urls(html,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||bad(u)||seen[u])return;seen[u]=1;out.push(u)}var t=s(html),res=[/(?:href|src|data-src|data-url|data-embed|data-player|data-video|data-link)=["']([^"']+)["']/gi,/(?:file|source|url|embedUrl|embed_url|contentUrl|content_url|playlist)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s]+(?:m3u8|mp4|mpd|mkv|webm)(?:\?[^"'<>\s]*)?)/gi],m;for(var i=0;i<res.length;i++)while((m=res[i].exec(t))!==null)add(m[1]);return out}
function score(u,m,q){var z=n(u),w=n(m.title),v=0;if(w&&z.indexOf(w)>=0)v+=80;w.split(" ").filter(function(x){return x.length>2}).forEach(function(x){if(z.indexOf(x)>=0)v+=8});if(m.year&&z.indexOf(String(m.year))>=0)v+=20;if(q.mediaType==="tv"&&new RegExp("(?:s|saison)[^0-9]*0?"+(Number(q.season)||1)+".*(?:e|ep|episode)[^0-9]*0?"+(Number(q.episode)||1),"i").test(z))v+=60;return v}
function playerScore(u,parent){if(media(u,"",""))return 1000;try{var a=new URL(u),b=new URL(parent),v=0;if(a.origin!==b.origin)v+=80;if(/(?:embed|player|video|watch|stream|playlist|\/e\/|\/v\/)/i.test(a.pathname+a.search))v+=160;if(/(?:dailymotion|lecteurvideo|sharecloudy|sibnet|vidmoly|vidzy|streamtape|sendvid|vidoza|uqload|voe)/i.test(a.hostname))v+=220;return v}catch(_){return -1}}
function unique(rows){var out=[],seen={};for(var i=0;i<rows.length;i++){var row=rows[i],u=s(row&&row.url);if(!u||seen[u])continue;seen[u]=1;out.push(row)}return out}
function normalizedPlayers(body,page){var out=[],seen={};function add(u){u=abs(u,page);if(!u||bad(u)||seen[u])return;seen[u]=1;out.push(u)}var h="";try{h=new URL(page).hostname.toLowerCase()}catch(_){}if(/(?:^|\.)dailymotion\.com$/.test(h)){var t=s(body),res=[/(?:videoId|video_id|video)\s*["']?\s*[:=]\s*["']([a-zA-Z0-9]+)["']/g,/\/video\/([a-zA-Z0-9]+)/g],m;for(var i=0;i<res.length;i++)while((m=res[i].exec(t))!==null)add("https://www.dailymotion.com/embed/video/"+m[1])}return out}
async function resolve(u,ref,depth,seen){if(depth>c.maxDepth||bad(u))return [];seen=seen||{};var requested=u;if(seen[requested])return [];seen[requested]=1;if(media(requested,"",""))return [{url:requested,referer:ref||requested}];var doc=await req(requested,false,ref);if(!doc)return [];var page=doc.url||requested;if(seen[page]&&page!==requested)return [];seen[page]=1;if(media(page,doc.type,doc.body))return [{url:page,referer:ref||requested}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));xs=Array.from(new Set(xs)).sort(function(a,b){return playerScore(b,page)-playerScore(a,page)});var out=[];for(var d=0;d<xs.length;d++)if(media(xs[d],"",""))out.push({url:xs[d],referer:page});for(var i=0;i<xs.length&&i<c.maxEmbeds&&out.length<c.maxEmbeds;i++){if(media(xs[i],"",""))continue;var ps=playerScore(xs[i],page);if(ps<80)continue;var r=await resolve(xs[i],page,depth+1,seen);out=out.concat(r)}return unique(out).slice(0,c.maxEmbeds)}
async function recover(q){if(c.types.indexOf(q.mediaType)<0)return [];var m=await meta(q);if(!m.title)return [];var cand=[],sl=slug(m.title),sharedSeen={};for(var i=0;i<c.directPaths.length;i++)cand.push(abs(c.directPaths[i].replace(/\{slug\}/g,sl).replace(/\{id\}/g,q.tmdbId).replace(/\{year\}/g,String(m.year||"")),c.baseUrl+"/"));for(var j=0;j<c.searchPaths.length;j++){var u=abs(c.searchPaths[j].replace(/\{query\}/g,encodeURIComponent(m.title)).replace(/\{slug\}/g,sl).replace(/\{id\}/g,q.tmdbId),c.baseUrl+"/"),doc=await req(u,false,c.baseUrl+"/");if(doc&&doc.body)cand=cand.concat(urls(doc.body,doc.url||u).sort(function(a,b){return score(b,m,q)-score(a,m,q)}).slice(0,c.maxPages))}cand=Array.from(new Set(cand)).sort(function(a,b){return score(b,m,q)-score(a,m,q)}).slice(0,c.maxPages);var found=[];for(var k=0;k<cand.length&&found.length<c.maxEmbeds;k++){var r=await resolve(cand[k],c.baseUrl+"/",0,sharedSeen);found=found.concat(r)}return unique(found).slice(0,c.maxEmbeds).map(function(row,i){return {name:c.providerName+(i?" #"+(i+1):""),title:c.providerName+" - "+m.title,url:row.url,quality:"HD",headers:hdr(row.referer||c.baseUrl+"/",row.url),isDirect:media(row.url,"","")}})}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioAdaptive)return false;var old=o[k];var w=async function(){var native=[];try{native=await old.apply(this,arguments)}catch(_){}if(Array.isArray(native)&&native.some(function(x){return x&&media(s(x.url),"","")}))return native;var r=await recover(args(arguments));return r.length?r:(Array.isArray(native)?native:[])};w.__nuvioAdaptive=true;o[k]=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
