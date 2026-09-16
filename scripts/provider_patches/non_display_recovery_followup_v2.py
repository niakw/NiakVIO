#!/usr/bin/env python3
"""Second-stage clean-room recovery runtime for remaining non-display routes.

This module is a shared implementation helper. Provider-owned wrapper modules
supply static MANAGED_FIX_ID values required by the v3 materializer.
"""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix

MARKER = "NIAKVIO_NON_DISPLAY_RECOVERY_FOLLOWUP_V2"
SUPPORTED = {"animesama-co", "neko-sama", "sekai", "voiranime-rip"}

WRAPPER = r'''
/* NIAKVIO_NON_DISPLAY_RECOVERY_FOLLOWUP_V2 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function arr(v){return Array.isArray(v)?v:[]}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function uniq(v){var out=[],seen={};for(var i=0;i<v.length;i++){var x=s(v[i]),k=norm(x);if(!x||!k||seen[k])continue;seen[k]=1;out.push(x)}return out}
function abs(v,b){try{return new URL(s(v).replace(/&amp;/gi,"&").replace(/&#0*38;/gi,"&").replace(/\\\//g,"/"),b).toString()}catch(_e){return""}}
function score(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 140;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 90;var aw=a.split(/\s+/),bw=b.split(/\s+/),n=0;for(var i=0;i<bw.length;i++)if(bw[i].length>2&&aw.indexOf(bw[i])>=0)n+=16;return n}
function request(a){var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||ctx.canonicalMediaType||ctx.semanticType||a[1]||"tv").toLowerCase();if(raw==="series"||raw==="anime")raw="tv";var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;var season=Number((o&&o.season)!=null?o.season:a[2])||1,episode=Number((o&&o.episode)!=null?o.episode:a[3])||1,m=(o&&o.tmdbMetadata)||ctx.tmdbMetadata||{},titles=uniq([o&&o.title,o&&o.name,m.title,m.name,m.original_title,m.original_name,ctx.title]);return{tmdbId:id,type:raw==="movie"?"movie":"tv",season:season,episode:episode,titles:titles}}
async function metadata(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type}),m=z&&z.metadata||{};q.titles=uniq(q.titles.concat([m.title,m.name,m.original_title,m.original_name]));var alt=m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length&&q.titles.length<12;i++)q.titles=uniq(q.titles.concat([alt[i]&&(alt[i].title||alt[i].name)]))}}catch(_e){}return q}
function headers(ref,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function resp(url,opt){try{var o=opt&&typeof opt==="object"?Object.assign({},opt):{};o.headers=Object.assign(headers(o.referer||c.base+"/",o.accept),o.headers||{});delete o.referer;delete o.accept;var r=await g.fetch(url,o);if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text(),status:r.status}}catch(_e){return null}}
function outRow(url,name,language,ref){return{url:url,provider:c.provider,name:name,title:name,language:language||"VOSTFR",quality:"HD",headers:{Referer:ref||c.base+"/"}}}
async function sibnet(shell,ref,name,language){var sh=await resp(shell,{referer:ref});if(!sh)return[];var m=sh.text.match(/player\.src\s*\(\s*\[\s*\{\s*src\s*:\s*["']([^"']+\.mp4[^"']*)["']/i)||sh.text.match(/["'](\/v\/[^"']+\.mp4[^"']*)["']/i);if(!m)return[];var u=abs(m[1],sh.url);return u?[outRow(u,name,language,sh.url)]:[]}
async function crawl(urls,ref,name,language){var clean=[],seen={};for(var i=0;i<urls.length;i++){var u=abs(urls[i],ref||c.base);if(!u||seen[u])continue;seen[u]=1;clean.push(u)}var direct=[];for(var j=0;j<clean.length&&direct.length<c.maxStreams;j++){if(/video\.sibnet\.ru\/shell\.php\?videoid=\d+/i.test(clean[j])){var sr=await sibnet(clean[j],ref,name,language);direct=direct.concat(sr)}}if(direct.length)return direct.slice(0,c.maxStreams);var rows=[];if(typeof _crawlDirectMedia==="function")try{rows=await _crawlDirectMedia(clean,ref||c.base+"/",4)}catch(_e){rows=[]}var out=[];for(var z=0;z<arr(rows).length&&out.length<c.maxStreams;z++){var r=rows[z];if(r&&/^https?:\/\//i.test(s(r.url))){r.provider=c.provider;r.name=r.name||name;r.title=r.title||name;r.language=r.language||language||"VOSTFR";r.quality=r.quality||"HD";r.headers=Object.assign({Referer:ref||c.base+"/"},r.headers||{});out.push(r)}}return out}
function playerUrls(html,base){var out=[],seen={},m,re=/<iframe[^>]+src=["']([^"']+)["']/gi;while((m=re.exec(html||""))!==null){var u=abs(m[1],base);if(u&&!seen[u]){seen[u]=1;out.push(u)}}var js=/["']?(?:vostfr|vf)["']?\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi;while((m=js.exec(html||""))!==null){var v=abs(m[1],base);if(v&&!seen[v]){seen[v]=1;out.push(v)}}return out}

function ascoLinks(html,base){var out=[],seen={},m,re=/href=["']([^"']*\/anime\/(\d+)-([^"'?#]+)\.html)["']/gi;while((m=re.exec(html||""))!==null){var u=abs(m[1],base);if(u&&!seen[u]){seen[u]=1;out.push({url:u,slug:m[3]})}}return out}
async function asco(q){q=await metadata(q);if(!q.titles.length)return[];var queries=q.titles.slice(0,10),fallback=[];for(var i=0;i<q.titles.length&&fallback.length<10;i++){var w=norm(q.titles[i]).split(/\s+/).filter(function(x){return x.length>=3});if(w.length){fallback.push(w[0]);if(w.length>1)fallback.push(w[w.length-1]);if(w.length>2)fallback.push(w.slice(0,2).join(" "))}}queries=uniq(queries.concat(fallback)).slice(0,18);var cand=[],seen={};for(var qi=0;qi<queries.length;qi++){var r=await resp(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"query="+encodeURIComponent(queries[qi]),referer:c.base+"/"});if(!r)continue;var links=ascoLinks(r.text,c.base);for(var li=0;li<links.length;li++){var best=0;for(var ti=0;ti<q.titles.length;ti++)best=Math.max(best,score(links[li].slug.replace(/-/g," "),q.titles[ti]));if(best>=55&&!seen[links[li].url]){seen[links[li].url]=1;cand.push({url:links[li].url,score:best})}}if(cand.some(function(x){return x.score>=120}))break}cand.sort(function(a,b){return b.score-a.score});for(var ci=0;ci<cand.length&&ci<8;ci++){var root=cand[ci].url.replace(/\.html$/i,""),ep=root+"/saison-"+q.season+"/episode-"+q.episode+".html",eh=await resp(ep,{referer:cand[ci].url});if(!eh)continue;var players=playerUrls(eh.text,eh.url);var rows=await crawl(players,eh.url,"AnimeSamaCo","VOSTFR");if(rows.length)return rows}return[]}

function nekoEpisodes(html){var out=[],seen={},start=(html||"").indexOf("eplister");if(start<0)return out;var end=(html||"").indexOf("</ul>",start),block=end>=0?html.slice(start,end):html.slice(start,start+100000),re=/<a[^>]+href=["']([^"']*episode-(\d+)(?:-saison-(\d+))?[^"'?]*)["'][^>]*>[\s\S]{0,500}?<(?:div|span)[^>]*class=["'][^"']*epl-num[^"']*["'][^>]*>\s*([^<]{0,30})<\/(?:div|span)>/gi,m;while((m=re.exec(block))!==null){var u=abs(m[1],c.base),n=parseInt(s(m[4]),10)||parseInt(m[2],10);if(u&&n&&!seen[n]){seen[n]=1;out.push({url:u,num:n})}}return out}
async function neko(q){q=await metadata(q);for(var ti=0;ti<q.titles.length&&ti<6;ti++){var sl=slug(q.titles[ti]),urls=[c.base+"/anime/"+sl+"-saison-"+q.season+"/",c.base+"/anime/"+sl+"/"];var sh=await resp(c.base+"/?s="+encodeURIComponent(q.titles[ti]),{referer:c.base+"/"});if(sh){var re=/<a[^>]+href=["']([^"']*\/anime\/[^"']+)["']/gi,m,scored=[];while((m=re.exec(sh.text))!==null){var u=abs(m[1],c.base),path="";try{path=new URL(u).pathname}catch(_e){}var baseSlug=path.replace(/.*\/anime\//,"").replace(/\/$/,""),clean=baseSlug.replace(/-saison-\d+$/,"").replace(/-/g," "),v=score(clean,q.titles[ti]);if(new RegExp("-saison-"+q.season+"(?:/|$)","i").test(path))v+=70;if(/(?:^|-)(?:oavs?|films?|movie|special|recap)(?:-|\/|$)/i.test(baseSlug))v-=100;scored.push({url:u,score:v})}scored.sort(function(a,b){return b.score-a.score});for(var si=0;si<scored.length&&si<8;si++)urls.push(scored[si].url)}urls=uniq(urls);for(var ui=0;ui<urls.length&&ui<10;ui++){var ph=await resp(urls[ui],{referer:c.base+"/"});if(!ph)continue;var eps=nekoEpisodes(ph.text),ep=null;for(var ei=0;ei<eps.length;ei++)if(eps[ei].num===q.episode){ep=eps[ei];break}if(!ep)continue;var eh=await resp(ep.url,{referer:ph.url});if(!eh)continue;var buttons=[],br=/loadMi\(\{\s*value\s*:\s*['"]([A-Za-z0-9+/=]{16,})['"]\s*\}\)/g,bm;while((bm=br.exec(eh.text))!==null&&buttons.length<12){try{var dec=atob(bm[1]),sm=dec.match(/src=["']([^"']+)["']/i),u=sm?abs(sm[1],c.base):"";if(u)buttons.push(u)}catch(_e){}}var players=[];for(var bi=0;bi<buttons.length&&bi<8;bi++){var bp=await resp(buttons[bi],{referer:eh.url});if(!bp)continue;players=players.concat(playerUrls(bp.text,bp.url))}var rows=await crawl(players,eh.url,"Neko-Sama","VOSTFR");if(rows.length)return rows}}}return[]}

function b64(v){try{return atob(v)}catch(_e){return""}}
async function sekai(q){q=await metadata(q);var sm=await resp(c.base+"/sitemap.xml",{referer:c.base+"/"});if(!sm)return[];var slugs=[],lm,re=/<loc>([^<]+)<\/loc>/gi;while((lm=re.exec(sm.text))!==null){try{var p=new URL(abs(lm[1],c.base)).pathname.replace(/^\/+|\/+$/g,"");if(p&&p!=="android"&&p.indexOf(".")<0)slugs.push(p)}catch(_e){}}var scored=[];for(var si=0;si<slugs.length;si++){var best=0;for(var ti=0;ti<q.titles.length;ti++)best=Math.max(best,score(slugs[si].replace(/-/g," "),q.titles[ti]));if(best>=45)scored.push({slug:slugs[si],score:best})}scored.sort(function(a,b){return b.score-a.score});for(var ci=0;ci<scored.length&&ci<5;ci++){var ph=await resp(c.base+"/"+scored[ci].slug,{referer:c.base+"/"});if(!ph)continue;var constants={},cr=/(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*atob\(\s*["']([^"']+)["']\s*\)/g,cm;while((cm=cr.exec(ph.text))!==null)constants[cm[1]]=b64(cm[2]);var sib="";for(var k in constants)if(/sibnet/i.test(constants[k])&&/shell\.php/i.test(constants[k])){sib=constants[k];break}var players=[],ar=/(episode(?:HD|FHD|VF|VOSTFR)?)\s*\[\s*(\d+)\s*\]\s*=\s*([^;\n]+)/gi,am;while((am=ar.exec(ph.text))!==null){if(Number(am[2])!==q.episode)continue;var rhs=am[3].trim(),dm=rhs.match(/^["'](\d+)["']$/);if(dm&&sib){players.push(sib+dm[1]);continue}var parts=rhs.split("+"),u="",ok=true;for(var pi=0;pi<parts.length;pi++){var p=parts[pi].trim(),qm=p.match(/^["']([\s\S]*)["']$/);if(qm)u+=qm[1];else if(constants[p]!=null)u+=constants[p];else if(/^\d+$/.test(p))u+=p;else{ok=false;break}}if(ok&&/^https?:\/\//i.test(u))players.push(u)}var rows=await crawl(players,ph.url,"Sekai","VOSTFR");if(rows.length)return rows}return[]}

async function vrip(q){q=await metadata(q);var roots=[];for(var ti=0;ti<q.titles.length&&ti<8&&!roots.length;ti++){var sr=await resp(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"query="+encodeURIComponent(q.titles[ti]),referer:c.base+"/"});if(!sr)continue;var re=/href=["']([^"']+)["']/gi,m,sc=[];while((m=re.exec(sr.text))!==null){var u=abs(m[1],c.base);try{var p=new URL(u);if(p.hostname!==new URL(c.base).hostname||p.pathname.split("/").filter(Boolean).length!==1)continue;var sl=p.pathname.replace(/^\/+|\/+$/g,""),v=score(sl.replace(/-/g," "),q.titles[ti]);if(v>=45)sc.push({url:u,score:v})}catch(_e){}}sc.sort(function(a,b){return b.score-a.score});roots=sc.slice(0,6)}for(var ri=0;ri<roots.length;ri++){var root=roots[ri].url.replace(/\/$/,""),ep=root+"/saison-"+q.season+"/episode-"+q.episode+"/",eh=await resp(ep,{referer:roots[ri].url});if(!eh)continue;var players=playerUrls(eh.text,eh.url);var rows=await crawl(players,eh.url,"VoirAnime.rip","VOSTFR");if(rows.length)return rows}return[]}

async function resolve(a,_ctx){var q=request(a);if(!q||q.type==="movie")return null;if(c.provider==="animesama-co")return asco(q);if(c.provider==="neko-sama")return neko(q);if(c.provider==="sekai")return sekai(q);if(c.provider==="voiranime-rip")return vrip(q);return null}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:c.provider,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    provider = str(cfg.get("provider") or "").strip().casefold().replace("_", "-")
    if provider not in SUPPORTED:
        raise ValueError(f"unsupported V2 non-display recovery provider: {provider!r}")
    defaults = {
        "animesama-co": "https://animesama.co",
        "neko-sama": "https://animes-sama.su",
        "sekai": "https://sekai.one",
        "voiranime-rip": "https://voiranime.rip",
    }
    payload = {
        "provider": provider,
        "base": str(cfg.get("base") or defaults[provider]).rstrip("/"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 4), 8)),
    }
    fix_id = "PROVIDER." + provider.upper() + ".NONDISPLAY.RECOVERY.V2"
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(text, fix_id, wrapper, data={
        "runtime": payload,
        "scope": "remaining-live-non-display-followup",
        "upstreamJsExecuted": False,
        "runtimeResolverRegistration": True,
        "sibnetShellResolution": True,
        "evidenceRuns": [35129779152, 35129997763, 35130125165, 35130324423],
    })
