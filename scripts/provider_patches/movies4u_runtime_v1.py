#!/usr/bin/env python3
"""Movies4U clean-v3 runtime adapter.

Authoritative live chain (2026-09-11):
movies4u.band -> current terminal -> /lookup.php -> exact detail page ->
m4ulinks.site/number/<id> -> HubCloud/GDFlix -> media candidate.

The adapter requires canonical title metadata before the first provider request and
is intentionally bounded; it does not crawl arbitrary pages.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIES4U.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIES4U_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MOVIES4U_RUNTIME_V1 */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function norm(v){return s(v).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/&amp;/g," and ").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
  function abs(base,value){try{return new URL(s(value),base).href}catch(_e){return ""}}
  function decodeHtml(v){return s(v).replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/&#0?39;|&apos;/g,"'").replace(/&lt;/g,"<").replace(/&gt;/g,">")}
  function stripTags(v){return decodeHtml(s(v).replace(/<[^>]*>/g," ")).replace(/\s+/g," ").trim()}
  function req(args){
    var first=args[0],obj=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
    var mt=s((obj&&(obj.canonicalMediaType||obj.semanticType||obj.mediaType||obj.type))||ctx.canonicalMediaType||ctx.semanticType||ctx.mediaType||args[1]||"").toLowerCase();
    if(mt==="series")mt="tv";if(mt!=="movie"&&mt!=="tv")return null;
    var meta=(obj&&obj.tmdbMetadata)||ctx.tmdbMetadata||{};
    var title=s((obj&&(obj.title||obj.name))||meta.title||meta.name||meta.original_title||meta.original_name||ctx.title||"");
    if(!title)return null;
    var year=s((obj&&obj.year)||String(meta.release_date||meta.first_air_date||"").slice(0,4)||ctx.year||"");
    var season=Number((obj&&obj.season)!=null?obj.season:(ctx.season!=null?ctx.season:args[2]))||1;
    var episode=Number((obj&&obj.episode)!=null?obj.episode:(ctx.episode!=null?ctx.episode:args[3]))||1;
    return {mediaType:mt,title:title,year:year,season:season,episode:episode};
  }
  function headers(referer,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"*/*","Accept-Language":"en-US,en;q=0.9"};if(referer)h.Referer=referer;return h}
  async function response(url,referer,accept){try{var r=await g.fetch(url,{headers:headers(referer,accept),redirect:"follow"});if(!r||!r.ok)return null;return r}catch(_e){return null}}
  async function text(url,referer){var r=await response(url,referer,"text/html,application/xhtml+xml,text/plain,*/*");if(!r)return null;try{return {body:await r.text(),url:r.url||url}}catch(_e){return null}}
  async function jsonGet(url,referer){var r=await response(url,referer,"application/json,text/plain,*/*");if(!r)return null;try{return await r.json()}catch(_e){try{return JSON.parse(await r.text())}catch(_x){return null}}}
  function scoreHit(hit,q){
    var ht=norm(hit&&hit.post_title),target=norm(q.title);if(!ht||!target)return -1000;
    var score=0;if(ht===target)score+=500;if(ht.indexOf(target)===0)score+=320;else if(ht.indexOf(target)>=0)score+=230;
    var words=target.split(" ").filter(function(x){return x.length>1}),common=0;for(var i=0;i<words.length;i++)if(ht.indexOf(words[i])>=0)common++;score+=common*18;
    if(words.length&&common<Math.max(1,Math.ceil(words.length*0.7)))score-=300;
    if(q.year){if(ht.indexOf(String(q.year))>=0)score+=90;else if(q.mediaType==="movie"&&/\b(?:19|20)\d{2}\b/.test(ht))score-=45}
    if(q.mediaType==="tv"){if(/season|series|web series|s\d+/i.test(s(hit&&hit.post_title)))score+=30}
    return score;
  }
  function chooseHit(data,q){var hits=data&&Array.isArray(data.hits)?data.hits:[],best=null,bestScore=-9999;for(var i=0;i<hits.length;i++){var sc=scoreHit(hits[i],q);if(sc>bestScore){best=hits[i];bestScore=sc}}return bestScore>=180?best:null}
  function m4uLinks(html,base,q){
    var out=[],seen=Object.create(null),re=/href=["']([^"']*m4ulinks\.site\/number\/[^"']+)["']/gi,m;
    while((m=re.exec(html||""))!==null){var u=abs(base,decodeHtml(m[1]));if(!u||seen[u])continue;seen[u]=1;var ctx=stripTags((html||"").slice(Math.max(0,m.index-650),Math.min((html||"").length,m.index+800))),score=0;
      if(q.mediaType==="tv"){
        var low=ctx.toLowerCase(),sn=String(q.season),ep=String(q.episode);
        var exact1=new RegExp("s0?"+sn+"[^a-z0-9]{0,5}e0?"+ep+"(?:[^0-9]|$)","i");
        var exact2=new RegExp("season\\s*0?"+sn+"[\\s\\S]{0,90}episode\\s*0?"+ep+"(?:[^0-9]|$)","i");
        var eponly=new RegExp("(?:episode|ep)\\s*0?"+ep+"(?:[^0-9]|$)","i");
        var seasonOnly=new RegExp("season\\s*0?"+sn+"(?:[^0-9]|$)|s0?"+sn+"(?:[^0-9]|$)","i");
        if(exact1.test(low)||exact2.test(low))score+=500;else{if(eponly.test(low))score+=260;if(seasonOnly.test(low))score+=80}
        var otherEp=low.match(/(?:episode|ep|e)\s*0?(\d{1,3})/i);if(otherEp&&Number(otherEp[1])!==q.episode)score-=220;
      } else score=100;
      var qm=ctx.match(/\b(2160p|4k|1080p|720p|480p)\b/i);out.push({url:u,ctx:ctx,score:score,quality:qm?qm[1]:"HD"});
    }
    out.sort(function(a,b){return b.score-a.score});
    if(q.mediaType==="tv"&&out.length&&out[0].score<200)return [];
    return out.slice(0,c.maxResolverLinks);
  }
  function externalLinks(html,base){var out=[],seen=Object.create(null),re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null){var u=abs(base,decodeHtml(m[1])),label=stripTags(m[2]);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;out.push({url:u,label:label})}return out}
  function directish(url,label){var x=(s(url)+" "+s(label)).toLowerCase();return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(url)||/10gbps|pixelserver|direct\s*download|instant\s*download|download\s*now/i.test(x)}
  async function resolveHubCloud(url,referer){
    var first=await text(url,referer);if(!first)return [];
    var m=/var\s+url\s*=\s*["']([^"']+)["']/i.exec(first.body),linksPage=m?abs(first.url,m[1]):"",page=first;
    if(linksPage){var p=await text(linksPage,first.url);if(p)page=p}
    var rows=externalLinks(page.body,page.url),out=[];
    for(var i=0;i<rows.length;i++){var u=rows[i].url,label=rows[i].label;if(!directish(u,label))continue;if(/(?:facebook|telegram|twitter|instagram|google\.com)/i.test(u))continue;out.push({url:u,label:label,referer:page.url});if(out.length>=c.maxStreams)break}
    return out;
  }
  async function resolveGdflix(url,referer){
    var page=await text(url,referer);if(!page)return [];
    var rows=externalLinks(page.body,page.url),out=[];
    for(var i=0;i<rows.length;i++){var u=rows[i].url,label=rows[i].label,x=(u+" "+label).toLowerCase();if(/(?:facebook|telegram|twitter|instagram|google\.com)/i.test(u))continue;if(directish(u,label)||/drive|pixel|cloud|server|download/i.test(x)){out.push({url:u,label:label,referer:page.url});if(out.length>=c.maxStreams)break}}
    return out;
  }
  async function resolverTargets(link,detailUrl){
    var page=await text(link.url,detailUrl);if(!page)return [];
    var rows=externalLinks(page.body,page.url),preferred=[],secondary=[];
    for(var i=0;i<rows.length;i++){var host="";try{host=new URL(rows[i].url).hostname.toLowerCase()}catch(_e){}
      if(host.indexOf("hubcloud.")>=0||host.indexOf("hubdrive.")>=0)preferred.push(rows[i].url);else if(host.indexOf("gdflix.")>=0)secondary.push(rows[i].url)}
    var out=[];
    for(var j=0;j<preferred.length&&out.length<c.maxStreams;j++){var a=await resolveHubCloud(preferred[j],page.url);out=out.concat(a)}
    for(var k=0;k<secondary.length&&out.length<c.maxStreams;k++){var b=await resolveGdflix(secondary[k],page.url);out=out.concat(b)}
    return out.slice(0,c.maxStreams);
  }
  function quality(v,fallback){var x=(s(v)+" "+s(fallback)).toLowerCase();if(x.indexOf("2160")>=0||x.indexOf("4k")>=0)return"2160p";if(x.indexOf("1080")>=0)return"1080p";if(x.indexOf("720")>=0)return"720p";if(x.indexOf("480")>=0)return"480p";return s(fallback)||"HD"}
  async function resolve(args){
    var q=req(args);if(!q)return [];
    var base=s(c.base).replace(/\/+$/,"");if(!/^https?:\/\//i.test(base))return [];
    var lookup=base+"/lookup.php?q="+encodeURIComponent(q.title)+"&page=1&per_page="+encodeURIComponent(String(c.perPage));
    var data=await jsonGet(lookup,base+"/");if(!data||data.ok===false)return [];
    var hit=chooseHit(data,q);if(!hit)return [];
    var detailUrl=abs(base,hit.permalink||hit.url);if(!detailUrl)return [];
    var detail=await text(detailUrl,lookup);if(!detail)return [];
    var links=m4uLinks(detail.body,detail.url,q);if(!links.length)return [];
    var out=[],seen=Object.create(null);
    for(var i=0;i<links.length&&out.length<c.maxStreams;i++){
      var targets=await resolverTargets(links[i],detail.url);
      for(var j=0;j<targets.length&&out.length<c.maxStreams;j++){
        var u=s(targets[j].url);if(!/^https?:\/\//i.test(u)||seen[u])continue;seen[u]=1;
        out.push({name:"Movies4U",title:"Movies4U | "+q.title,url:u,quality:quality(targets[j].label,links[i].quality),language:"multi",headers:headers(targets[j].referer||detail.url,"*/*"),provider:"movies4u"});
      }
    }
    return out;
  }
  function install(container,key){if(!container||typeof container[key]!=="function"||container[key].__niakvioMovies4uRuntimeV1)return false;var wrapped=async function(){return await resolve(arguments)};wrapped.__niakvioMovies4uRuntimeV1=true;container[key]=wrapped;return true}
  var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://new6.movies4u.clinic"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        ),
        "perPage": int(cfg.get("per_page") or 30),
        "maxResolverLinks": int(cfg.get("max_resolver_links") or 4),
        "maxStreams": int(cfg.get("max_streams") or 4),
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
            "identity": "canonical-title-year-before-provider-network",
            "search": "/lookup.php?q={title}&page=1&per_page={perPage}",
            "detail": "exact permalink from lookup hit",
            "resolver": "m4ulinks -> hubcloud/gdflix -> media",
            "officialHub": "https://movies4u.band",
            "legacyExecutableSeed": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
