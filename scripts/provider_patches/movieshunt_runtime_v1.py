#!/usr/bin/env python3
"""Clean provider-local MoviesHunt catalogue -> Abhilinks -> host runtime."""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIESHUNT.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIESHUNT_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MOVIESHUNT_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[’'\x60]/g,"").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function abs(v,b){try{return new URL(s(v).replace(/&amp;/gi,"&"),b).toString()}catch(_e){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_e){return""}}
function uniq(rows,keyfn){var out=[],seen={};for(var i=0;i<(rows||[]).length;i++){var x=rows[i],k=keyfn?keyfn(x):s(x);if(k&&!seen[k]){seen[k]=1;out.push(x)}}return out}
function request(args){var f=args[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var t=s((o&&(o.semanticType||o.canonicalMediaType||o.mediaType||o.type))||ctx.semanticType||ctx.canonicalMediaType||args[1]||"movie").toLowerCase();if(t==="series")t="tv";if(t!=="movie")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{tmdbId:id,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:"movie",tmdbNamespace:"movie"});return projected(r)}}catch(_e){}return null}
function aliases(md){if(!md)return[];var out=[md.title,md.original_title,md.name,md.original_name],alt=md.alternative_titles&&(md.alternative_titles.titles||md.alternative_titles.results||md.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length;i++)out.push(alt[i]&&(alt[i].title||alt[i].name));return uniq(out.filter(Boolean)).slice(0,6)}
function headers(ref,extra){var h={"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return Object.assign(h,extra||{})}
async function fetchText(url,ref,extra){try{var r=await g.fetch(url,{headers:headers(ref,extra),redirect:"follow"});if(!r)return{ok:false,url:url,text:""};return{ok:r.ok,url:r.url||url,text:await r.text()}}catch(_e){return{ok:false,url:url,text:""}}}
function strip(v){var src=String(v==null?"":v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return s(out).replace(/&(?:nbsp|amp|quot|#039);/gi," ").replace(/\s+/g," ").trim()}
function attr(tag,name){var re=new RegExp(name+"\\s*=\\s*[\"']([^\"']+)[\"']","i"),m=re.exec(tag);return m?m[1]:""}
function anchors(html,base){var out=[],re=/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<240){var href=attr(m[1],"href"),u=abs(href,base);if(!u)continue;out.push({url:u,text:strip(m[2]),index:m.index,tag:m[0]})}return out}
function scoreTitle(label,title,year){var a=norm(label),b=norm(title),score=0;if(!a||!b)return 0;if(a===b)score+=220;else if(a.indexOf(b)>=0||b.indexOf(a)>=0)score+=135;var bt=b.split(/\s+/).filter(function(x){return x.length>=3}),hit=0;for(var i=0;i<bt.length;i++)if(a.indexOf(bt[i])>=0)hit++;if(bt.length)score+=Math.round(hit/bt.length*80);if(year&&a.indexOf(String(year))>=0)score+=25;return score}
function jsonRows(raw,base,title,year){var data=null;try{data=JSON.parse(raw)}catch(_e){return[]}var out=[],seen={},visited=0;function add(obj){if(!obj||typeof obj!=="object")return;var label=s(obj.post_title||obj.title||obj.name||obj.label||obj.text||obj.postTitle||obj.display_title),candidate=obj.permalink||obj.url||obj.link||obj.href||obj.path||obj.slug||obj.post_url||obj.postUrl||"";var u=abs(candidate,base);if(!u&&candidate&&String(candidate).charAt(0)!=="/")u=abs("/"+candidate,base);var sc=scoreTitle(label,title,year);if(u&&label&&sc>=70&&!seen[u]){seen[u]=1;out.push({url:u,title:label,score:sc})}}function walk(v,depth){if(depth>6||visited>1200||v==null)return;visited++;if(Array.isArray(v)){for(var i=0;i<v.length;i++)walk(v[i],depth+1);return}if(typeof v==="object"){add(v);var keys=Object.keys(v);for(var j=0;j<keys.length;j++)walk(v[keys[j]],depth+1);return}if(typeof v==="string"&&v.indexOf("<a")>=0){var rows=searchRows(v,base,title,year);for(var k=0;k<rows.length;k++)if(!seen[rows[k].url]){seen[rows[k].url]=1;out.push(rows[k])}}}walk(data,0);out.sort(function(a,b){return b.score-a.score});return out.slice(0,8)}
async function dynamicLookup(searchResponse,title,year){var b="";try{b=new URL(searchResponse&&searchResponse.url||c.base).origin}catch(_e){return[]}var u=b+"/lookup.php?q="+encodeURIComponent(title)+"&page=1&per_page=30",r=await fetchText(u,searchResponse&&searchResponse.url||b+"/search.html",{"Accept":"application/json,text/plain,*/*"});if(!r.ok)return[];return jsonRows(r.text,r.url||u,title,year)}
function searchRows(html,base,title,year){var out=[],seen={},re=/<h[1-6]\b[^>]*class=["'][^"']*entry-title[^"']*["'][^>]*>([\s\S]*?)<\/h[1-6]>/gi,m;while((m=re.exec(html||""))!==null&&out.length<80){var a=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/i.exec(m[1]);if(!a)continue;var u=abs(a[1],base),label=strip(a[2]),sc=scoreTitle(label,title,year);if(u&&sc>=80&&!seen[u]){seen[u]=1;out.push({url:u,title:label,score:sc})}}if(!out.length){var as=anchors(html,base),bh="";try{bh=new URL(base).hostname.toLowerCase()}catch(_e){}for(var i=0;i<as.length;i++){var pu=null;try{pu=new URL(as[i].url)}catch(_e2){continue}var path=(pu.pathname||"/").toLowerCase();if(bh&&pu.hostname.toLowerCase()!==bh)continue;if(/\/(?:search(?:\.html)?|search\/label|p|feeds?|assets?|static|images?|css|js)(?:[/?#.-]|$)/i.test(path))continue;if(!/\.html$/i.test(path)&&!/\/(?:movie|movies|film|download|[a-z0-9-]{5,})\/?$/i.test(path))continue;var blob=as[i].text+" "+decodeURIComponent(path).replace(/[\/_-]+/g," "),sc2=scoreTitle(blob,title,year);if(sc2>=80&&!seen[as[i].url]){seen[as[i].url]=1;out.push({url:as[i].url,title:as[i].text||path,score:sc2})}}}out.sort(function(a,b){return b.score-a.score});return out.slice(0,5)}
async function detail(md){var als=aliases(md),year=Number(s(md&&md.release_date).slice(0,4))||0;for(var i=0;i<als.length;i++){var queries=[c.base+"/?s="+encodeURIComponent(als[i]),c.base+"/search.html?q="+encodeURIComponent(als[i])];for(var q=0;q<queries.length;q++){var search=queries[q],sr=await fetchText(search,c.base+"/");if(!sr.ok)continue;var rows=searchRows(sr.text,sr.url||search,als[i],year);if(!rows.length&&/\/search\.html(?:\?|$)/i.test(sr.url||search))rows=await dynamicLookup(sr,als[i],year);for(var j=0;j<rows.length;j++){var dr=await fetchText(rows[j].url,sr.url||search);if(dr.ok)return dr}}}return null}
function abhilinks(html,base){var out=[],as=anchors(html,base);for(var i=0;i<as.length;i++)if(/^https?:\/\/abhilinks\.(?:life|site)\//i.test(as[i].url))out.push(as[i].url);return uniq(out).slice(0,5)}
function quality(blob){var x=s(blob),m=x.match(/(?:^|\D)(2160|1080|720|480)\s*[pP](?:\D|$)/);if(m)return m[1]+"p";return /\b4k\b|\buhd\b/i.test(x)?"2160p":""}
function size(blob){var m=s(blob).match(/(\d+(?:\.\d+)?\s*(?:GB|MB))/i);return m?m[1]:""}
function unwrapVcloud(v){var u=s(v);var m=u.match(/href\.li\/\?https:\/\/vcloud\.zip\/([^"&?]+)/i);if(m)return"https://vcloud.zip/"+m[1];return u}
function sourceOptions(html,base){var out=[],seen={},as=anchors(html,base);for(var i=0;i<as.length;i++){var u=as[i].url,low=u.toLowerCase(),kind="";if(/hubcloud\.cx\/(?:drive|video)\//i.test(low))kind="hubcloud";else if(/href\.li\/\?https:\/\/vcloud\.zip\//i.test(low)||/vcloud\.zip\//i.test(low)){kind="vcloud";u=unwrapVcloud(u)}if(!kind||seen[u])continue;seen[u]=1;var start=Math.max(0,as[i].index-650),blob=(html||"").slice(start,as[i].index+as[i].tag.length+650)+" "+as[i].text;out.push({url:u,kind:kind,quality:quality(blob),size:size(blob)})}return out.slice(0,10)}
function terminalAnchors(html,base){var out=[],as=anchors(html,base);for(var i=0;i<as.length;i++){var u=as[i].url,h=host(u);if(!/^https?:/i.test(u))continue;if(/(^|\.)cdn\.fsl-buckets\.life$/.test(h)||/cloudflarestorage/.test(h)||/\.r2\.dev$/.test(h)||/workers\.dev$/.test(h)||/^hub\.(?:latent|whistle)/.test(h))out.push({url:u,quality:quality(as[i].text),label:as[i].text})}return uniq(out,function(x){return x.url}).slice(0,12)}
async function hubcloud(url,referer){var p=await fetchText(url,referer);if(!p.ok)return[];var direct=terminalAnchors(p.text,p.url);if(direct.length)return direct;var m=/<a\b[^>]*href=["']([^"']*hubcloud\.php[^"']*)["']/i.exec(p.text||"");if(!m)return[];var php=abs(m[1],p.url),q=await fetchText(php,p.url,{"Cookie":"xla=s4t","Accept":"text/html,*/*"});return q.ok?terminalAnchors(q.text,q.url):[]}
function decode64(v){try{var fn=(g&&g.atob)||((typeof atob==="function")?atob:null);return fn?fn(v):""}catch(_e){return""}}
async function vcloud(url,referer){var p=await fetchText(unwrapVcloud(url),referer);if(!p.ok)return[];var direct=terminalAnchors(p.text,p.url);if(direct.length)return direct;var m=/atob\s*\(\s*atob\s*\(\s*["']([^"']+)["']\s*\)\s*\)/i.exec(p.text||"");if(!m)return[];var a=decode64(m[1]),target=decode64(a);if(!/^https?:/i.test(target))return[];var q=await fetchText(target,c.base+"/",{"Cookie":"xla=s4t"});return q.ok?terminalAnchors(q.text,q.url):[]}
async function crawlFallback(url,referer){var rows=[];try{if(typeof _crawlDirectMedia==="function")rows=await _crawlDirectMedia([url],referer,2)}catch(_e){rows=[]}var out=[];for(var i=0;i<(rows||[]).length;i++){var x=rows[i];if(x&&/^https?:/i.test(s(x.url)))out.push({url:x.url,quality:s(x.quality),label:s(x.title||x.name)})}return out}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q);if(!md)return[];var page=await detail(md);if(!page)return[];var absPages=abhilinks(page.text,page.url),out=[],seen={};if(!absPages.length){var directFallback=await crawlFallback(page.url,page.url);for(var d=0;d<directFallback.length&&out.length<c.maxStreams;d++){var du=directFallback[d];if(seen[du.url])continue;seen[du.url]=1;out.push({name:"MoviesHunt",title:"MoviesHunt"+(du.quality?" - "+du.quality:""),url:du.url,quality:du.quality||"Unknown",provider:"movieshunt",isDirect:true,headers:{Referer:page.url,"User-Agent":c.userAgent}})}if(out.length)return out}for(var i=0;i<absPages.length&&out.length<c.maxStreams;i++){var ap=await fetchText(absPages[i],page.url);if(!ap.ok)continue;var opts=sourceOptions(ap.text,ap.url);if(!opts.length){var fallback=await crawlFallback(absPages[i],page.url);for(var f=0;f<fallback.length&&out.length<c.maxStreams;f++){var fu=fallback[f];if(seen[fu.url])continue;seen[fu.url]=1;out.push({name:"MoviesHunt",title:"MoviesHunt"+(fu.quality?" - "+fu.quality:""),url:fu.url,quality:fu.quality||"Unknown",provider:"movieshunt",isDirect:true,headers:{Referer:page.url,"User-Agent":c.userAgent}})}continue}for(var j=0;j<opts.length&&out.length<c.maxStreams;j++){var opt=opts[j],rows=opt.kind==="hubcloud"?await hubcloud(opt.url,ap.url):await vcloud(opt.url,ap.url);if(!rows.length)rows=await crawlFallback(opt.url,ap.url);for(var k=0;k<rows.length&&out.length<c.maxStreams;k++){var row=rows[k],u=s(row.url);if(!/^https?:/i.test(u)||seen[u])continue;seen[u]=1;var ql=s(row.quality||opt.quality)||"Unknown";out.push({name:"MoviesHunt",title:"MoviesHunt"+(ql&&ql!=="Unknown"?" - "+ql:""),url:u,quality:ql,provider:"movieshunt",isDirect:true,size:opt.size||"",sourceName:s(row.label),headers:{Referer:page.url,"User-Agent":c.userAgent}})}}}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"movieshunt",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://movieshunt.run",
        "maxStreams": 6,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "movieshunt-search-redirect-html-abhilinks-host-v2",
            "identity": "core-tmdb-title-provider-catalogue",
            "semanticLanes": ["movie"],
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
