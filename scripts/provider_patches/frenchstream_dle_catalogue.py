#!/usr/bin/env python3
"""Append an exact Frenchstream DLE search/detail/player adapter."""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_FRENCHSTREAM_DLE_CATALOGUE_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "hubUrl": str(cfg.get("hub_url") or "https://www.fstream.org/").rstrip("/") + "/",
        "fallbackBase": str(cfg.get("base_url") or "https://fs16.lol").rstrip("/"),
        "providerName": str(cfg.get("provider_name") or "Frenchstream"),
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return ""}}
function args(a){var q=a[0]&&typeof a[0]==="object"?Object.assign({},a[0]):{tmdbId:a[0],mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||"movie").toLowerCase();return q}
async function request(url,kind,referer,method,body){var headers={Accept:kind==="json"?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5"};if(referer){headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_){}}if(body)headers["Content-Type"]="application/x-www-form-urlencoded; charset=UTF-8";try{var r=await g.fetch(url,{method:method||"GET",headers:headers,body:body||undefined,redirect:"follow",credentials:"include"});if(!r||!r.ok)return null;return {url:s(r.url||url),body:kind==="json"?await r.json():await r.text()}}catch(_){return null}}
async function meta(q){var title=s(q.title||q.name||q.label).replace(/\s*\(\d{4}\)\s*$/,"");var year=Number(q.year)||0;if(!title&&q.tmdbId){var type=q.mediaType==="tv"?"tv":"movie",r=await request("https://api.themoviedb.org/3/"+type+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","json");if(r&&r.body){title=s(r.body.title||r.body.name);year=Number(s(r.body.release_date||r.body.first_air_date).slice(0,4))||year}}return {title:title,year:year}}
async function base(){var hub=await request(c.hubUrl,"text",c.hubUrl);if(hub){var m=/(?:href=["'])?(https:\/\/fs\d+\.[a-z0-9.-]+)\/?/i.exec(s(hub.body));if(m)return m[1].replace(/\/$/,"")}return c.fallbackBase}
function score(text,m){var n=norm(text),t=norm(m.title),v=0;if(t&&n.indexOf(t)>=0)v+=100;t.split(" ").filter(function(x){return x.length>2}).forEach(function(x){if(n.indexOf(x)>=0)v+=8});if(m.year&&n.indexOf(String(m.year))>=0)v+=20;return v}
function detailLinks(html,root,m){var out=[],seen={},text=s(html),patterns=[/<a\b([^>]*)href=["']([^"']*(?:newsid=\d+|\/\d+[^"']*))["']([^>]*)>([\s\S]*?)<\/a>/gi,/(?:onclick=["'][^"']*location(?:\.href)?\s*=\s*\\?["'])([^"'\\]+)(?:\\?["'])/gi],x;while((x=patterns[0].exec(text))!==null){var attrs=s(x[1])+" "+s(x[3]),inner=s(x[4]).replace(/<[^>]+>/g," "),label=attrs+" "+inner,u=abs(x[2],root);if(u&&score(label,m)>20&&!seen[u]){seen[u]=1;out.push({url:u,score:score(label,m)})}}while((x=patterns[1].exec(text))!==null){var u2=abs(x[1],root);if(u2&&!seen[u2]){var near=text.slice(Math.max(0,x.index-500),Math.min(text.length,x.index+700));if(score(near,m)>20){seen[u2]=1;out.push({url:u2,score:score(near,m)})}}}return out.sort(function(a,b){return b.score-a.score}).map(function(v){return v.url})}
function players(html,baseUrl){var text=s(html),out=[],seen={};function add(v){var u=abs(v,baseUrl);if(!u||seen[u])return;if(!/(?:embed|player|watch|stream|video|vidzy|fsvid|uqload|voe|vidmoly|sibnet|dailymotion|\.m3u8|\.mp4|\/e\/|\/v\/)/i.test(u))return;seen[u]=1;out.push(u)}var patterns=[/(?:data-embed|data-src|data-url|data-link|src|href)=["']([^"']+)["']/gi,/(?:file|source|url|embedUrl|embed_url)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s]+(?:m3u8|mp4|embed|player|watch|stream)[^"'<>\s]*)/gi],m;for(var i=0;i<patterns.length;i++)while((m=patterns[i].exec(text))!==null)add(m[1]);return out}
function unique(values){var out=[],seen={};values.forEach(function(v){v=s(v);if(v&&!seen[v]){seen[v]=1;out.push(v)}});return out}
async function recover(q){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return [];var m=await meta(q);if(!m.title)return [];var root=await base(),searches=[];var post=await request(root+"/engine/ajax/search.php","text",root+"/","POST","query="+encodeURIComponent(m.title)+"&page=1");if(post)searches.push(post);var get=await request(root+"/?do=search&subaction=search&story="+encodeURIComponent(m.title),"text",root+"/");if(get)searches.push(get);var links=[];searches.forEach(function(r){links=links.concat(detailLinks(r.body,r.url||root+"/",m))});links=unique(links).slice(0,6);var streams=[];for(var i=0;i<links.length&&streams.length<12;i++){var detail=await request(links[i],"text",root+"/");if(!detail||score(detail.body,m)<20)continue;var urls=players(detail.body,detail.url);for(var j=0;j<urls.length;j++){var u=urls[j];streams.push({name:c.providerName+(streams.length?" #"+(streams.length+1):""),title:c.providerName+" - "+m.title,url:u,quality:"HD",language:"fr",isDirect:/\.(?:m3u8|mp4|mpd)(?:[?#]|$)/i.test(u),headers:{Referer:detail.url,Origin:root}})}if(streams.length)break}return streams}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__frenchstreamDle)return false;var old=o[k];var wrap=async function(){var native=[];try{native=await old.apply(this,arguments)}catch(_){}if(Array.isArray(native)&&native.length)return native;var recovered=await recover(args(arguments));return recovered.length?recovered:(Array.isArray(native)?native:[])};wrap.__frenchstreamDle=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
