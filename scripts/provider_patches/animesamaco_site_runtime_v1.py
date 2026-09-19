#!/usr/bin/env python3
"""AnimeSamaCo current-site runtime Lego.

Observable clean-room contracts:
- search POST -> /anime/{id}-{slug}.html;
- anime series -> /saison-{n}/episode-{n}.html;
- episode page exposes VF/VOSTFR Sibnet shell URLs;
- Sibnet shell exposes a relative player.src MP4 URL.

The movie lane deliberately falls back to native while its JJK0 Sibnet terminal is
runner-blocked. ProviderBase remains immutable.
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.ANIMESAMA-CO.SITE.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMESAMACO_SITE_RUNTIME_V1"

WRAPPER = r'''
/* NIAKVIO_ANIMESAMACO_SITE_RUNTIME_V1 */
/* NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function runtimeBase(){try{var m=typeof NIAKVIO_PROVIDER_MODEL!=="undefined"&&NIAKVIO_PROVIDER_MODEL,b=s(m&&(m.officialSite||m.knownSite)||c.base);return b.replace(/\/$/,"")}catch(_e){return s(c.base).replace(/\/$/,"")}}
function norm(v){return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function visible(v){var src=String(v==null?"":v),low=src.toLowerCase(),out="",i=0;while(i<src.length){if(src.charAt(i)!=="<"){out+=src.charAt(i);i++;continue}if(low.slice(i,i+7)==="<script"){var cs=low.indexOf("</script",i+7);if(cs<0)break;var es=src.indexOf(">",cs+8);i=es<0?src.length:es+1;out+=" ";continue}if(low.slice(i,i+6)==="<style"){var ct=low.indexOf("</style",i+6);if(ct<0)break;var et=src.indexOf(">",ct+7);i=et<0?src.length:et+1;out+=" ";continue}var end=src.indexOf(">",i+1);if(end<0){out+=src.slice(i);break}out+=" ";i=end+1}return out.replace(/&[^;]+;/g," ").replace(/\s+/g," ").trim()}
function request(a){
  var first=a[0],o=first&&typeof first==="object"&&!Array.isArray(first)?first:null,ctx={};try{ctx=g&&g.__nuvioMediaContext||{}}catch(_e){}
  var semantic=s((o&&o.semanticType)||ctx.semanticType||"").toLowerCase();
  var raw=s((o&&(o.canonicalMediaType||o.mediaType||o.type))||a[1]||ctx.canonicalMediaType||ctx.mediaType||semantic||"").toLowerCase();
  if(raw==="series")raw="tv";
  /* AnimeSamaCo declares anime+movie, not a semantic TV lane. Some callers lose
     semanticType and transport anime as tv, so provider-local tv transport maps
     back to anime only when no stronger semantic label is present. */
  if(semantic==="anime"||(raw==="tv"&&!semantic))raw="anime";
  if(raw!=="anime")return null;
  var id=s((o&&(o.tmdbId||o.tmdb_id||o.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\d+$/.test(id))return[];
  return{type:"anime",transport:"tv",tmdbId:id,season:Number((o&&o.season)!=null?o.season:(a[2]!=null?a[2]:ctx.season))||1,episode:Number((o&&o.episode)!=null?o.episode:(a[3]!=null?a[3]:ctx.episode))||1}
}
function headers(ref,accept){var h={"User-Agent":c.ua,"Accept":accept||"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.7"};if(ref)h.Referer=ref;return h}
async function text(url,opt){try{var o=opt&&typeof opt==="object"?Object.assign({},opt):{};o.headers=Object.assign(headers(o.referer||""),o.headers||{});delete o.referer;var r=await g.fetch(url,o);if(!r||!r.ok)return null;return{url:r.url||url,text:await r.text()}}catch(_e){return null}}
async function meta(q){try{var fn=g&&g.__nuvioCoreGetTmdbDataV1;if(typeof fn==="function"){var z=await fn({tmdbId:q.tmdbId,mediaType:q.transport,tmdbNamespace:q.transport}),m=z&&z.metadata;if(m)return m}}catch(_e){}try{var ctx=g&&g.__nuvioMediaContext||{};return ctx.tmdbMetadata||null}catch(_e){return null}}
function title(m){return s(m&&(m.title||m.name||m.original_title||m.original_name))}
function aliases(m){var vals=[m&&m.name,m&&m.title,m&&m.original_name,m&&m.original_title],alt=m&&m.alternative_titles&&(m.alternative_titles.results||m.alternative_titles.titles||m.alternative_titles),out=[],seen={};if(Array.isArray(alt))for(var i=0;i<alt.length;i++)vals.push(alt[i]&&(alt[i].title||alt[i].name));for(var j=0;j<vals.length;j++){var v=s(vals[j]),k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}}return out.slice(0,6)}
function fallbackQueries(vals){var out=[],seen={};for(var i=0;i<vals.length&&out.length<5;i++){var w=s(vals[i]).split(/\s+/).filter(function(x){return x.length>=3});var q=[w[w.length-1],w.slice(-2).join(" "),w[0]];for(var j=0;j<q.length&&out.length<5;j++){var v=s(q[j]),k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}}}return out}
function attr(tag,key){var m=String(tag||"").match(new RegExp("\\b"+key+"\\s*=\\s*([\\\"'])([\\s\\S]*?)\\1","i"));return m?m[2]:""}
function resultRows(html){var out=[],seen={},re=/<a\b([^>]*)>([\s\S]*?)<\/a>/gi,m;while((m=re.exec(html||""))!==null){var attrs=m[1]||"",cls=attr(attrs,"class"),href=s(attr(attrs,"href"));if(cls&&cls.indexOf("asn-search-result")<0&&href.indexOf("/anime/")<0)continue;if(!/\/anime\/[^"'#?]+\.html(?:[?#].*)?$/i.test(href))continue;var titleMatch=String(m[2]||"").match(/class=["'][^"']*asn-search-result-title[^"']*["'][^>]*>([\s\S]*?)<\//i),label=visible(titleMatch?titleMatch[1]:m[2]);try{href=new URL(href,runtimeBase()).toString()}catch(_e){continue}if(href.indexOf(runtimeBase()+"/anime/")!==0||seen[href])continue;seen[href]=1;out.push({url:href,label:label})}return out}
function choose(rows,expected){var n=norm(expected),best=null,bestScore=999;for(var i=0;i<rows.length;i++){var label=norm(rows[i].label),score=50;if(label===n)score=0;else if(label.indexOf(n)===0)score=5;else if(label.indexOf(n)>=0)score=10;else continue;if(/\b(?:film|movie)\b/.test(label))score+=30;if(/\b0\b/.test(label)&&!/\b0\b/.test(n))score+=20;if(score<bestScore){best=rows[i];bestScore=score}}return best}
function videoShells(html){var out=[],seen={};function add(u,lang){u=s(u).replace(/&amp;/gi,'&').replace(/\\\//g,'/');if(!/^https?:\/\/video\.sibnet\.ru\/shell\.php\?videoid=\d+/i.test(u)||seen[u])return;seen[u]=1;out.push({url:u,lang:lang})}var block=/videoUrls\s*=\s*\{([\s\S]*?)\}/i.exec(html);if(block){var re=/(vostfr|vf)\s*:\s*["']([^"']+)["']/gi,m;while((m=re.exec(block[1]))!==null)add(m[2],m[1].toLowerCase())}var frame=/<iframe[^>]+src=["']([^"']+)["']/gi,x;while((x=frame.exec(html))!==null)add(x[1],"vf");return out}
function sibnetMp4(html,base){var m=/player\.src\s*\(\s*\[\s*\{\s*src\s*:\s*["']([^"']+\.mp4[^"']*)["']/i.exec(html);if(!m)m=/["'](\/v\/[^"']+\.mp4[^"']*)["']/i.exec(html);if(!m)return"";try{return new URL(m[1].replace(/\\\//g,'/'),base).toString()}catch(_e){return""}}
async function resolveShell(row,episodeUrl,q,expectedTitle){var ref=s(c.sibnetReferer||"https://video.sibnet.ru/");var shell=await text(row.url,{referer:ref,headers:headers(ref)});if(!shell)return null;var media=sibnetMp4(shell.text,shell.url);if(!media)return null;var label=row.lang==="vf"?"VF":"VOSTFR";return{name:"AnimeSamaCo | "+label,title:expectedTitle+" | S"+q.season+"E"+q.episode+" | "+label,url:media,quality:"HD",language:label,provider:"animesama-co",isDirect:true,headers:headers(ref,"video/mp4,*/*")}}
async function resolve(a,_ctx){var q=request(a);if(q===null)return null;if(!q||!q.tmdbId)return[];var m=await meta(q),t=title(m),names=aliases(m);if(!t)return[];if(!names.length)names=[t];var picked=null,queries=names.concat(fallbackQueries(names));for(var qi=0;qi<queries.length&&!picked;qi++){var search=await text(runtimeBase()+"/template-php/defaut/fetch.php",{method:"POST",headers:{"Accept":"text/html, */*","Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest","Referer":runtimeBase()+"/"},body:"query="+encodeURIComponent(queries[qi])});if(!search)continue;var rows=resultRows(search.text),best=null,bestScore=999;for(var ai=0;ai<names.length;ai++){var c=choose(rows,names[ai]);if(c){var score=norm(c.label)===norm(names[ai])?0:5;if(score<bestScore){best=c;bestScore=score}}}picked=best}if(!picked)return[];var root=picked.url.replace(/\.html(?:[?#].*)?$/i,'');var episodeUrl=root+"/saison-"+q.season+"/episode-"+q.episode+".html";var episode=await text(episodeUrl,{referer:picked.url});if(!episode)return[];var identity=(episode.text.match(/<title[^>]*>([\s\S]*?)<\/title>/i)||[])[1]||"";var ni=norm(identity),nt=norm(t);if(ni.indexOf(nt)<0||ni.indexOf("saison "+q.season)<0||ni.indexOf("episode "+q.episode)<0)return[];var shells=videoShells(episode.text),out=[],seen={};for(var i=0;i<shells.length&&out.length<3;i++){var st=await resolveShell(shells[i],episode.url,q,t);if(st&&st.url&&!seen[st.url]){seen[st.url]=1;out.push(st)}}return out}
try{if(g)g.__niakvioProviderRuntimeResolverV1={provider:"animesama-co",resolve:resolve}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = {
        "base": "https://animesama.co",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145 Safari/537.36",
        "sibnetReferer": "https://video.sibnet.ru/",
    }
    cfg.update(dict(options or {}))
    cfg["base"] = str(cfg.get("base") or "").rstrip("/")
    if not cfg["base"].startswith(("http://", "https://")):
        raise ValueError("AnimeSamaCo site runtime base must be http(s)")
    js = WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        js.lstrip(),
        data={
            "runtimeFamily": "animesamaco-search-episode-sibnet-v3-canonical-referer",
            "identity": "exact-search-title-plus-season-episode-page",
            "runtimeResolverRegistration": True,
            "coreFinalOutputOwnership": True,
            "semanticLanes": ["anime"],
            "transportFallback": "tv-without-semantic-maps-to-anime-provider-locally",
            "movieDisposition": "native-fallback-runner-blocked-sibnet-jjk0",
            "legacyExecutableSeed": False,
            "upstreamJsExecuted": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
