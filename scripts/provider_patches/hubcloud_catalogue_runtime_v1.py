#!/usr/bin/env python3
"""Owned clean-room HubCloud-family catalogue resolver.

Knowledge source: persisted provider LKG contracts only. No upstream JavaScript is
embedded or executed. The catalogue origin always comes from NIAKVIO_PROVIDER_MODEL
so Domain Refresh remains the sole owner of provider-domain authority.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.HUBCLOUD.CATALOGUE.RUNTIME.V1"
MARKER = "NIAKVIO_HUBCLOUD_CATALOGUE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_HUBCLOUD_CATALOGUE_RUNTIME_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function diag(stage,detail){try{var row={stage:s(stage).slice(0,64),lane:"",providerId:c.provider,stepIndex:-1,route:s(detail).slice(0,220)};g.__nuvioProviderValueTraceV18=row;var hist=Array.isArray(g.__nuvioProviderValueTraceHistoryV21)?g.__nuvioProviderValueTraceHistoryV21:[];hist.push(row);while(hist.length>48)hist.shift();g.__nuvioProviderValueTraceHistoryV21=hist}catch(_e){}}
function model(){try{return typeof NIAKVIO_PROVIDER_MODEL!=="undefined"?NIAKVIO_PROVIDER_MODEL:null}catch(_e){return null}}
function base(){var m=model()||{},u=s(m.officialSite||m.knownSite||"");return /^https?:\/\//i.test(u)?u.replace(/\/$/,""):""}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/\[[^\]]*\]/g," ").replace(/\b(the|a|an|directors?|cut)\b/g," ").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function score(a,b){var aa=norm(a).split(" ").filter(Boolean),bb=new Set(norm(b).split(" ").filter(Boolean));if(!aa.length)return 0;var n=0;for(var i=0;i<aa.length;i++)if(bb.has(aa[i]))n++;return n/aa.length}
function abs(url,origin){try{return new URL(s(url),origin).toString()}catch(_e){return""}}
function meta(args){var ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var md=ctx.tmdbMetadata||{};if(md&&md.state==="ok"&&md.metadata)md=md.metadata;var type=s(args&&args[1]||ctx.canonicalMediaType||"movie").toLowerCase();var title=s(md.title||md.name||md.original_title||md.original_name||ctx.title),date=s(md.release_date||md.first_air_date||ctx.year);if(!title)return null;return{title:title,year:Number(date.slice(0,4))||0,type:type==="movie"?"movie":"tv",season:Number(args&&args[2])||1,episode:Number(args&&args[3])||1}}
function headers(ref){return{"User-Agent":c.userAgent,"Accept":"text/html,application/xhtml+xml,application/json,text/plain,*/*","Accept-Language":"en-US,en;q=0.8",Referer:ref||base()+"/"}}
async function fetchText(url,ref){var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||!r.ok)throw new Error("hubcloud_http_"+String(r&&r.status||0));return{body:await r.text(),url:r.url||url}}
function b64(v){try{return atob(s(v).replace(/\s+/g,""))}catch(_e){return""}}
function rot13(v){return s(v).replace(/[a-zA-Z]/g,function(ch){var cc=ch.charCodeAt(0)+13,edge=ch<="Z"?90:122;return String.fromCharCode(cc<=edge?cc:cc-26)})}
async function decodeRedirect(url,ref){if(/hubcloud|hubdrive/i.test(url))return url;try{var page=await fetchText(url,ref),m=page.body.match(/["']o["']\s*,\s*["']([^"']+)["']/)||page.body.match(/'o','([^']+)'/);if(!m)return page.url||url;var raw=b64(rot13(b64(b64(m[1])))),j=JSON.parse(raw);return j&&j.o?s(b64(j.o)):(page.url||url)}catch(_e){return url}}
function directVideo(url){try{var h=new URL(url).hostname.toLowerCase();return h.endsWith(".workers.dev")||h.endsWith(".r2.cloudflarestorage.com")}catch(_e){return false}}
function quality(v){var m=s(v).match(/\b(2160|1080|720|480)p?\b/i);return m?(m[1]==="2160"?"2160p":m[1]+"p"):"1080p"}
function cleanText(v){return s(v).replace(/<[^>]+>/g," ").replace(/&nbsp;/gi," ").replace(/&amp;/gi,"&").replace(/\s+/g," ").trim()}
function getCheerio(){try{return typeof require==="function"?require("cheerio-without-node-native"):null}catch(_e){return null}}
async function findPage(m){var root=base();if(!root)return"";var q=m.type==="tv"?(m.title+" Season "+m.season):(m.title+" "+(m.year||"")),res=await fetchText(root+"/?s="+encodeURIComponent(q),root+"/"),cheerio=getCheerio();if(!cheerio)return"";var $=cheerio.load(res.body),best=null;$(".movie-card").each(function(_i,el){var card=$(el),title=cleanText(card.find(".movie-card-title").text()),format=cleanText(card.find(".movie-card-format").text()),metaText=cleanText(card.find(".movie-card-meta").text()),href=card.attr("href")||card.find("a[href]").first().attr("href");if(!title||!href)return;if(m.type==="tv"&&!/series/i.test(format))return;if(m.type==="movie"&&!/movies?/i.test(format))return;var ym=metaText.match(/\b(19|20)\d{2}\b/),yr=ym?Number(ym[0]):0,sc=score(m.title,title);if(m.year&&yr===m.year)sc+=0.35;else if(m.year&&yr&&Math.abs(yr-m.year)>1)sc-=0.5;if(m.type==="tv"){var sm=title.match(/(?:season\s*|s)(\d+)/i);if(sm&&Number(sm[1])===m.season)sc+=0.4;else if(sm)sc-=0.6}if(!best||sc>best.score)best={url:abs(href,res.url||root),score:sc,title:title}});diag("hubcloud_catalogue_match","score="+String(best?best.score:0)+";selected="+(best&&best.score>=0.7?1:0));return best&&best.score>=0.7?best.url:""}
async function findHubCloud(item,pageUrl,$){var anchors=item.find("a[href]").toArray();for(var i=0;i<anchors.length;i++){var a=$(anchors[i]),href=a.attr("href"),label=cleanText(a.text())+" "+s(href);if(!href)continue;if(/hubcloud/i.test(label))return await decodeRedirect(abs(href,pageUrl),pageUrl);if(/hubdrive/i.test(label)){var hd=await decodeRedirect(abs(href,pageUrl),pageUrl);try{var p=await fetchText(hd,pageUrl),ch=getCheerio();if(!ch)continue;var $$=ch.load(p.body),found="";$$("a[href]").each(function(_j,el){if(found)return;var x=$$(el),h=x.attr("href")||"",t=cleanText(x.text())+" "+h;if(/hubcloud/i.test(t))found=abs(h,p.url||hd)});if(found)return found}catch(_e){}}}return""}
async function extractHubCloud(url,ref){try{var page=await fetchText(url,ref),current=page.url||url,body=page.body,m=body.match(/var\s+url\s*=\s*["']([^"']+)["']/),ch=getCheerio();if(!ch)return[];var $=ch.load(body),next=m&&m[1]?abs(m[1],current):abs($("#download").attr("href"),current);if(next&&next!==current){page=await fetchText(next,current);current=page.url||next;body=page.body;$=ch.load(body)}var out=[];$("a[href]").each(function(_i,el){var href=abs($(el).attr("href"),current);if(href&&directVideo(href)&&out.indexOf(href)<0)out.push(href)});diag("hubcloud_direct_media","count="+String(out.length));return out}catch(_e){diag("hubcloud_extract_error","error=1");return[]}}
async function detailItems(pageUrl,m){var page=await fetchText(pageUrl,base()+"/"),ch=getCheerio();if(!ch)return[];var $=ch.load(page.body),items=[];if(m.type==="movie"){$(".download-item").each(function(_i,el){items.push($(el))})}else{var season="S"+String(m.season).padStart(2,"0"),ep="Episode-"+String(m.episode).padStart(2,"0");$(".episode-item").each(function(_i,el){var row=$(el);if(cleanText(row.find(".episode-title").text()).indexOf(season)<0)return;row.find(".episode-download-item").each(function(_j,e){if(cleanText($(e).text()).indexOf(ep)>=0)items.push($(e))})})}var out=[];for(var i=0;i<items.length;i++){var cloud=await findHubCloud(items[i],page.url||pageUrl,$);if(!cloud)continue;var urls=await extractHubCloud(cloud,page.url||pageUrl);for(var j=0;j<urls.length;j++)out.push({url:urls[j],label:cleanText(items[i].text())})}return out}
async function resolve(args){var m=meta(args);if(!m)return[];var page=await findPage(m);if(!page)return[];var rows=await detailItems(page,m),out=[];for(var i=0;i<rows.length&&out.length<20;i++){out.push({url:rows[i].url,name:c.name+" - "+quality(rows[i].label),title:c.name+" - "+m.title,quality:quality(rows[i].label),provider:c.provider,headers:{"Referer":base()+"/","User-Agent":c.userAgent},isDirect:true})}diag("hubcloud_runtime_result","count="+String(out.length));return out}
try{g.__niakvioProviderRuntimeResolverV1={provider:c.provider,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    provider = str(cfg.get("provider") or "").strip().lower()
    if not provider:
        raise ValueError("hubcloud catalogue runtime requires provider")
    payload = {
        "provider": provider,
        "name": str(cfg.get("name") or provider).strip(),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 NiakVIO/4"),
    }
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtime": payload,
            "runtimeFamily": "catalogue-hubdrive-hubcloud-v1",
            "catalogueDomainAuthority": "NIAKVIO_PROVIDER_MODEL",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
            "coreFinalOutputOwnership": True,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
