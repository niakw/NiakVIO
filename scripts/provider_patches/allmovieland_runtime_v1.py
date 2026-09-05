#!/usr/bin/env python3
"""Clean Provider-v3 AllMovieLand runtime from structured route knowledge only."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ALLMOVIELAND.RUNTIME.V1"
MARKER = "NIAKVIO_ALLMOVIELAND_RUNTIME_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    sites = []
    for raw in cfg.get("sites") or ["https://allmovieland.to", "https://allmovieland.art"]:
        value = str(raw or "").strip().rstrip("/")
        if value.startswith(("http://", "https://")) and value not in sites:
            sites.append(value)
    payload = {"sites": sites[:4], "name": "AllMovieLand", "provider": "allmovieland"}
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    wrapper = r'''
/* NIAKVIO_ALLMOVIELAND_RUNTIME_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return""}}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function q(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||{};if(md&&md.state==="ok"&&md.metadata)md=md.metadata;var type=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(type!=="movie"&&type!=="tv")return null;var title=s((o&&o.title)||md.title||md.name||ctx.title),date=s(md.release_date||md.first_air_date||(o&&o.year)||ctx.year),year=Number(date.slice(0,4))||Number(o&&o.year)||0;return{type:type,title:title,year:year,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
function headers(ref){var h={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3","Accept":"text/html,application/json,text/plain,*/*"};if(ref)h.Referer=ref;return h}
async function text(url,init){var o=Object.assign({},init||{});o.headers=Object.assign({},headers(o.referer||""),o.headers||{});delete o.referer;var r=await g.fetch(url,o);if(!r||!r.ok)throw new Error("allmovieland_http_"+String(r&&r.status||0));return{body:await r.text(),url:r.url||url}}
function visible(v){return s(v).replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ")}
function score(title,want,year){var a=norm(title),b=norm(want);if(!a||!b)return 0;var n=a===b?240:(a.indexOf(b)>=0||b.indexOf(a)>=0?120:0);for(var t of b.split(" "))if(t.length>=3&&a.indexOf(t)>=0)n+=16;if(year&&s(title).indexOf(String(year))>=0)n+=30;return n}
function candidates(html,base,meta){var out=[],re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html))&&out.length<100){var u=abs(m[1],base),t=visible(m[2]);if(!u||!t)continue;var sc=score(t,meta.title,meta.year);if(sc>=32)out.push({url:u,score:sc})}out.sort(function(a,b){return b.score-a.score});var seen={},urls=[];for(var i=0;i<out.length&&urls.length<6;i++){if(!seen[out[i].url]){seen[out[i].url]=1;urls.push(out[i].url)}}return urls}
function playerData(html){var d=/const\s+AwsIndStreamDomain\s*=\s*["']([^"']+)["']/i.exec(html),id=/(?:\bsrc\s*:\s*|data-src=["'])["']?([^"'\s,;}]+)["']?/i.exec(html);return{domain:d?s(d[1]).replace(/\/$/,""):"",id:id?s(id[1]):""}}
function p3(html){var m=/(?:let|const|var)\s+(?:p3|playlist)\s*=\s*(\{[\s\S]*?\})\s*;/i.exec(html);if(!m)return null;var raw=m[1].replace(/\\\//g,"/");try{return JSON.parse(raw)}catch(_e){var file=/["']?file["']?\s*:\s*["']([^"']+)/i.exec(raw),key=/["']?key["']?\s*:\s*["']([^"']+)/i.exec(raw);return file&&key?{file:file[1],key:key[1]}:null}}
function json(v){try{return JSON.parse(s(v).replace(/,\s*\]/g,"]"))}catch(_e){return null}}
function files(data,meta){if(!Array.isArray(data))return[];if(meta.type==="movie")return data.filter(function(x){return x&&x.file}).slice(0,8);var season=data.find(function(x){var n=/season\s*(\d+)/i.exec(s(x&&x.title));return String(x&&x.id)===String(meta.season)||(n&&Number(n[1])===meta.season)})||data[meta.season-1];var eps=season&&season.folder;if(!Array.isArray(eps))return[];var ep=eps.find(function(x){var n=/episode\s*(\d+)/i.exec(s(x&&x.title));return String(x&&x.episode)===String(meta.episode)||(n&&Number(n[1])===meta.episode)})||eps[meta.episode-1];return ep&&Array.isArray(ep.folder)?ep.folder.filter(function(x){return x&&x.file}).slice(0,8):[]}
function quality(v){var m=s(v).match(/(2160|1080|720|480|360)p?/i);return m?m[1]+"p":""}
async function resolveDetail(url,meta){var detail=await text(url),pd=playerData(detail.body);if(!pd.domain||!pd.id)return[];var embed=pd.domain+"/play/"+encodeURIComponent(pd.id),page=await text(embed,{referer:url}),cfg=p3(page.body);if(!cfg||!cfg.file||!cfg.key)return[];var listUrl=/^https?:/i.test(s(cfg.file))?s(cfg.file):abs(s(cfg.file),pd.domain),list=await text(listUrl,{method:"POST",referer:embed,headers:{"X-CSRF-TOKEN":s(cfg.key)}}),rows=files(json(list.body),meta),out=[];for(var i=0;i<rows.length&&out.length<8;i++){var f=s(rows[i].file).replace(/^~/,""),u=pd.domain+"/playlist/"+encodeURIComponent(f)+".txt";try{var r=await text(u,{method:"POST",referer:embed,headers:{"X-CSRF-TOKEN":s(cfg.key)}}),media=s(r.body);if(!/^https?:\/\//i.test(media))continue;var ql=quality(rows[i].title);var row={name:c.name,title:c.name,url:media,provider:c.provider,headers:{Referer:pd.domain+"/","User-Agent":headers()["User-Agent"]}};if(ql)row.quality=ql;out.push(row)}catch(_e){}}return out}
async function run(args){var meta=q(args);if(!meta||!meta.title)return[];for(var b=0;b<c.sites.length;b++){var base=c.sites[b];try{var search=base+"/index.php?story="+encodeURIComponent(meta.title)+"&do=search&subaction=search",page=await text(search),urls=candidates(page.body,page.url||search,meta);for(var i=0;i<urls.length;i++){var out=await resolveDetail(urls[i],meta);if(out.length)return out}}catch(_e){}}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAllMovieLandV1)return false;var fn=async function(){try{return await run(arguments)}catch(_e){return[]}};fn.__niakvioAllMovieLandV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER", serialized)
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper.lstrip(),
        data={"runtime": payload, "legacyExecutableSeed": False, "upstreamJsExecuted": False},
    )
