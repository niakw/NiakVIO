#!/usr/bin/env python3
"""CinemaCity clean-v3 sitemap/proxy runtime adapter.

Historical CinemaCity JavaScript is knowledge-only. The durable contract is:
cinemacity.cc catalogue -> /news_pages.xml -> strict title/year/kind candidate ->
cc.realbestia.com proxy -> direct media extraction. The adapter is bounded and
fails closed for episodic identity when the requested episode cannot be proven.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.CINEMACITY.RUNTIME.V1"
MARKER = "NIAKVIO_CINEMACITY_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_CINEMACITY_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function norm(v){
    var x=s(v);
    try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}
    return x.toLowerCase().replace(/\([^)]*\)/g," ").replace(/[^a-z0-9]+/g," ").trim();
  }
  function requestArgs(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null;
    var ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var md=(obj&&(obj.tmdbMetadata||obj.tmdb_metadata||obj.metadata))||ctx.tmdbMetadata||null;
    if(md&&md.state==="ok"&&md.metadata)md=md.metadata;
    md=md&&typeof md==="object"?md:{};
    var type=s((obj&&(obj.canonicalMediaType||obj.mediaType||obj.type))||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();
    var date=s(md.release_date||md.first_air_date||md.year);
    var aliases=[md.title,md.name,md.original_title,md.original_name].map(s).filter(Boolean);
    return {
      id:s((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||ctx.tmdbId||first).replace(/^tmdb:/i,"").split(":")[0],
      type:type==="movie"?"movie":"tv",
      titles:aliases,
      year:date.slice(0,4),
      season:Number((obj&&obj.season)!=null?obj.season:args[2])||0,
      episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||0
    };
  }
  async function text(url){
    var response=await g.fetch(url,{headers:{"Accept":"text/html,application/xml,text/plain,*/*","User-Agent":c.userAgent},redirect:"follow"});
    if(!response||!response.ok)throw new Error("cinemacity_http_"+(response&&response.status||0));
    return {body:await response.text(),url:response.url||url,headers:response.headers};
  }
  function decodeEntities(v){return s(v).replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/&#039;/g,"'").replace(/&lt;/g,"<").replace(/&gt;/g,">")}
  function entries(xml){
    var out=[],re=/<loc>(https:\/\/cinemacity\.cc\/(movies|tv-series)\/\d+-([a-z0-9-]+)\.html)<\/loc>/gi,m;
    while((m=re.exec(s(xml)))&&out.length<8000){
      var slug=m[3],ym=slug.match(/-(\d{4})$/),title=slug.replace(/-(?:19|20)\d{2}$/,"").replace(/-/g," ");
      out.push({url:m[1],kind:m[2]==="movies"?"movie":"tv",title:title,year:ym?ym[1]:""});
    }
    return out;
  }
  function score(q,row){
    if(!row||row.kind!==q.type)return -1;
    var wanted=q.titles.map(norm).filter(Boolean),actual=norm(row.title),best=-1;
    for(var i=0;i<wanted.length;i++){
      var w=wanted[i],v=0;
      if(actual===w)v=500;
      else if(actual&&w&&(actual.indexOf(w)>=0||w.indexOf(actual)>=0))v=240;
      else continue;
      if(q.year&&row.year){
        if(q.year!==row.year)continue;
        v+=100;
      }
      if(v>best)best=v;
    }
    return best;
  }
  function proxyUrl(url){
    try{var p=new URL(url);return c.proxyBase+p.pathname+p.search}catch(_e){return ""}
  }
  function direct(url){
    return /^https?:\/\//i.test(s(url))&&(/\.(?:m3u8|mp4|mkv|webm)(?:[?#]|$)/i.test(url)||/\/(?:hls|stream|streams|video)(?:[/?#.-]|$)/i.test(url));
  }
  function urlsFrom(v){
    var out=[],seen=Object.create(null),txt=decodeEntities(v),res=[
      /(?:href|src|file|url)\s*[:=]\s*["']([^"'<>\s]+)["']/gi,
      /https?:\/\/[^"'<>\s)]+/gi
    ];
    function add(raw,base){
      var u=s(raw);if(!u)return;
      try{if(/^\//.test(u))u=new URL(u,base||c.site).toString()}catch(_e){}
      if(/^https?:\/\//i.test(u)&&!seen[u]){seen[u]=1;out.push(u)}
    }
    for(var p=0;p<res.length;p++){
      var re=res[p],m;while((m=re.exec(txt))&&out.length<300)add(m[1]||m[0],c.site);
    }
    var b64=/["']([A-Za-z0-9+/]{24,}={0,2})["']/g,bm;
    while((bm=b64.exec(txt))&&out.length<300){
      try{
        var decoded=typeof atob==="function"?atob(bm[1]):"";
        var ur=/https?:\/\/[^"'<>\s)]+/gi,um;
        while((um=ur.exec(decoded))&&out.length<300)add(um[0],c.site);
      }catch(_e){}
    }
    return out;
  }
  function episodeEvidence(html,q,url){
    if(q.type!=="tv")return true;
    if(!q.season||!q.episode)return false;
    var ss=String(q.season),ee=String(q.episode),patterns=[
      new RegExp("s0*"+ss+"\\s*e0*"+ee,"i"),
      new RegExp("season\\s*0*"+ss+"[^\\n]{0,120}episode\\s*0*"+ee,"i"),
      new RegExp("0*"+ss+"x0*"+ee,"i")
    ];
    var target=s(url),idx=target?html.indexOf(target):-1;
    var scope=idx>=0?html.slice(Math.max(0,idx-900),Math.min(html.length,idx+900)):html;
    for(var i=0;i<patterns.length;i++)if(patterns[i].test(scope))return true;
    return false;
  }
  async function sitemap(){
    var first=c.proxyBase+c.sitemapPath+"?page=1&perPage=500";
    var r=await text(first),all=entries(r.body);
    var total=0;try{total=Number(r.headers&&r.headers.get&&r.headers.get("x-total-entries")||0)||0}catch(_e){}
    var pages=total>0?Math.ceil(total/500):1;
    pages=Math.max(1,Math.min(pages,c.maxPages));
    for(var page=2;page<=pages;page++){
      try{var next=await text(c.proxyBase+c.sitemapPath+"?page="+page+"&perPage=500");all=all.concat(entries(next.body))}catch(_e){}
    }
    if(!all.length){
      try{all=entries((await text(c.site+c.sitemapPath)).body)}catch(_e){}
    }
    return all;
  }
  async function resolve(args){
    var q=requestArgs(args);
    if(!q.titles.length||!q.year)return [];
    if(q.type==="tv"&&(!q.season||!q.episode))return [];
    try{
      var rows=await sitemap(),ranked=rows.map(function(row){return {row:row,score:score(q,row)}})
        .filter(function(x){return x.score>=240}).sort(function(a,b){return b.score-a.score}).slice(0,3);
      for(var i=0;i<ranked.length;i++){
        var target=proxyUrl(ranked[i].row.url);if(!target)continue;
        try{
          var page=await text(target),found=urlsFrom(page.body),out=[],seen=Object.create(null);
          for(var j=0;j<found.length;j++){
            var u=found[j];if(!direct(u)||seen[u]||!episodeEvidence(page.body,q,u))continue;
            seen[u]=1;out.push({
              name:"CinemaCity",
              title:q.titles[0]+(q.type==="tv"?" S"+q.season+"E"+q.episode:""),
              url:u,
              provider:"cinemacity",
              headers:{"Referer":ranked[i].row.url,"User-Agent":c.userAgent}
            });
          }
          if(out.length)return out.slice(0,20);
        }catch(_e){}
      }
    }catch(_e){}
    return [];
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__niakvioCinemaCityRuntimeV1)return false;
    var wrapped=async function(){return await resolve(arguments)};
    wrapped.__niakvioCinemaCityRuntimeV1=true;container[key]=wrapped;return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "site": str(cfg.get("site") or "https://cinemacity.cc").rstrip("/"),
        "proxyBase": str(cfg.get("proxy_base") or "https://cc.realbestia.com").rstrip("/"),
        "sitemapPath": str(cfg.get("sitemap_path") or "/news_pages.xml"),
        "maxPages": max(1, min(int(cfg.get("max_pages") or 8), 20)),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36"
        ),
    }
    wrapper = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "identity": "strict-sitemap-title-year-kind-episode",
            "legacyExecutableSeed": False,
        },
    )

if __name__ == "__main__":
    raise SystemExit("patch module only")
