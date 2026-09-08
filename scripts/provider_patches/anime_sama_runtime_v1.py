#!/usr/bin/env python3
"""NiakVIO-owned Anime-Sama deterministic catalogue/episodes.js runtime.

This is a clean-room declarative runtime family implementation derived from the
observable provider contract (catalogue slug -> language/season episodes.js ->
player URL). It does not embed or execute upstream JavaScript.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIME-SAMA.RUNTIME.V1"
MARKER = "NIAKVIO_ANIME_SAMA_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIME_SAMA_RUNTIME_V1 */
;(function(g,c){"use strict";
function txt(v){return String(v==null?"":v).trim()}
function uniq(v){return Array.from(new Set((v||[]).filter(Boolean)))}
function request(args){var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=txt((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(raw!=="movie"&&raw!=="tv"&&raw!=="anime")return null;var id=txt((obj&&(obj.tmdbId||obj.tmdb_id))||ctx.tmdbId||(typeof first==="string"?first:""));if(!/^\d+$/.test(id))return null;return{type:raw,transport:raw==="movie"?"movie":"tv",tmdbId:id,season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1}}
function slug(v){try{if(typeof _slug==="function")return _slug(v)}catch(_e){}return txt(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
function bases(){var out=[];try{out.push(NIAKVIO_PROVIDER_MODEL.officialSite,NIAKVIO_PROVIDER_MODEL.knownSite)}catch(_e){}out.unshift(c.base);for(var i=0;i<(c.fallbackBases||[]).length;i++)out.push(c.fallbackBases[i]);return uniq(out.map(function(v){return txt(v).replace(/\/$/,"")}).filter(function(v){return /^https?:\/\//i.test(v)}))}
async function text(url,opt){try{var r=typeof _fetch==="function"?await _fetch(url,opt||{}):await g.fetch(url,opt||{});if(!r||r.ok===false)return"";return await r.text()}catch(_e){return""}}
function arrays(js){var out=[],re=/var\s+([a-z0-9_$]+)\s*=\s*\[([\s\S]*?)\s*\];/gim,m;while((m=re.exec(txt(js)))!==null){var vals=[],q=/["']([^"']+)["']/g,x;while((x=q.exec(m[2]))!==null){if(/^https?:\/\//i.test(x[1]))vals.push(x[1])}if(vals.length)out.push(vals);if(out.length>=24)break}return out}
async function direct(player,referer){if(!/^https?:\/\//i.test(txt(player)))return[];try{if(typeof _directMedia==="function"&&_directMedia(player)&&typeof _streams==="function")return _streams([player],referer).slice(0,4)}catch(_e){}try{if(typeof _crawlDirectMedia==="function")return (await _crawlDirectMedia([player],referer,2)).slice(0,4)}catch(_e){}return[]}
async function episodeJs(base,s,lang,q){var paths=[];if(q.type==="movie")paths.push("film");else{paths.push("saison"+q.season);paths.push("")}for(var p=0;p<paths.length;p++){var middle=paths[p]?"/"+paths[p]:"";var u=base+"/catalogue/"+encodeURIComponent(s)+middle+"/"+lang+"/episodes.js";var body=await text(u,{headers:{Referer:base+"/"}});if(!body)continue;var groups=arrays(body),idx=q.type==="movie"?0:q.episode-1;if(idx<0)continue;var streams=[];for(var i=0;i<groups.length&&streams.length<c.targetStreams;i++){var player=groups[i][idx];if(!player)continue;var rows=await direct(player,base+"/");for(var j=0;j<rows.length;j++){var row=rows[j];if(row&&typeof row==="object"){row.name=row.name||"Anime-Sama";row.title=row.title||("Anime-Sama "+lang.toUpperCase());row.language=row.language||(lang==="vf"?"fr":"vostfr")}streams.push(row)}}if(streams.length)return streams}return[]}
function titles(meta){var out=[];if(meta){out.push(meta.title,meta.name,meta.original_title,meta.original_name);if(Array.isArray(meta.aliases))out=out.concat(meta.aliases)}return uniq(out.map(txt).filter(Boolean)).slice(0,5)}
async function searchSlugs(base,title){var url=base+"/template-php/defaut/fetch.php",body="query="+encodeURIComponent(title),html=await text(url,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","Referer":base+"/"},body:body});if(!html)return[];var out=[],re=/href=["'][^"']*\/catalogue\/([^/"'#?]+)\/?[^"']*["']/gi,m;while((m=re.exec(html))!==null){var s=txt(m[1]);if(s&&!out.includes(s))out.push(s);if(out.length>=2)break}return out}
async function trySlug(base,s,q){var out=[];for(var i=0;i<c.languages.length&&out.length<c.targetStreams;i++){var rows=await episodeJs(base,s,c.languages[i],q);out=out.concat(rows)}return out.slice(0,c.targetStreams)}
async function resolve(args){var q=request(args);if(!q)return[];var meta=null;try{if(typeof _tmdb==="function")meta=await _tmdb(q.tmdbId,q.transport)}catch(_e){}if(!meta){try{var ctx=g&&g.__nuvioMediaContext||{};meta=ctx.tmdbMetadata||null}catch(_e){}}var tt=titles(meta);if(!tt.length)return[];var bs=bases();for(var b=0;b<bs.length;b++){var base=bs[b],primary=slug(tt[0]),candidates=[primary];if(q.type!=="movie"&&q.season>1){candidates.push(primary+"-saison-"+q.season,primary+"-"+q.season)}for(var i=0;i<candidates.length;i++){var rows=await trySlug(base,candidates[i],q);if(rows.length)return rows}for(var t=0;t<tt.length&&t<3;t++){var found=await searchSlugs(base,tt[t]);for(var f=0;f<found.length;f++){if(candidates.includes(found[f]))continue;var rows2=await trySlug(base,found[f],q);if(rows2.length)return rows2}}}return[]}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__niakvioAnimeSamaRuntimeV1)return false;var fn=async function(){try{return await resolve(arguments)}catch(_e){return[]}};fn.__niakvioAnimeSamaRuntimeV1=true;o[k]=fn;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://anime-sama.to",
        "fallbackBases": ["https://anime-sama.store"],
        "languages": ["vostfr", "vf"],
        "targetStreams": 3,
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["fallbackBases"] = [str(v).rstrip("/") for v in cfg.get("fallbackBases") or [] if str(v).startswith(("http://", "https://"))]
    cfg["languages"] = [str(v).strip().casefold() for v in cfg.get("languages") or [] if str(v).strip()][:4] or ["vostfr", "vf"]
    cfg["targetStreams"] = max(1, min(8, int(cfg.get("targetStreams") or 3)))
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError(f"{MANAGED_FIX_ID}: base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "catalogue-episodes-js-v1",
            "identity": "core-tmdb-metadata-to-anime-sama-catalogue-slug",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
