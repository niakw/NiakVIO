#!/usr/bin/env python3
"""Global TMDB/IMDb-first catalogue fallback for HTML/mixed providers.

Native provider resolution always wins. This wrapper only runs when native
resolution returns no streams. Numeric TMDB IDs are consumed directly; IMDb
``tt...`` IDs are resolved through TMDB's external-ID endpoint. Only then are
localized/original/alternative titles used internally to search a target site's
HTML catalogue. No provider title or work ID is hard-coded in this engine.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"
LEGACY_MARKER = "/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1:"
WRAPPER_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'

# Before 5.20.41, guessed /title-slugs were inserted before real catalogue
# search hits. With max_aliases == max_candidates (the default), those guesses
# could consume the whole candidate budget and silently discard the real search
# result. Keep this exact upgrader so already-patched/LKG provider sources are
# repaired too instead of being skipped merely because they already carry V2.
_OLD_CANDIDATE_PLAN = r'''var candidates=[],searches=[];m.titles.forEach(function(t){candidates.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&candidates.length<c.maxCandidates*4;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)candidates=candidates.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}candidates=unique(candidates).slice(0,c.maxCandidates);'''
_NEW_CANDIDATE_PLAN = r'''var guessed=[],found=[],searches=[];m.titles.forEach(function(t){guessed.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)found=found.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);'''


def _upgrade_existing_search_priority(text: str) -> str:
    """Upgrade already-injected V2 runtimes without stacking another wrapper."""
    if _OLD_CANDIDATE_PLAN in text:
        return text.replace(_OLD_CANDIDATE_PLAN, _NEW_CANDIDATE_PLAN)
    return text


def _strip_legacy_v1(text: str) -> str:
    """Remove the superseded V1 fallback before installing/updating V2.

    Some long-lived published bundles retained both generations. Because V2
    wraps V1, an empty native result caused the complete V1 catalogue crawl to
    run before V2 could apply its stricter identity and search-priority logic.
    On slow sites that duplicated dozens of sequential requests and could
    exhaust the client worker timeout.
    """
    while True:
        start = text.find(LEGACY_MARKER)
        if start < 0:
            return text
        call = text.find(WRAPPER_CALL, start)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated legacy global catalogue alias recovery wrapper")
        text = (text[:start] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    text = _strip_legacy_v1(text)
    base_url = str(cfg.get("base_url") or "").rstrip("/")
    if not base_url:
        return text
    payload = {
        "baseUrl": base_url,
        "providerName": str(cfg.get("provider_name") or "Provider"),
        "maxAliases": max(2, min(int(cfg.get("max_aliases", 8)), 12)),
        "maxCandidates": max(2, min(int(cfg.get("max_candidates", 8)), 16)),
        "maxPlayers": max(1, min(int(cfg.get("max_players", 8)), 16)),
        "timeoutMs": max(2500, min(int(cfg.get("timeout_ms", 7000)), 15000)),
        "budgetMs": max(5000, min(int(cfg.get("budget_ms", 45000)), 60000)),
        "languageHint": str(cfg.get("language_hint") or "").strip().lower(),
        "implementationRevision": "native-identity-budget-v2",
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return _upgrade_existing_search_priority(text)

    old = text.find(f"/* {MARKER}:")
    if old >= 0:
        call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', old)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated global catalogue alias recovery wrapper")
        text = (text[:old] + text[end + 2 :]).rstrip()

    js = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){v=s(v).replace(/\s*\(\d{4}\)\s*$/,"");var k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}});return out}
function args(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{id:first,mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};var raw=s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id||first),m;q.mediaType=s(q.mediaType||q.type||q.category||"movie").toLowerCase();q.season=Number(q.season)||0;q.episode=Number(q.episode)||0;q.tmdbId="";q.imdbId="";m=/^(?:imdb:)?(tt\d+)(?::(\d+):(?:(\d+)))?$/i.exec(raw);if(m){q.imdbId=m[1].toLowerCase();if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}else{raw=raw.replace(/^tmdb:/i,"");m=/^(\d+)(?::(\d+):(?:(\d+)))?$/.exec(raw);if(m){q.tmdbId=m[1];if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}}return q}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
async function request(url,json,referer){try{var h={Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"};if(referer){h.Referer=referer;try{h.Origin=new URL(referer).origin}catch(_){}}var r=await g.fetch(url,{headers:h,redirect:"follow",signal:timeout()});if(!r||!r.ok)return null;return{url:s(r.url||url),body:json?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
function kindFor(q){if(q.mediaType==="tv")return"tv";if(q.mediaType==="anime"&&q.season&&q.episode)return"tv";return"movie"}
async function resolveIdentity(q,kind){if(/^\d+$/.test(q.tmdbId||""))return{tmdbId:q.tmdbId,imdbId:q.imdbId||"",seed:null};if(!/^tt\d+$/i.test(q.imdbId||""))return{tmdbId:"",imdbId:q.imdbId||"",seed:null};var r=await request("https://api.themoviedb.org/3/find/"+encodeURIComponent(q.imdbId)+"?api_key="+TMDB_KEY+"&external_source=imdb_id",true);if(!r||!r.body)return{tmdbId:"",imdbId:q.imdbId,seed:null};var preferred=kind==="tv"?(r.body.tv_results||[]):(r.body.movie_results||[]),other=kind==="tv"?(r.body.movie_results||[]):(r.body.tv_results||[]),seed=(preferred[0]||other[0]||null);return{tmdbId:seed&&seed.id?String(seed.id):"",imdbId:q.imdbId,seed:seed}}
async function meta(q){var titles=unique([q.title,q.name,q.label,q.settings&&q.settings.title]),year=Number(q.year||q.settings&&q.settings.year)||0,kind=kindFor(q),identity=await resolveIdentity(q,kind);if(identity.seed){var sd=identity.seed;titles=unique(titles.concat([sd.title,sd.name,sd.original_title,sd.original_name]));var seedDate=s(sd.release_date||sd.first_air_date);year=year||Number(seedDate.slice(0,4))||0}if(identity.tmdbId){var urls=["https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=en-US"];for(var i=0;i<urls.length;i++){var r=await request(urls[i],true);if(r&&r.body){var d=r.body;titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));var date=s(d.release_date||d.first_air_date);year=year||Number(date.slice(0,4))||0}}var alt=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"/alternative_titles?api_key="+TMDB_KEY,true);if(alt&&alt.body){var rows=alt.body.titles||alt.body.results||[],priority={FR:100,US:90,GB:80,CA:70,DK:60};rows=rows.slice().sort(function(a,b){return(priority[String(b&&b.iso_3166_1||"").toUpperCase()]||0)-(priority[String(a&&a.iso_3166_1||"").toUpperCase()]||0)});rows.slice(0,50).forEach(function(x){if(x&&x.title)titles.push(x.title)});titles=unique(titles)}}return{titles:titles.slice(0,c.maxAliases),year:year,tmdbId:identity.tmdbId,imdbId:identity.imdbId}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,streaming:1,watch:1,voir:1,regarder:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function aliasScore(text,m){var n=norm(text),best=-1;(m.titles||[]).forEach(function(t){var nt=norm(t),want=tokens(t);if(!want.length)return;var score=n.indexOf(nt)>=0?120:0;if(!score&&want.every(function(x){return n.indexOf(x)>=0}))score=90;if(score>best)best=score});if(best<0)return-1;var years=n.match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&years.indexOf(String(m.year))<0)return-1;if(m.year&&n.indexOf(String(m.year))>=0)best+=15;return best}
function links(html,base,m){var rows=[],seen={},re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(String(html||"")))!==null){var u=abs(x[2],base),label=s(x[1])+" "+s(x[3])+" "+s(x[4]).replace(/<[^>]+>/g," ");if(!u||seen[u])continue;seen[u]=1;var score=aliasScore(label+" "+u,m);if(score>=90)rows.push({url:u,score:score})}return rows.sort(function(a,b){return b.score-a.score}).slice(0,c.maxCandidates)}
function mediaish(u){return/(?:\.m3u8|\.mpd|\.mp4|\.mkv|\.webm)(?:[?#]|$)|\/(?:embed|player|watch|stream|video)(?:[/?#.-]|$)|\/e\//i.test(u)}
function extractPlayers(html,base,q){var text=String(html||"").replace(/\\\//g,"/"),out=[],seen={};function add(v){var u=abs(v,base);if(!u||seen[u]||!/^https?:\/\//i.test(u)||!mediaish(u))return;seen[u]=1;out.push(u)}var scoped=text;if((q.mediaType==="tv"||q.mediaType==="anime")&&q.season&&q.episode){var patterns=[new RegExp("s(?:aison|eason)?[ ._-]*0?"+q.season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+q.episode,"i"),new RegExp("(?:episode|ep)[ ._-]*0?"+q.episode,"i")],chunks=text.split(/(?=<[^>]+(?:episode|season|saison|data-ep))/i).filter(function(x){return patterns.some(function(p){return p.test(x)})});if(chunks.length)scoped=chunks.join("\n");else return[]}var patterns2=[/(?:src|href|data-src|data-url|data-embed|data-player|data-video|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi],m;for(var i=0;i<patterns2.length;i++){patterns2[i].lastIndex=0;while((m=patterns2[i].exec(scoped))!==null){add(m[1]);if(out.length>=c.maxPlayers)return out}}return out}
function rows(urls,m,page){return urls.slice(0,c.maxPlayers).map(function(u,i){var out={name:c.providerName+(urls.length>1?" #"+(i+1):""),title:c.providerName+" - "+(m.titles[0]||"Media"),url:u,quality:"Unknown",headers:{Referer:page,Origin:(function(){try{return new URL(page).origin}catch(_){return c.baseUrl}})()}};if(c.languageHint)out.language=c.languageHint;if(/\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(u))out.isDirect=true;return out})}
function idEvidence(body,m){var text=String(body||"");if(m.tmdbId&&new RegExp("tmdb[^0-9]{0,24}"+String(m.tmdbId),"i").test(text))return true;if(m.imdbId&&new RegExp("imdb[^a-z0-9]{0,24}"+String(m.imdbId),"i").test(text))return true;return false}
async function recover(q,knownMeta,deadline){if(["movie","tv","anime"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];var m=knownMeta||await meta(q);if(!m.titles.length||Date.now()>=deadline)return[];var guessed=[],found=[],searches=[];m.titles.forEach(function(t){guessed.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)found=found.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);for(var j=0;j<candidates.length&&Date.now()<deadline;j++){var page=await request(candidates[j],false,c.baseUrl+"/");if(!page)continue;var identity=aliasScore(page.url+" "+String(page.body||"").slice(0,180000),m);if(identity<90&&!idEvidence(page.body,m))continue;var p=extractPlayers(page.body,page.url,q);if(p.length)return rows(p,m,page.url)}return[]}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function identityLabel(row){return s(row&&((row.title||row.description||row.filename||row.name)||""))}
function nativeIdentityReject(row,q,m){var label=identityLabel(row);if(!label)return false;var se=/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);if(q.mediaType==="movie"&&se)return true;if(se&&(q.mediaType==="tv"||q.mediaType==="anime")){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true}if(aliasScore(label,m)>=90)return false;var tech={server:1,serveur:1,stream:1,streaming:1,source:1,mirror:1,direct:1,download:1,telecharger:1,play:1,player:1,vcloud:1,hubcloud:1,file:1,video:1,quality:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var providerTokens=tokens(c.providerName),expected={};(m.titles||[]).forEach(function(t){tokens(t).forEach(function(x){expected[x]=1})});var words=tokens(label).filter(function(x){return !tech[x]&&providerTokens.indexOf(x)<0&&!/^\d{3,4}p$/.test(x)});if(words.length<2)return false;for(var i=0;i<words.length;i++)if(expected[words[i]])return false;return true}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v),m=null;if(x&&x.list.length){try{m=await meta(q)}catch(_){m=null}if(!m||!m.titles||!m.titles.length)return v;var kept=x.list.filter(function(row){return !nativeIdentityReject(row,q,m)});if(kept.length)return rebuild(v,x,kept)}var recovered=await recover(q,m,deadline);if(!recovered.length)return x?rebuild(v,x,[]):v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return _upgrade_existing_search_priority(text.rstrip() + "\n" + js.lstrip())
