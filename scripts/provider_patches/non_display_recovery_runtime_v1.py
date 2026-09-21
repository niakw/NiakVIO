#!/usr/bin/env python3
"""Clean-room recovery runtime for six current non-display regressions.

The upstream projects are evidence/knowledge only. This Lego re-implements the
small HTTP contracts proven by NiakVIO parity/route-delta runs without embedding
or executing upstream JavaScript.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MARKER = "NIAKVIO_NON_DISPLAY_RECOVERY_RUNTIME_V1"
SUPPORTED = {
    "animesama-co",
    "animevostfr",
    "coflix",
    "neko-sama",
    "sekai",
    "voiranime-rip",
}

WRAPPER = r'''
/* NIAKVIO_NON_DISPLAY_RECOVERY_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function arr(v){return Array.isArray(v)?v:[]}
function uniq(v){var o=[],seen={};for(var i=0;i<v.length;i++){var x=s(v[i]);if(!x)continue;var k=norm(x);if(!k||seen[k])continue;seen[k]=1;o.push(x)}return o}
function norm(v){var x=s(v).toLowerCase();try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.replace(/[^a-z0-9]+/g," ").trim()}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,base){try{return new URL(s(v).replace(/&amp;/gi,"&").replace(/&#0*38;/gi,"&").replace(/\\\//g,"/"),base).toString()}catch(_e){return""}}
function score(a,b){a=norm(a);b=norm(b);if(!a||!b)return 0;if(a===b)return 120;if(a.indexOf(b)>=0||b.indexOf(a)>=0)return 85;var aw=a.split(/\s+/),bw=b.split(/\s+/),n=0;for(var i=0;i<bw.length;i++)if(bw[i].length>2&&aw.indexOf(bw[i])>=0)n+=15;return n}
function strip(v){return s(v).replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ").replace(/&[^;]+;/g," ").replace(/\s+/g," ").trim()}
function request(a){var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}var raw=s((o&&(o.canonicalMediaType||o.semanticType||o.mediaType||o.type))||ctx.canonicalMediaType||ctx.semanticType||a[1]||"tv").toLowerCase();if(raw==="series")raw="tv";var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId).replace(/^tmdb:/i,"").split(":")[0];if(!/^\d+$/.test(id))return null;var season=Number((o&&o.season)!=null?o.season:a[2])||1,episode=Number((o&&o.episode)!=null?o.episode:a[3])||1;var m=(o&&o.tmdbMetadata)||ctx.tmdbMetadata||{},titles=uniq([o&&o.title,o&&o.name,m.title,m.name,m.original_title,m.original_name,ctx.title]);return{tmdbId:id,type:raw==="movie"?"movie":"tv",semantic:raw,season:season,episode:episode,titles:titles}}
async function metadata(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.type,tmdbNamespace:q.type}),m=z&&z.metadata||{};q.titles=uniq(q.titles.concat([m.title,m.name,m.original_title,m.original_name]));var alt=m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles);if(Array.isArray(alt))for(var i=0;i<alt.length&&q.titles.length<8;i++)q.titles=uniq(q.titles.concat([alt[i]&&(alt[i].title||alt[i].name)]))}}catch(_e){}return q}
function headers(ref,accept){var h={"User-Agent":c.userAgent,"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function resp(url,opt){try{var o=opt&&typeof opt==="object"?Object.assign({},opt):{};o.headers=Object.assign(headers(o.referer||c.base+"/",o.accept),o.headers||{});delete o.referer;delete o.accept;var r=await g.fetch(url,o);if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text(),status:r.status}}catch(_e){return null}}
async function jsonReq(url,opt){var r=await resp(url,Object.assign({accept:"application/json,text/plain,*/*"},opt||{}));if(!r)return null;try{return{url:r.url,data:JSON.parse(r.text)}}catch(_e){return null}}
function decorate(rows,name,language,ref){var out=[],seen={};for(var i=0;i<arr(rows).length&&out.length<c.maxStreams;i++){var r=rows[i];if(!r||!/^https?:\/\//i.test(s(r.url))||seen[r.url])continue;seen[r.url]=1;r.provider=c.provider;r.name=r.name||name;r.title=r.title||name;r.language=r.language||language||"VOSTFR";r.quality=r.quality||"HD";r.headers=Object.assign({Referer:ref||c.base+"/"},r.headers||{});out.push(r)}return out}
async function crawl(urls,ref,name,language){var clean=[],seen={};for(var i=0;i<urls.length;i++){var u=abs(urls[i],ref||c.base);if(!u||seen[u])continue;seen[u]=1;clean.push(u)}if(!clean.length)return[];var rows=[];if(typeof _crawlDirectMedia==="function")try{rows=await _crawlDirectMedia(clean,ref||c.base+"/",Math.max(2,Math.min(c.maxStreams,4)))}catch(_e){rows=[]}return decorate(rows,name,language,ref)}
function hrefs(html,re,base){var out=[],seen={},m;while((m=re.exec(html||""))!==null&&out.length<60){var u=abs(m[1],base);if(u&&!seen[u]){seen[u]=1;out.push(u)}}return out}

async function animeSamaCo(q){q=await metadata(q);if(!q.titles.length)return[];var candidates=[],seen={};for(var ti=0;ti<q.titles.length&&ti<6;ti++){var t=q.titles[ti],r=await resp(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"query="+encodeURIComponent(t),referer:c.base+"/"});if(!r)continue;var re=/<a[^>]+href=["']([^"']*\/anime\/[^"'#?]+\.html)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(r.text))!==null){var u=abs(m[1],c.base),label=strip(m[2]),sc=score(label||u,t);if(u&&!seen[u]&&sc>=35){seen[u]=1;candidates.push({url:u,score:sc,title:t})}}if(candidates.length>=4)break}candidates.sort(function(a,b){return b.score-a.score});for(var ci=0;ci<candidates.length&&ci<6;ci++){var root=candidates[ci].url.replace(/\.html(?:[?#].*)?$/i,""),ep=root+"/saison-"+q.season+"/episode-"+q.episode+".html",eh=await resp(ep,{referer:candidates[ci].url});if(!eh)continue;var shells=hrefs(eh.text,/["'](https?:\/\/video\.sibnet\.ru\/shell\.php\?videoid=\d+[^"']*)["']/gi,eh.url);var rows=await crawl(shells,eh.url,"AnimeSamaCo","VOSTFR");if(rows.length)return rows}return[]}

function pageCandidates(html,base,kind){var out=[],seen={},re=kind==="av"?/<a[^>]+href=["']([^"']*\/(?:animes|film)\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi:/<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null&&out.length<80){var u=abs(m[1],base),label=strip(m[2]);if(!u||seen[u])continue;seen[u]=1;out.push({url:u,label:label})}return out}
async function animeVostfr(q){q=await metadata(q);var roots=[];for(var ti=0;ti<q.titles.length&&ti<6&&!roots.length;ti++){var sr=await resp(c.base+"/?s="+encodeURIComponent(q.titles[ti]),{referer:c.base+"/"});if(!sr)continue;var rows=pageCandidates(sr.text,c.base,"av");rows.sort(function(a,b){return score(b.label||b.url,q.titles[ti])-score(a.label||a.url,q.titles[ti])});roots=rows.slice(0,5)}for(var ri=0;ri<roots.length;ri++){var rh=await resp(roots[ri].url,{referer:c.base+"/"});if(!rh)continue;var eps=hrefs(rh.text,/<a[^>]+href=["']([^"']*\/episode\/[^"']+)["']/gi,rh.url),target="";for(var ei=0;ei<eps.length;ei++){var u=eps[ei],low=u.toLowerCase(),n=String(q.episode),sn=String(q.season);if(low.indexOf("-"+sn+"-episode-"+n)>=0||low.indexOf("-saison-"+sn+"-episode-"+n)>=0||((q.season===1)&&low.indexOf("-episode-"+n)>=0)){target=u;break}}if(!target&&eps.length===1)target=eps[0];if(!target)continue;var eh=await resp(target,{referer:rh.url});if(!eh)continue;var tr=hrefs(eh.text,/(?:src|data-src)=["']([^"']*\?trembed=[^"']+)["']/gi,eh.url),embeds=[];for(var j=0;j<tr.length&&j<6;j++){var th=await resp(tr[j],{referer:eh.url});if(!th)continue;var inner=hrefs(th.text,/(?:src|data-src)=["']([^"']+)["']/gi,th.url);embeds=embeds.concat(inner)}var direct=await crawl(embeds,eh.url,"AnimeVOSTFR","VOSTFR");if(direct.length)return direct}return[]}

function coflixCandidates(html,title){var out=[],seen={},re=/href=["'](?:https?:\/\/coflix\.wiki)?\/film\/([^"'\/]+)\/ep-(\d+)["']/gi,m;while((m=re.exec(html||""))!==null){var sl=m[1],key=sl+"|"+m[2];if(seen[key])continue;seen[key]=1;var clean=sl.replace(/-(?:vf|vostfr|truefrench|french)$/i,"");out.push({slug:sl,epId:m[2],score:score(clean.replace(/-/g," "),title),lang:/vostfr$/i.test(sl)?"VOSTFR":"VF"})}out.sort(function(a,b){return b.score-a.score});return out}
async function coflix(q){q=await metadata(q);var candidates=[],seen={};for(var ti=0;ti<q.titles.length&&ti<3;ti++){var jr=await jsonReq(c.base+"/ajax/search/suggest?keyword="+encodeURIComponent(q.titles[ti]),{referer:c.base+"/"});var html=jr&&jr.data&&jr.data.html;if(!html)continue;var batch=coflixCandidates(html,q.titles[ti]);for(var bi=0;bi<batch.length;bi++){var k=batch[bi].slug;if(!seen[k]&&batch[bi].score>=30){seen[k]=1;candidates.push(batch[bi])}}}candidates.sort(function(a,b){return b.score-a.score});for(var ci=0;ci<candidates.length&&ci<6;ci++){var cand=candidates[ci],epId=cand.epId;if(q.type!=="movie"){var ph=await resp(c.base+"/film/"+cand.slug+"/",{referer:c.base+"/"});if(!ph)continue;var idm=ph.text.match(/id=["']watch-page["'][^>]*data-id=["'](\d+)["']/i)||ph.text.match(/data-id=["'](\d+)["']/i);if(!idm)continue;var lr=await jsonReq(c.base+"/ajax/episode/list-episode?movieId="+encodeURIComponent(idm[1]),{referer:ph.url});var lh=lr&&lr.data&&lr.data.html||"",re=/data-num=["'](\d+)["'][^>]*data-id=["'](\d+)["']|data-id=["'](\d+)["'][^>]*data-num=["'](\d+)["']/gi,m;epId="";while((m=re.exec(lh))!==null){var num=Number(m[1]||m[4]),eid=m[2]||m[3];if(num===q.episode){epId=eid;break}}if(!epId)continue}var pr=await jsonReq(c.base+"/ajax/episode/player?episode_id="+encodeURIComponent(epId),{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"episode_id="+encodeURIComponent(epId),referer:c.base+"/film/"+cand.slug+"/"}),msg=arr(pr&&pr.data&&pr.data.message),players=[];for(var pi=0;pi<msg.length;pi++){var u=msg[pi]&&msg[pi].server_link;if(u&&typeof u==="object")u=u.url;if(/^https?:\/\//i.test(s(u))&&!/kakaflix/i.test(u))players.push(u)}var rows=await crawl(players,c.base+"/film/"+cand.slug+"/","Coflix",cand.lang);if(rows.length)return rows}return[]}

function nekoEpisodes(html){var out=[],seen={},start=(html||"").indexOf("eplister");if(start<0)return out;var end=(html||"").indexOf("</ul>",start),block=end>=0?html.slice(start,end):html.slice(start,start+100000),re=/<a[^>]+href=["']([^"']*episode-(\d+)(?:-saison-(\d+))?[^"'?]*)["'][^>]*>[\s\S]{0,500}?<(?:div|span)[^>]*class=["'][^"']*epl-num[^"']*["'][^>]*>\s*([^<]{0,30})<\/(?:div|span)>/gi,m;while((m=re.exec(block))!==null){var u=abs(m[1],c.base),n=parseInt(s(m[4]),10)||parseInt(m[2],10);if(u&&n&&!seen[n]){seen[n]=1;out.push({url:u,num:n})}}return out}
async function nekoSeries(q){for(var ti=0;ti<q.titles.length&&ti<5;ti++){var sh=await resp(c.base+"/?s="+encodeURIComponent(q.titles[ti]),{referer:c.base+"/"});if(!sh)continue;var links=hrefs(sh.text,/<a[^>]+href=["']([^"']*\/anime\/[^"']+)["']/gi,c.base);links.sort(function(a,b){return score(b.replace(/.*\/anime\//,"").replace(/-/g," "),q.titles[ti])-score(a.replace(/.*\/anime\//,"").replace(/-/g," "),q.titles[ti])});for(var li=0;li<links.length&&li<8;li++){var h=await resp(links[li],{referer:c.base+"/"});if(!h)continue;var eps=nekoEpisodes(h.text);if(eps.some(function(e){return e.num===q.episode}))return eps;var root=links[li].replace(/\/$/,"").replace(/-(?:saison|saga)-\d+(?:-[^\/]*)?$/i,"");var subs=hrefs(h.text,/<a[^>]+href=["']([^"']*\/anime\/[^"']+)["']/gi,h.url);for(var si=0;si<subs.length&&si<6;si++){if(subs[si].indexOf(root+"-")!==0)continue;var hh=await resp(subs[si],{referer:h.url});if(!hh)continue;var ee=nekoEpisodes(hh.text);if(ee.some(function(e){return e.num===q.episode}))return ee}}}return[]}
async function neko(q){q=await metadata(q);var eps=await nekoSeries(q),ep=null;for(var i=0;i<eps.length;i++)if(eps[i].num===q.episode){ep=eps[i];break}if(!ep)return[];var eh=await resp(ep.url,{referer:c.base+"/"});if(!eh)return[];var b64=[],re=/loadMi\(\{\s*value\s*:\s*['"]([A-Za-z0-9+/=]{20,})['"]\s*\}\)/g,m;while((m=re.exec(eh.text))!==null&&b64.length<10)b64.push(m[1]);var players=[];for(var bi=0;bi<b64.length;bi++){try{var dec=atob(b64[bi]),sm=dec.match(/src=["']([^"']+)["']/i),u=sm?abs(sm[1],c.base):"";if(!u)continue;if(u.indexOf("animes-sama.su")>=0){var ph=await resp(u,{referer:ep.url});if(!ph)continue;var im=ph.text.match(/<iframe[^>]*class=["'][^"']*player-iframe[^"']*["'][^>]*(?:src|data-src)=["']([^"']+)["']/i)||ph.text.match(/<iframe[^>]*(?:src|data-src)=["']([^"']+)["']/i);if(im)u=abs(im[1],ph.url)}if(u)players.push(u)}catch(_e){}}return await crawl(players,ep.url,"Neko-Sama","VOSTFR")}

function b64(v){try{return atob(v)}catch(_e){return""}}
function evalSimple(expr,constants){var parts=String(expr||"").split("+"),out="";for(var i=0;i<parts.length;i++){var p=parts[i].trim(),m=p.match(/^["']([\s\S]*)["']$/);if(m){out+=m[1];continue}if(constants[p]!=null){out+=constants[p];continue}if(/^\d+$/.test(p)){out+=p;continue}return""}return out}
async function sekai(q){q=await metadata(q);var sm=await resp(c.base+"/sitemap.xml",{referer:c.base+"/"});if(!sm)return[];var slugs=[],re=/<loc>([^<]+)<\/loc>/gi,m;while((m=re.exec(sm.text))!==null){var u=abs(m[1],c.base),p="";try{p=new URL(u).pathname.replace(/^\/+|\/+$/g,"")}catch(_e){}if(p&&p!=="android"&&p.indexOf(".")<0)slugs.push(p)}var scored=[];for(var si=0;si<slugs.length;si++){var best=0;for(var ti=0;ti<q.titles.length;ti++)best=Math.max(best,score(slugs[si].replace(/-/g," "),q.titles[ti]));if(best>=40)scored.push({slug:slugs[si],score:best})}scored.sort(function(a,b){return b.score-a.score});for(var ci=0;ci<scored.length&&ci<4;ci++){var ph=await resp(c.base+"/"+scored[ci].slug,{referer:c.base+"/"});if(!ph)continue;var constants={},cr=/(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*atob\(\s*["']([^"']+)["']\s*\)/g,cm;while((cm=cr.exec(ph.text))!==null)constants[cm[1]]=b64(cm[2]);var sib="";for(var k in constants)if(constants[k].indexOf("sibnet")>=0&&constants[k].indexOf("php")>=0){sib=constants[k];break}var players=[],ar=new RegExp("(?:episode|episodeHD|episodeFHD|episodeVF|episodeVOSTFR)\\s*\\[\\s*"+q.episode+"\\s*\\]\\s*=\\s*([^;\\n]+)","gi"),am;while((am=ar.exec(ph.text))!==null){var rhs=am[1].trim(),dm=rhs.match(/^["'](\d+)["']$/),u="";if(dm&&sib)u=sib+dm[1];else u=evalSimple(rhs,constants);if(/^https?:\/\//i.test(u))players.push(u)}if(!players.length){var shells=hrefs(ph.text,/["'](https?:\/\/video\.sibnet\.ru\/shell\.php\?videoid=\d+[^"']*)["']/gi,ph.url);players=players.concat(shells)}var rows=await crawl(players,ph.url,"Sekai","VOSTFR");if(rows.length)return rows}return[]}

async function voiranimeRip(q){q=await metadata(q);var roots=[];for(var ti=0;ti<q.titles.length&&ti<6&&!roots.length;ti++){var sr=await resp(c.base+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"},body:"query="+encodeURIComponent(q.titles[ti]),referer:c.base+"/"});if(!sr)continue;var rows=pageCandidates(sr.text,c.base,"rip");rows=rows.filter(function(r){try{return new URL(r.url).hostname===new URL(c.base).hostname&&new URL(r.url).pathname.split("/").filter(Boolean).length===1}catch(_e){return false}});rows.sort(function(a,b){return score(b.label||b.url,q.titles[ti])-score(a.label||a.url,q.titles[ti])});roots=rows.slice(0,6)}for(var ri=0;ri<roots.length;ri++){var root=roots[ri].url.replace(/\/$/,""),ep=root+"/saison-"+q.season+"/episode-"+q.episode+"/",eh=await resp(ep,{referer:roots[ri].url});if(!eh)continue;var players=hrefs(eh.text,/<iframe[^>]+src=["']([^"']+)["']/gi,eh.url),js=/(?:vostfr|vf)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,jm;while((jm=js.exec(eh.text))!==null)players.push(jm[1]);var rows2=await crawl(players,eh.url,"VoirAnime.rip","VOSTFR");if(rows2.length)return rows2}return[]}

async function resolve(a,_ctx){var q=request(a);if(!q)return[];if(c.provider!=="coflix"&&q.type==="movie")return null;if(c.provider==="animesama-co")return animeSamaCo(q);if(c.provider==="animevostfr")return animeVostfr(q);if(c.provider==="coflix")return coflix(q);if(c.provider==="neko-sama")return neko(q);if(c.provider==="sekai")return sekai(q);if(c.provider==="voiranime-rip")return voiranimeRip(q);return[]}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:c.provider,resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    provider = str(cfg.get("provider") or "").strip().casefold().replace("_", "-")
    if provider not in SUPPORTED:
        raise ValueError(f"unsupported non-display recovery provider: {provider!r}")
    default_bases = {
        "animesama-co": "https://animesama.co",
        "animevostfr": "https://animevostfr.org",
        "coflix": "https://coflix.wiki",
        "neko-sama": "https://animes-sama.su",
        "sekai": "https://sekai.one",
        "voiranime-rip": "https://voiranime.rip",
    }
    payload = {
        "provider": provider,
        "base": str(cfg.get("base") or default_bases[provider]).rstrip("/"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 4), 8)),
    }
    if not payload["base"].startswith("https://"):
        raise ValueError("non-display recovery runtime requires https base")
    fix_id = "PROVIDER." + provider.upper() + ".NONDISPLAY.RECOVERY.V1"
    wrapper = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        fix_id,
        wrapper,
        data={
            "runtime": payload,
            "scope": "fresh-live-parity-regression-recovery",
            "upstreamJsExecuted": False,
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "terminalResolution": "existing-bounded-direct-media-crawler",
            "evidenceRun": 35112301175,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
