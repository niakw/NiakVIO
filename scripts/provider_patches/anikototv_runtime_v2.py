#!/usr/bin/env python3
"""NiakVIO-owned AniKotoTV runtime v2.

Current clean-room chain:
  AniKoto search AJAX -> exact watch candidate -> episode list -> server list ->
  server URL -> MegaPlay embed -> /stream/getSources -> final media URL.

No upstream provider JavaScript is embedded or executed. Provider-specific catalogue
and extraction live here; Core still owns timeout/cancellation, HTTP/media
fail-closed, identity and final output validation.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIKOTOTV.RUNTIME.V2"
MARKER = "NIAKVIO_ANIKOTOTV_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_ANIKOTOTV_RUNTIME_V2 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function q(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||{};if(md&&md.state==="ok"&&md.metadata)md=md.metadata;var type=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||ctx.canonicalMediaType||args[1]||"anime").toLowerCase();if(type==="tv")type="anime";if(type!=="anime"&&type!=="movie")return null;var title=s((o&&o.title)||md.title||md.name||ctx.title),date=s(md.release_date||md.first_air_date||(o&&o.year)||ctx.year);return{type:type,title:title,year:Number(date.slice(0,4))||Number(o&&o.year)||0,season:Number((o&&o.season)!=null?o.season:args[2])||1,episode:Number((o&&o.episode)!=null?o.episode:args[3])||1}}
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
function finalSource(raw){var data=parsed(raw),src=data&&data.sources;if(src&&typeof src==="object"){var file=s(src.file||src.url||src.src);if(/^https?:\/\//i.test(file))return file}if(Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\/\//i.test(u))return u}}return""}
function megaFileId(html){var m=/<title[^>]*>\s*File\s+(\d+)\s*-\s*MegaPlay/i.exec(html);return s(m&&m[1])}
async function resolveMega(url,referer,cookie){if(!/^https?:\/\/(?:www\.)?megaplay\.buzz\//i.test(s(url)))return"";var page=await get(url,referer,false,cookie,"https://megaplay.buzz"),fid=megaFileId(page.body);if(!fid)return"";var sources=await get("https://megaplay.buzz/stream/getSources?id="+encodeURIComponent(fid),url,true,page.cookie||cookie,"https://megaplay.buzz");return finalSource(sources.body)}
function quality(url){var m=s(url).match(/(2160|1440|1080|720|480|360)p?/i);return m?m[1]+"p":""}
async function resolveOn(base,meta){var search=base+"/ajax/anime/search?keyword="+encodeURIComponent(meta.title),page=await get(search,base+"/",true,"",""),cands=results(page.body,meta);for(var i=0;i<cands.length;i++){var slug=cands[i].slug;try{var watch=await get(base+"/watch/"+encodeURIComponent(slug),base+"/",false,page.cookie,""),aid=animeId(watch.body);if(!aid)continue;var epsResp=await get(base+"/ajax/episode/list/"+encodeURIComponent(aid),watch.url,true,watch.cookie||page.cookie,""),episodes=episodeRows(epsResp.body);if(!episodes.length)continue;var wanted=meta.type==="movie"?episodes[0]:episodes.find(function(e){return Number(e.num)===Number(meta.episode)})||episodes[meta.episode-1];if(!wanted)continue;var ids=s(wanted.ids||wanted.id);if(!ids)continue;var servers=await get(base+"/ajax/server/list?servers="+encodeURIComponent(ids),watch.url,true,watch.cookie||page.cookie,""),links=serverLinks(servers.body);for(var j=0;j<links.length&&j<8;j++){try{var st=await get(base+"/ajax/server?get="+encodeURIComponent(links[j]),watch.url,true,watch.cookie||page.cookie,""),u=playerUrl(st.body);if(!u)continue;var media=u;if(/^https?:\/\/(?:www\.)?megaplay\.buzz\//i.test(u))media=await resolveMega(u,watch.url,watch.cookie||page.cookie);if(!media)continue;var isMega=/^https?:\/\/(?:www\.)?megaplay\.buzz\//i.test(u),ql=quality(media),headers={Referer:isMega?"https://megaplay.buzz/":base+"/","User-Agent":c.userAgent};if(isMega)headers.Origin="https://megaplay.buzz";var row={name:c.name,title:c.name,url:media,provider:c.provider,headers:headers};if(ql)row.quality=ql;return[row]}catch(_e){}}}catch(_e){}}return[]}
async function run(args){var meta=q(args);if(!meta||!meta.title)return[];for(var i=0;i<c.mirrors.length;i++){try{var out=await resolveOn(c.mirrors[i],meta);if(out.length)return out}catch(_e){}}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAnikotoV2)return false;var fn=async function(){try{return await run(arguments)}catch(_e){return[]}};fn.__niakvioAnikotoV2=true;o[k]=fn;return true}
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
            "runtimeFamily": "anikoto-ajax-megaplay-v2",
            "identity": "catalogue-title-season-episode",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["anime"],
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
