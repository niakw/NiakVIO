#!/usr/bin/env python3
"""Clean AniKotoTV runtime using the current site/AJAX route contract."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIKOTOTV.RUNTIME.V1"
MARKER = "NIAKVIO_ANIKOTOTV_RUNTIME_V1"


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
    payload = {"mirrors": mirrors[:5], "provider": "anikototv", "name": "AnikotoTV"}
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    wrapper = r'''
/* NIAKVIO_ANIKOTOTV_RUNTIME_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function q(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||{};if(md&&md.state==="ok"&&md.metadata)md=md.metadata;var type=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||ctx.canonicalMediaType||args[1]||"anime").toLowerCase();if(type!=="anime"&&type!=="movie")return null;var title=s((o&&o.title)||md.title||md.name||ctx.title),date=s(md.release_date||md.first_air_date||(o&&o.year)||ctx.year);return{type:type,title:title,year:Number(date.slice(0,4))||Number(o&&o.year)||0,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
function h(ref,xhr){var out={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/3","Accept":"text/html,application/json,text/plain,*/*"};if(ref)out.Referer=ref;if(xhr)out["X-Requested-With"]="XMLHttpRequest";return out}
async function get(url,ref,xhr){var r=await g.fetch(url,{headers:h(ref,xhr),credentials:"include"});if(!r||!r.ok)throw new Error("anikoto_http_"+String(r&&r.status||0));return{body:await r.text(),url:r.url||url}}
function text(v){return s(v).replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ")}
function score(a,b,year){var x=norm(a),y=norm(b);if(!x||!y)return 0;var n=x===y?240:(x.indexOf(y)>=0||y.indexOf(x)>=0?120:0);for(var t of y.split(" "))if(t.length>=3&&x.indexOf(t)>=0)n+=16;if(year&&s(a).indexOf(String(year))>=0)n+=20;return n}
function results(html,base,meta){var out=[],re=/<a\b[^>]*href=["']([^"']*\/watch\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html))&&out.length<120){var title=text(m[2]),sc=score(title,meta.title,meta.year);if(sc<32)continue;var slug=s(m[1]).split("/watch/").pop().split(/[?#]/)[0];if(slug)out.push({slug:slug,score:sc,title:title})}out.sort(function(a,b){return b.score-a.score});var seen={},v=[];for(var i=0;i<out.length&&v.length<6;i++){if(!seen[out[i].slug]){seen[out[i].slug]=1;v.push(out[i])}}return v}
function parsed(v){try{return JSON.parse(s(v))}catch(_e){return null}}
function episodeRows(raw){var data=parsed(raw),html=data&&data.result?data.result:raw,out=[],re=/<a\b([^>]+)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(s(html)))&&out.length<300){var attrs=m[1],id=(/(?:data-ep-id|data-id)=["']([^"']+)/i.exec(attrs)||[])[1]||"",num=Number(((/data-num=["']([^"']+)/i.exec(attrs)||[])[1]))||out.length+1,ids=(/data-ids=["']([^"']+)/i.exec(attrs)||[])[1]||"",slug=(/data-slug=["']([^"']+)/i.exec(attrs)||[])[1]||"";if(id||ids)out.push({id:id,num:num,ids:ids.replace(/[\\"']/g,""),slug:slug})}return out}
function serverLinks(raw){var data=parsed(raw),html=data&&data.result?data.result:raw,out=[],re=/data-link-id=["']([^"']+)["']/gi,m;while((m=re.exec(s(html)))&&out.length<12){if(m[1]&&!out.includes(m[1]))out.push(m[1])}return out}
function streamUrl(raw){var data=parsed(raw),r=data&&data.results?data.results:(data&&data.result?data.result:data);if(typeof r==="string"){var p=parsed(r);if(p)r=p}if(r&&typeof r==="object"){var u=s(r.url||r.file||r.src);if(/^https?:\/\//i.test(u))return u}return""}
function quality(url){var m=s(url).match(/(2160|1080|720|480|360)p?/i);return m?m[1]+"p":""}
async function resolveOn(base,meta){var search=base+"/search?keyword="+encodeURIComponent(meta.title),page=await get(search,base+"/",false),cands=results(page.body,base,meta);for(var i=0;i<cands.length;i++){var slug=cands[i].slug;try{var epsResp=await get(base+"/api/episodes/"+encodeURIComponent(slug),base+"/watch/"+slug,false),epsData=parsed(epsResp.body),block=epsData&&epsData.results?epsData.results:null,episodes=[];if(block&&Array.isArray(block.episodes)){episodes=block.episodes.map(function(e,j){return{id:s(e.id),num:Number(e.episode_no)||j+1,ids:s(e.server_ids),slug:s(e.slug)}})}else episodes=episodeRows(epsResp.body);if(!episodes.length)continue;var wanted=meta.type==="movie"?episodes[0]:episodes.find(function(e){return Number(e.num)===Number(meta.episode)})||episodes[meta.episode-1];if(!wanted)continue;var ids=s(wanted.ids||wanted.id);if(!ids)continue;var servers=await get(base+"/api/servers?ids="+encodeURIComponent(ids),base+"/watch/"+slug,false),svData=parsed(servers.body),links=[];if(svData&&Array.isArray(svData.results))links=svData.results.map(function(x){return s(x&&x.link_id)}).filter(Boolean);if(!links.length)links=serverLinks(servers.body);for(var j=0;j<links.length&&j<6;j++){try{var st=await get(base+"/api/stream?id="+encodeURIComponent(links[j])+"&slug="+encodeURIComponent(slug),base+"/watch/"+slug,false),u=streamUrl(st.body);if(!u)continue;var ql=quality(u),row={name:c.name,title:c.name,url:u,provider:c.provider,headers:{Referer:base+"/","User-Agent":h()["User-Agent"]}};if(ql)row.quality=ql;return[row]}catch(_e){}}}catch(_e){}}return[]}
async function run(args){var meta=q(args);if(!meta||!meta.title)return[];for(var i=0;i<c.mirrors.length;i++){try{var out=await resolveOn(c.mirrors[i],meta);if(out.length)return out}catch(_e){}}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAnikotoV1)return false;var fn=async function(){try{return await run(arguments)}catch(_e){return[]}};fn.__niakvioAnikotoV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("CONFIG_PLACEHOLDER", serialized)
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper.lstrip(),
        data={"runtime": payload, "legacyExecutableSeed": False, "upstreamJsExecuted": False},
    )
