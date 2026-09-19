#!/usr/bin/env python3
"""NiakVIO-owned 4KHDHub catalogue -> HubCloud runtime.

The current provider contract is:
4khdhub.one search -> movie/series detail -> download/episode item ->
HubCloud/HubDrive -> direct workers/R2 media.

TMDB metadata remains Core-owned. Upstream provider JavaScript is never executed.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.4KHDHUB.RUNTIME.V1"
MARKER = "NIAKVIO_4KHDHUB_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_4KHDHUB_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function norm(v){var x=s(v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/\[[^\]]*\]/g," ").replace(/\b(the|a|an|directors?|cut)\b/g," ").replace(/[^a-z0-9]+/g," ").replace(/\s+/g," ").trim()}
function visible(v){var src=String(v==null?"":v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return s(out).replace(/&(?:nbsp|amp|quot|#0*39|apos);/gi," ").replace(/\s+/g," ").trim()}
function attr(tag,key){var m=s(tag).match(new RegExp("\\b"+key+"\\s*=\\s*[\"']([^\"']+)[\"']","i"));return m?m[1].replace(/&amp;/gi,"&"):""}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_e){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_e){return""}}
function uniq(rows,key){var out=[],seen={};for(var i=0;i<(rows||[]).length;i++){var x=rows[i],k=key?key(x):s(x);if(k&&!seen[k]){seen[k]=1;out.push(x)}}return out}
function headers(ref){var h={"User-Agent":c.ua,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9"};if(ref)h.Referer=ref;return h}
async function fetchText(url,ref){try{var r=await g.fetch(url,{headers:headers(ref),redirect:"follow"});if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text(),status:r.status}}catch(_e){return null}}
function req(a){var f=a[0],o=f&&typeof f==="object"&&!Array.isArray(f)?f:null,x={};try{x=g.__nuvioMediaContext||{}}catch(_e){}var t=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||a[1]||x.canonicalMediaType||x.mediaType||"movie").toLowerCase();if(t==="series")t="tv";if(t!=="movie"&&t!=="tv")return null;var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof f==="string"?f:"")||x.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;var se=Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:x.season))||1,ep=Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:x.episode))||1;return{tmdbId:id,type:t,season:se,episode:ep}}
async function meta(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type}),m=z&&z.metadata||z;if(m&&typeof m==="object")return m}}catch(_e){}try{var x=g&&g.__nuvioMediaContext||{},m2=x.tmdbMetadata||x.fixtureMetadata||x.metadata;if(m2&&typeof m2==="object")return m2}catch(_e2){}return null}
function metaView(m,q){var title=s(m&&(q.type==="tv"?(m.name||m.original_name):(m.title||m.original_title))),date=s(m&&(q.type==="tv"?(m.first_air_date||m.release_date):(m.release_date||m.first_air_date))),year=date.slice(0,4);return{title:title,year:year}}
function base(){try{var m=typeof NIAKVIO_PROVIDER_MODEL!=="undefined"&&NIAKVIO_PROVIDER_MODEL,u=s(m&&(m.officialSite||m.knownSite));if(u)return u.replace(/\/$/,"")}catch(_e){}return s(c.base).replace(/\/$/,"")}
function anchors(html,b){var out=[],re=/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<500){var u=abs(attr(m[1],"href"),b);if(u)out.push({url:u,text:visible(m[2]),tag:m[0],index:m.index})}return out}
function classText(html,cls){var re=new RegExp("<[a-z0-9]+\\b[^>]*class=[\"'][^\"']*\\b"+cls.replace(/[-/\\^$*+?.()|[\]{}]/g,"\\$&")+"\\b[^\"']*[\"'][^>]*>([\\s\\S]*?)<\\/[a-z0-9]+>","i"),m=re.exec(html||"");return m?visible(m[1]):""}
function classBlocks(html,cls){var esc=cls.replace(/[-/\\^$*+?.()|[\]{}]/g,"\\$&"),re=new RegExp("<(?:div|article|li|a)\\b[^>]*class=[\"'][^\"']*\\b"+esc+"\\b[^\"']*[\"'][^>]*>","gi"),starts=[],m;while((m=re.exec(html||""))!==null)starts.push({at:m.index,tag:m[0]});var out=[];for(var i=0;i<starts.length;i++){var end=i+1<starts.length?starts[i+1].at:Math.min(String(html||"").length,starts[i].at+12000);out.push({html:String(html||"").slice(starts[i].at,end),tag:starts[i].tag})}return out}
function scoreTitle(want,label){var a=norm(want).split(/\s+/).filter(Boolean),b=norm(label),hit=0;if(!a.length||!b)return 0;if(b===norm(want))return 1;for(var i=0;i<a.length;i++)if(b.indexOf(a[i])>=0)hit++;return hit/a.length}
async function detail(q,m){var b=base();if(!b||!m.title)return null;var query=q.type==="tv"?m.title+" Season "+q.season:(m.title+(m.year?" "+m.year:""));var sr=await fetchText(b+"/?s="+encodeURIComponent(query),b+"/");if(!sr)return null;var cards=classBlocks(sr.text,"movie-card"),best=null;for(var i=0;i<cards.length;i++){var card=cards[i],title=classText(card.html,"movie-card-title")||visible(card.html),format=classText(card.html,"movie-card-format"),metaText=classText(card.html,"movie-card-meta"),href=attr(card.tag,"href"),aa=anchors(card.html,sr.url);if(!href&&aa.length)href=aa[0].url;href=abs(href,sr.url);if(!href)continue;if(q.type==="tv"&&!/series/i.test(format))continue;if(q.type==="movie"&&!/movies?/i.test(format))continue;var sc=scoreTitle(m.title,title),ym=metaText.match(/\b(19|20)\d{2}\b/),y=ym?Number(ym[0]):0,w=Number(m.year)||0;if(w&&y){if(y===w)sc+=0.35;else if(Math.abs(y-w)>1)sc-=0.5}if(q.type==="tv"){var sm=title.match(/(?:season\s*|s)(\d+)/i);if(sm&&Number(sm[1])===q.season)sc+=0.4;else if(sm)sc-=0.6}if(!best||sc>best.score)best={url:href,score:sc,title:title}}if(!best||best.score<0.7)return null;return await fetchText(best.url,sr.url)}
function releaseBlocks(html,q){if(q.type==="movie")return classBlocks(html,"download-item").map(function(x){return x.html});var eps=classBlocks(html,"episode-download-item"),out=[];for(var i=0;i<eps.length;i++){var label=classText(eps[i].html,"episode-file-title")||visible(eps[i].html),m=label.match(/(?:^|\\b)S(\\d{1,2})E(\\d{1,3})(?:\\b|$)/i);if(!m)m=label.match(/Season\\s*(\\d{1,2})[\\s\\S]{0,40}?Episode\\s*(\\d{1,3})/i);if(m&&Number(m[1])===q.season&&Number(m[2])===q.episode)out.push(eps[i].html)}return out}
function quality(v){var x=s(v).toLowerCase();if(/2160p|\b4k\b|\buhd\b/.test(x))return"2160p";var m=x.match(/\b(1080|720|480)p\b/);return m?m[1]+"p":"1080p"}
function size(v){var m=s(v).match(/([\d.]+)\s*(GB|MB|KB)/i);return m?m[1]+" "+m[2].toUpperCase():""}
function b64(v){try{var fn=(g&&g.atob)||((typeof atob==="function")?atob:null);return fn?fn(s(v)):""}catch(_e){return""}}
function rot13(v){return s(v).replace(/[a-zA-Z]/g,function(ch){var c=ch.charCodeAt(0)+(13),z=ch<="Z"?90:122;return String.fromCharCode(c<=z?c:c-26)})}
async function decodeRedirect(url){if(/hubcloud|hubdrive/i.test(url))return url;var p=await fetchText(url,base()+"/");if(!p)return url;var m=p.text.match(/[\"']o[\"']\s*,\s*[\"']([^\"']+)[\"']/)||p.text.match(/'o','([^']+)'/);if(!m)return url;try{var raw=b64(b64(m[1])),decoded=b64(rot13(raw)),obj=JSON.parse(decoded),u=obj&&obj.o?b64(obj.o).trim():"";return u||url}catch(_e){return url}}
async function hubFromBlock(block,detailUrl){var aa=anchors(block,detailUrl);for(var i=0;i<aa.length;i++){var blob=(aa[i].text+" "+aa[i].url).toLowerCase();if(blob.indexOf("hubcloud")>=0)return await decodeRedirect(aa[i].url);if(/green(?:mount)?motors\./i.test(blob)){var gm=await decodeRedirect(aa[i].url);if(gm)return gm}if(blob.indexOf("hubdrive")>=0){var hd=await decodeRedirect(aa[i].url),page=await fetchText(hd,detailUrl);if(!page)continue;var hh=anchors(page.text,page.url);for(var j=0;j<hh.length;j++)if((hh[j].text+" "+hh[j].url).toLowerCase().indexOf("hubcloud")>=0)return abs(hh[j].url,page.url)}}return""}
function directVideo(u){var h=host(u);return h.endsWith(".workers.dev")||h.endsWith(".r2.cloudflarestorage.com")||h.endsWith(".cloudflarestorage.com")||h.endsWith(".r2.dev")||h.endsWith(".googleusercontent.com")||h.endsWith(".googlevideo.com")||h.indexOf("pixel.hubcloud.")===0}
async function hubStreams(url,fallback){var p=await fetchText(url,url);if(!p)return[];var html=p.text,cur=p.url,m=html.match(/var\s+url\s*=\s*[\"']([^\"']+)[\"']/i);if(!m){var dm=/<a\b[^>]*id=[\"']download[\"'][^>]*href=[\"']([^\"']+)[\"']/i.exec(html);if(dm)m=[dm[0],dm[1]]}if(m){var next=abs(m[1],cur),p2=await fetchText(next,cur);if(p2){html=p2.text;cur=p2.url}}var title=classText(html,"card-header")||visible((html.match(/<title\b[^>]*>[\s\S]*?<\/title>/i)||[""])[0])||fallback,aa=anchors(html,cur),out=[];for(var i=0;i<aa.length;i++)if(directVideo(aa[i].url))out.push({url:aa[i].url,title:title,quality:quality(title),size:size(title),referer:cur});if(!out.length)try{if(typeof _crawlDirectMedia==="function"){var rows=await _crawlDirectMedia([url],url,3);for(var j=0;j<(rows||[]).length;j++){var r=rows[j]||{};if(/^https?:/i.test(s(r.url)))out.push({url:r.url,title:s(r.title||r.name)||title,quality:s(r.quality)||quality(title),size:s(r.size)||size(title),referer:url})}}}catch(_e){}return uniq(out,function(x){return x.url})}
async function resolve(a){var q=req(a);if(q===null)return null;if(!q)return[];var md=await meta(q),m=metaView(md,q);if(!m.title)return[];var page=await detail(q,m);if(!page)return[];var blocks=releaseBlocks(page.text,q),out=[],seen={};for(var i=0;i<blocks.length&&out.length<c.maxStreams;i++){var label=classText(blocks[i],"file-title")||classText(blocks[i],"episode-file-title")||visible(blocks[i]),hub=await hubFromBlock(blocks[i],page.url);if(!hub)continue;var rows=await hubStreams(hub,label);for(var j=0;j<rows.length&&out.length<c.maxStreams;j++){var r=rows[j];if(seen[r.url])continue;seen[r.url]=1;var ident=m.title+(m.year?" ("+m.year+")":"")+(q.type==="tv"?" S"+String(q.season).padStart(2,"0")+"E"+String(q.episode).padStart(2,"0"):"");out.push({name:"4KHDHub | "+r.quality,title:ident+" | "+r.title,filename:r.title,sourceName:r.title,url:r.url,quality:r.quality,size:r.size,language:"multi",provider:"4khdhub",isDirect:true,headers:headers(r.referer||page.url)})}}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"4khdhub",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://4khdhub.one",
        "maxStreams": 8,
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    cfg["maxStreams"] = max(1, min(int(cfg.get("maxStreams") or 8), 12))
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "4khdhub-search-detail-hubcloud-v1",
            "identity": "core-tmdb-title-year-season-episode",
            "semanticLanes": ["movie", "tv"],
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
