#!/usr/bin/env python3
"""Reusable open-archive JSON runtime restricted to explicitly public-domain video."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MARKER = "NIAKVIO_OPEN_ARCHIVE_PUBLIC_DOMAIN_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_OPEN_ARCHIVE_PUBLIC_DOMAIN_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function arr(v){return Array.isArray(v)?v:(v==null?[]:[v])}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function uniq(v){var out=[],seen=Object.create(null);for(var i=0;i<v.length;i++){var x=s(v[i]),k=norm(x);if(!x||!k||seen[k])continue;seen[k]=1;out.push(x)}return out}
function yearOf(v){var m=s(v).match(/\b(18|19|20)\d{2}\b/);return m?Number(m[0]):0}
function isPublicDomain(v){var values=arr(v);for(var i=0;i<values.length;i++){var x=s(values[i]).toLowerCase();if(x.indexOf("creativecommons.org/publicdomain/")>=0)return true}return false}
function request(args){
  var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
  if(type!=="movie")return null;
  var id=s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];
  if(!/^\d+$/.test(id))return null;
  var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||{};
  var titles=uniq([obj&&obj.title,obj&&obj.name,md.title,md.original_title,ctx.title].concat(arr(obj&&obj.aliases)));
  var year=Number((obj&&obj.year)||yearOf(md.release_date)||yearOf(ctx.releaseDate))||0;
  return{tmdbId:id,type:"movie",titles:titles,year:year}
}
async function hydrate(q){
  if(!q)return q;
  try{
    var fn=g&&g.__nuvioCoreGetTmdbDataV1;
    if(typeof fn==="function"){
      var z=await fn({tmdbId:q.tmdbId,mediaType:"movie",tmdbNamespace:"movie"}),m=(z&&z.metadata)||z||{};
      q.titles=uniq(q.titles.concat([m.title,m.original_title]));
      if(!q.year)q.year=yearOf(m.release_date);
      var alt=m.alternative_titles&&(m.alternative_titles.titles||m.alternative_titles.results||m.alternative_titles);
      if(Array.isArray(alt))for(var i=0;i<alt.length&&q.titles.length<10;i++)q.titles=uniq(q.titles.concat([alt[i]&&(alt[i].title||alt[i].name)]));
    }
  }catch(_e){}
  return q
}
async function getJson(url){
  try{
    var u=new URL(url);if(u.origin!==c.base)return null;
    var r=await g.fetch(url,{redirect:"follow",headers:{"Accept":"application/json,*/*","User-Agent":c.userAgent}});
    if(!r||!r.ok)return null;
    return await r.json()
  }catch(_e){return null}
}
function titleMatch(candidate,titles){var n=norm(candidate);if(!n)return 0;for(var i=0;i<titles.length;i++){var t=norm(titles[i]);if(t&&n===t)return 120}return 0}
async function search(q){
  for(var t=0;t<q.titles.length&&t<6;t++){
    var title=q.titles[t],query='title:"'+s(title).replace(/"/g,"")+'" AND mediatype:movies AND licenseurl:*publicdomain*';
    var url=c.base+"/advancedsearch.php?q="+encodeURIComponent(query)+"&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=date&fl%5B%5D=year&fl%5B%5D=licenseurl&rows=20&page=1&output=json";
    var value=await getJson(url),docs=value&&value.response&&Array.isArray(value.response.docs)?value.response.docs:[];
    var best=null,bestScore=0;
    for(var i=0;i<docs.length;i++){
      var row=docs[i]||{};if(!s(row.identifier)||!isPublicDomain(row.licenseurl))continue;
      var score=titleMatch(row.title,q.titles);if(!score)continue;
      var cy=Number(row.year)||yearOf(row.date),distance=(q.year&&cy)?Math.abs(q.year-cy):0;
      if(q.year&&cy&&distance>3)continue;
      score-=distance*4;
      if(score>bestScore){best=row;bestScore=score}
    }
    if(best)return best
  }
  return null
}
function pathEncode(v){return s(v).split("/").map(function(p){return encodeURIComponent(p)}).join("/")}
function quality(row){var h=Number(row&&row.height)||0;if(h>=2160)return"2160p";if(h>=1440)return"1440p";if(h>=1080)return"1080p";if(h>=720)return"720p";if(h>=480)return"480p";return"Auto"}
function playableFile(row){
  var n=s(row&&row.name),f=s(row&&row.format).toLowerCase();
  if(!n||/\.(?:srt|vtt|jpg|jpeg|png|gif|txt|xml|json)$/i.test(n))return false;
  return /\.(?:mp4|m4v)$/i.test(n)||/mpeg-?4|h\.?264/.test(f)
}
async function resolve(args){
  var q=request(args);if(!q)return[];q=await hydrate(q);if(!q.titles.length)return[];
  var hit=await search(q);if(!hit)return[];
  var meta=await getJson(c.base+"/metadata/"+encodeURIComponent(s(hit.identifier)));if(!meta||!meta.metadata||!isPublicDomain(meta.metadata.licenseurl))return[];
  var sourceTitle=s(meta.metadata.title||hit.title),identity=titleMatch(sourceTitle,q.titles);if(!identity)return[];
  var sourceYear=yearOf(meta.metadata.date)||Number(hit.year)||yearOf(hit.date);
  if(q.year&&sourceYear&&Math.abs(q.year-sourceYear)>3)return[];
  var files=Array.isArray(meta.files)?meta.files.filter(playableFile):[];
  files.sort(function(a,b){var ah=Number(a&&a.height)||0,bh=Number(b&&b.height)||0;if(ah!==bh)return bh-ah;return (Number(b&&b.size)||0)-(Number(a&&a.size)||0)});
  var out=[],seen=Object.create(null);
  for(var i=0;i<files.length&&out.length<c.maxStreams;i++){
    var file=files[i]||{},name=s(file.name);if(!name)continue;
    var url=c.base+"/download/"+encodeURIComponent(s(hit.identifier))+"/"+pathEncode(name);if(seen[url])continue;seen[url]=1;
    out.push({provider:c.provider,name:c.name,title:c.name+" | "+sourceTitle,sourceName:c.name,sourceTitle:sourceTitle,sourceYear:sourceYear||undefined,url:url,quality:quality(file),format:"MP4",headers:{"User-Agent":c.userAgent}})
  }
  return out
}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:c.provider,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply_runtime(
    text: str,
    *,
    managed_fix_id: str,
    options: dict[str, Any] | None = None,
) -> str:
    cfg = dict(options or {})
    base = str(cfg.get("base") or "https://archive.org").rstrip("/")
    if base != "https://archive.org":
        raise ValueError("open archive public-domain runtime is restricted to https://archive.org")
    payload = {
        "base": base,
        "provider": str(cfg.get("provider") or "internet-archive").strip(),
        "name": str(cfg.get("name") or "Internet Archive — Public Domain").strip(),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 4), 8)),
        "userAgent": str(cfg.get("user_agent") or "NiakVIO/5 public-domain archive reader"),
    }
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        managed_fix_id,
        wrapper,
        data={
            "runtime": payload,
            "scope": "explicit-public-domain-movies-only",
            "search": "archive.org advancedsearch mediatype:movies + licenseurl:*publicdomain*",
            "rightsRecheck": "metadata.licenseurl must contain creativecommons.org/publicdomain/",
            "terminalMedia": "archive.org/download/<identifier>/<video-file>",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("shared patch implementation only")
