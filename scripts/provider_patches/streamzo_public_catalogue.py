#!/usr/bin/env python3
"""Append an exact StreamZo public catalogue/player adapter."""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_STREAMZO_PUBLIC_CATALOGUE_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "baseUrl": str(cfg.get("base_url") or "https://streamzo.fr").rstrip("/"),
        "providerName": str(cfg.get("provider_name") or "StreamZo"),
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return ""}}
function args(a){var q=a[0]&&typeof a[0]==="object"?Object.assign({},a[0]):{tmdbId:a[0],mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||"movie").toLowerCase();return q}
async function request(url,kind,referer,extra){var headers=Object.assign({Accept:kind==="json"?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5"},extra||{});if(referer){headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_){}}try{var r=await g.fetch(url,{headers:headers,redirect:"follow"});if(!r||!r.ok)return null;return {url:s(r.url||url),body:kind==="json"?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
async function meta(q){var title=s(q.title||q.name||q.label).replace(/\s*\(\d{4}\)\s*$/,"");var year=Number(q.year)||0;if(!title&&q.tmdbId){var type=q.mediaType==="tv"?"tv":"movie",r=await request("https://api.themoviedb.org/3/"+type+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","json");if(r&&r.body){title=s(r.body.title||r.body.name);year=Number(s(r.body.release_date||r.body.first_air_date).slice(0,4))||year}}return {title:title,year:year}}
function scoreText(text,m){var n=norm(text),t=norm(m.title),score=0;if(t&&n.indexOf(t)>=0)score+=100;t.split(" ").filter(function(x){return x.length>2}).forEach(function(x){if(n.indexOf(x)>=0)score+=8});if(m.year&&n.indexOf(String(m.year))>=0)score+=20;return score}
function detailLinks(html,base,m){var rows=[],re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(s(html)))!==null){var attrs=s(x[1])+" "+s(x[3]),inner=s(x[4]).replace(/<[^>]+>/g," "),label=attrs+" "+inner,u=abs(x[2],base);if(u&&scoreText(label,m)>20)rows.push({url:u,score:scoreText(label,m)})}return rows.sort(function(a,b){return b.score-a.score}).map(function(x){return x.url})}
function pageData(html,base){var text=s(html),id="",embed="",m;m=/\bdata-film-id=["'](\d+)["']/i.exec(text);if(m)id=m[1];m=/\bdata-embed=["']([^"']+)["']/i.exec(text);if(m)embed=abs(m[1],base);var urls=[],seen={};function add(v){var u=abs(v,base);if(!u||seen[u])return;seen[u]=1;urls.push(u)}if(embed)add(embed);var re=/(?:data-embed|data-src|data-url|src|href)=["']([^"']+)["']/gi;while((m=re.exec(text))!==null){if(/(?:\/embed\/|player|watch|stream|\.m3u8|\.mp4)/i.test(m[1]))add(m[1])}return {id:id,urls:urls}}
function mirrorUrls(value,base,out){out=out||[];if(value==null)return out;if(typeof value==="string"){if(/^(?:https?:\/\/|\/)/i.test(value)&&/(?:embed|player|watch|stream|video|\.m3u8|\.mp4|\/e\/|\/v\/)/i.test(value))out.push(abs(value,base));return out}if(Array.isArray(value)){value.forEach(function(v){mirrorUrls(v,base,out)});return out}if(typeof value==="object"){Object.keys(value).forEach(function(k){mirrorUrls(value[k],base,out)})}return out}
function unique(values){var out=[],seen={};values.forEach(function(v){v=s(v);if(v&&!seen[v]){seen[v]=1;out.push(v)}});return out}
async function recover(q){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return [];var m=await meta(q);if(!m.title)return [];var candidates=[c.baseUrl+"/"+slug(m.title)],searches=[c.baseUrl+"/?s="+encodeURIComponent(m.title),c.baseUrl+"/search?q="+encodeURIComponent(m.title)];for(var i=0;i<searches.length;i++){var sr=await request(searches[i],"text",c.baseUrl+"/");if(sr)candidates=candidates.concat(detailLinks(sr.body,sr.url,m).slice(0,5))}candidates=unique(candidates);var streams=[];for(var j=0;j<candidates.length&&streams.length<12;j++){var page=await request(candidates[j],"text",c.baseUrl+"/");if(!page||scoreText(page.body,m)<20)continue;var data=pageData(page.body,page.url);var urls=data.urls.slice();if(data.id){var mirrors=await request(c.baseUrl+"/api/mirrors/film/"+encodeURIComponent(data.id),"json",page.url);if(mirrors)urls=urls.concat(mirrorUrls(mirrors.body,c.baseUrl+"/",[]))}urls=unique(urls);for(var k=0;k<urls.length;k++){var u=urls[k];streams.push({name:c.providerName+(streams.length?" #"+(streams.length+1):""),title:c.providerName+" - "+m.title,url:u,quality:"HD",language:"fr",isDirect:/\.(?:m3u8|mp4|mpd)(?:[?#]|$)/i.test(u),headers:{Referer:page.url,Origin:c.baseUrl}})}if(streams.length)break}return streams}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__streamzoPublic)return false;var old=o[k];var wrap=async function(){var native=[];try{native=await old.apply(this,arguments)}catch(_){}if(Array.isArray(native)&&native.length)return native;var recovered=await recover(args(arguments));return recovered.length?recovered:(Array.isArray(native)?native:[])};wrap.__streamzoPublic=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
