#!/usr/bin/env python3
"""Clean provider-local MoviesMod search/download/Driveseed runtime."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.MOVIESMOD.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIESMOD_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_MOVIESMOD_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return""}}
function origin(v){try{return new URL(v).origin}catch(_e){return""}}
function request(args){var first=args[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var t=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||args[1]||ctx.canonicalMediaType||ctx.mediaType||"movie").toLowerCase();if(t==="series")t="tv";if(t!=="movie"&&t!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;return{type:t,tmdbId:id,season:Number((o&&o.season)!=null?o.season:(args[2]!=null?args[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(args[3]!=null?args[3]:ctx.episode))||1,metadata:(o&&(o.tmdbMetadata||o.tmdb_metadata||o.metadata))||ctx.tmdbMetadata||null}}
function projected(row){if(row&&row.state==="ok"&&row.metadata)row=row.metadata;return row&&typeof row==="object"?row:null}
async function metadata(q){var row=projected(q.metadata);if(row)return row;try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var r=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type});return projected(r)}}catch(_e){}return null}
function title(md,q){if(!md)return"";return s(q.type==="movie"?(md.title||md.original_title||md.name):(md.name||md.original_name||md.title))}
function headers(ref){var h={"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function fetchText(url,opt){try{var o=opt||{},r=await g.fetch(url,{method:o.method||"GET",headers:Object.assign(headers(o.referer||""),o.headers||{}),body:o.body,redirect:"follow"});if(!r)return{ok:false,url:url,text:""};return{ok:r.ok,url:r.url||url,text:await r.text()}}catch(_e){return{ok:false,url:url,text:""}}}
function attr(tag,name){var re=new RegExp(name+"\\s*=\\s*[\"']([^\"']+)[\"']","i"),m=re.exec(tag);return m?m[1]:""}
function firstArticle(html,base){var m=/<article\b[\s\S]*?<a[^>]+href=["']([^"']+)["']/i.exec(html||"");return m?abs(m[1],base):""}
function anchors(html,base){var out=[],re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<160){var u=abs(m[1],base),txt=s(m[2]).replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ").replace(/\s+/g," ").trim();if(u)out.push({url:u,text:txt})}return out}
function quality(v){var x=s(v).toUpperCase(),m=x.match(/(2160|1080|720|480|360)P/);if(m)return m[1]+"p";return /\b4K\b|\bUHD\b/.test(x)?"2160p":"Unknown"}
function candidateDownloadLinks(html,page,q){var out=[],seen={},as=anchors(html,page);for(var i=0;i<as.length;i++){var label=as[i].text.toLowerCase();if(q.type==="movie"){if(label.indexOf("download")<0)continue}else{if(label.indexOf("episode")<0&&label.indexOf("download")<0)continue}var context=(html||"").slice(Math.max(0,(html||"").indexOf(as[i].url)-1200),(html||"").indexOf(as[i].url)+600);var blob=(context+" "+as[i].text).toLowerCase();if(q.type==="tv"&&!new RegExp("(?:s0?"+q.season+"|season\\s*"+q.season+")","i").test(blob))continue;if(!seen[as[i].url]){seen[as[i].url]=1;out.push({url:as[i].url,quality:quality(blob)})}}if(!out.length){for(var j=0;j<as.length;j++)if(/download|episode/i.test(as[j].text)&&!seen[as[j].url]){seen[as[j].url]=1;out.push({url:as[j].url,quality:quality(as[j].text)})}}return out.slice(0,10)}
function form(html){var re=/<form\b([^>]*)>([\s\S]*?)<\/form>/gi,m;while((m=re.exec(html||""))!==null){var open=m[1],id=attr(open,"id");if(id!=="landing")continue;var action=attr(open,"action"),fields={},ir=/<input\b([^>]*)>/gi,x;while((x=ir.exec(m[2]))!==null){var name=attr(x[1],"name");if(name)fields[name]=attr(x[1],"value")}return{action:action,fields:fields}}return null}
function encode(fields){var out=[];for(var k in fields)out.push(encodeURIComponent(k)+"="+encodeURIComponent(fields[k]));return out.join("&")}
async function bypass(url){var host=origin(url);if(!host)return"";var r1=await fetchText(url,{}),f1=form(r1.text);if(!f1||!f1.action)return"";var r2=await fetchText(abs(f1.action,r1.url),{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:encode(f1.fields),referer:r1.url}),f2=form(r2.text);if(!f2||!f2.action)return"";var r3=await fetchText(abs(f2.action,r2.url),{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:encode(f2.fields),referer:r2.url});var token=(r3.text.match(/\?go=([^"'&\s]+)/)||[])[1]||"",cookie=f2.fields._wp_http2||"";if(!token)return"";var r4=await fetchText(host+"?go="+encodeURIComponent(token),{headers:cookie?{"Cookie":token+"="+cookie}:{},referer:r3.url});var meta=(r4.text.match(/<meta[^>]+http-equiv=["']refresh["'][^>]+content=["'][^"']*url=([^"']+)["']/i)||[])[1]||"";if(!meta)return"";var drive=abs(meta,r4.url),r5=await fetchText(drive,{referer:r4.url}),path=(r5.text.match(/replace\(["']([^"']+)["']\)/)||[])[1]||"";if(!path||path==="/404")return"";return abs(path,r5.url)}
async function driveseed(url){var page=url;if(/r\?key=/i.test(page)){var rr=await fetchText(page,{}),p=(rr.text.match(/replace\(["']([^"']+)["']\)/)||[])[1]||"";if(p)page=abs(p,rr.url)}var r=await fetchText(page,{});if(!r.ok)return[];var q=quality(r.text),size=(r.text.match(/Size\s*:\s*([^<\n]{1,60})/i)||[])[1]||"",as=anchors(r.text,r.url),out=[];for(var i=0;i<as.length&&out.length<8;i++){var label=as[i].text.toLowerCase();if(label.indexOf("instant download")>=0){try{var x=await g.fetch(as[i].url,{headers:headers(r.url),redirect:"follow"}),u=x&&x.url?x.url:"";if(u){try{var parsed=new URL(u),param=parsed.searchParams.get("url");if(param)u=param}catch(_e){}if(/^https?:/i.test(u))out.push({url:u,quality:q,size:size})}}catch(_e){}}else if(label.indexOf("resume cloud")>=0){var cr=await fetchText(as[i].url,{referer:r.url}),ca=anchors(cr.text,cr.url).find(function(z){return /download|success/i.test(z.text)||/btn-success/i.test(cr.text)});if(ca&&/^https?:/i.test(ca.url))out.push({url:ca.url,quality:q,size:size})}else if(label.indexOf("cloud download")>=0&&/^https?:/i.test(as[i].url)){out.push({url:as[i].url,quality:q,size:size})}}return out}
function gatewayHost(url){try{var h=new URL(url).hostname.toLowerCase();return h==="driveseed.org"||h==="cloud.unblockedgames.world"||h==="tech.unblockedgames.world"||h==="urlflix.xyz"}catch(_e){return false}}
function redirectHint(html,base){var src=String(html||""),m=src.match(/<meta[^>]+http-equiv=["']refresh["'][^>]+content=["'][^"']*url=([^"']+)["']/i)||src.match(/(?:window\.)?location(?:\.href|\.replace)?\s*(?:=|\()\s*["']([^"']+)/i);return m?abs(m[1],base):""}
async function gatewayToDrive(seed,referer){var queue=[{url:seed,referer:referer}],seen={},steps=0;while(queue.length&&steps++<6){var row=queue.shift(),u=row&&row.url;if(!u||seen[u])continue;seen[u]=1;if(/driveseed\.org/i.test(u))return u;if(/unblockedgames\.world/i.test(u)){var b=await bypass(u);if(b&&!seen[b])queue.unshift({url:b,referer:u});continue}var r=await fetchText(u,{referer:row.referer||referer});if(!r.ok)continue;var hinted=redirectHint(r.text,r.url);if(hinted&&gatewayHost(hinted)&&!seen[hinted])queue.push({url:hinted,referer:r.url});var aa=anchors(r.text,r.url);for(var i=0;i<aa.length;i++){var v=aa[i].url;if(gatewayHost(v)&&!seen[v])queue.push({url:v,referer:r.url})}}return""}
async function modLinks(url,referer,q){var r=await fetchText(url,{referer:referer}),as=anchors(r.text,r.url),targets=[];for(var i=0;i<as.length;i++)if(gatewayHost(as[i].url))targets.push(as[i].url);targets=[...new Set(targets)];var out=[];for(var j=0;j<targets.length&&out.length<8;j++){var u=await gatewayToDrive(targets[j],r.url);if(!u)continue;var ds=await driveseed(u);for(var k=0;k<ds.length&&out.length<8;k++){out.push({name:"MoviesMod",title:"MoviesMod - "+(ds[k].quality||q||"HD")+(ds[k].size?" ["+ds[k].size+"]":""),url:ds[k].url,quality:ds[k].quality||q||"HD",provider:"moviesmod",isDirect:true})}}return out}
async function resolve(args){var q=request(args);if(!q)return null;var md=await metadata(q),needle=title(md,q);if(!needle)return[];var query=needle+(q.type==="tv"?" "+q.season:""),search=c.base+"/search/"+encodeURIComponent(query),sr=await fetchText(search,{}),page=firstArticle(sr.text,sr.url||search);if(!page)return[];var detail=await fetchText(page,{referer:search});if(!detail.ok)return[];var links=candidateDownloadLinks(detail.text,detail.url,q),out=[];for(var i=0;i<links.length&&out.length<8;i++){var rows=await modLinks(links[i].url,detail.url,links[i].quality);for(var j=0;j<rows.length&&out.length<8;j++){var x=rows[j];if(q.type==="tv"){x.season=q.season;x.episode=q.episode}out.push(x)}}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"moviesmod",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg={"base":"https://moviesmod.ai.in","userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
    cfg.update(dict(options or {})); cfg["base"]=str(cfg.get("base") or "").rstrip("/")
    js=WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,ensure_ascii=False,separators=(",",":")))
    return replace_managed_fix(text,MANAGED_FIX_ID,js.lstrip(),data={
        "runtimeFamily":"moviesmod-search-download-driveseed-v1",
        "identity":"core-tmdb-imdb-or-title-provider-search",
        "semanticLanes":["movie","tv"],
        "runtimeResolverRegistration":True,
        "legacyExecutableSeed":False,
        "upstreamJsExecuted":False,
    })

if __name__=="__main__":
    raise SystemExit("patch module only")
