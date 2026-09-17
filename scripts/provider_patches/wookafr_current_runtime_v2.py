#!/usr/bin/env python3
"""WookaFR current runtime: WP search -> typed work -> exact episode -> lecteurvideo players."""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.WOOKAFR.CURRENT.RUNTIME.V2"
MARKER = "NIAKVIO_WOOKAFR_CURRENT_RUNTIME_V2"

WRAPPER = r'''
/* NIAKVIO_WOOKAFR_CURRENT_RUNTIME_V2 */
;(function(){
  "use strict";
  try{
    if(typeof _spv4GetStreams!=="function"||_spv4GetStreams.__niakvioWookaCurrentV2)return;
    var original=_spv4GetStreams,BASE="https://wookafr.boston/",UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36";
    function clean(v){var src=String(v==null?"":v),out="",inTag=false;for(var i=0;i<src.length;i++){var ch=src.charAt(i);if(ch==="<"){inTag=true;out+=" ";continue}if(ch===">"){inTag=false;continue}if(!inTag)out+=ch}return out.replace(/&amp;/gi,"&").replace(/&#038;/gi,"&").replace(/&quot;/gi,'"').replace(/&#39;/gi,"'").replace(/\s+/g," ").trim()}
    function norm(v){try{return clean(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return clean(v).toLowerCase()}}
    function hdr(ref){return {"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,text/plain,*/*","Accept-Language":"fr-FR,fr;q=0.9,en;q=0.8","Referer":ref||BASE}}
    function mediaContext(tmdbId){try{var c=globalThis&&globalThis.__nuvioMediaContext;if(c&&String(c.tmdbId||"")===String(tmdbId||"")&&c.tmdbMetadata)return c.tmdbMetadata}catch(_e){}return null}
    async function meta(tmdbId,lane){
      var row=mediaContext(tmdbId);if(row){var date=String(row.release_date||row.first_air_date||"");return {title:String(row.title||row.name||row.original_title||row.original_name||""),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||0)||0,aliases:_uniq([row.title,row.name,row.original_title,row.original_name])}}
      try{return await _tmdb(tmdbId,lane==="movie"?"movie":"tv")}catch(_e){return null}
    }
    function anchors(html,base){var out=[],m,re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;while((m=re.exec(String(html||"")))&&out.length<1200){var u=_absolute(clean(m[1]),base),label=clean(m[2]);if(u&&/^https?:/i.test(u))out.push({url:u,text:label})}return out}
    function expectedTitles(m){return _uniq([m&&m.title].concat(m&&Array.isArray(m.aliases)?m.aliases:[])).map(norm).filter(Boolean)}
    function workCandidates(html,base,m,lane){
      var exp=expectedTitles(m),year=Number(m&&m.year||0)||0,out=[],seen=Object.create(null);
      for(var row of anchors(html,base)){
        if(seen[row.url])continue;var path="";try{path=new URL(row.url).pathname.toLowerCase()}catch(_e){continue}
        var isSeries=/^\/streaming\/series\//.test(path),isEpisode=/^\/streaming\/episodes\//.test(path),isWork=/^\/streaming\//.test(path)&&!isEpisode;
        if(lane==="movie"?(!isWork||isSeries):!isSeries)continue;
        var hay=norm(row.text+" "+decodeURIComponent(path)),score=0;
        for(var e of exp){if(!e)continue;if(hay===e||hay.endsWith(" "+e)||hay.indexOf(e)>=0)score=Math.max(score,100);var tokens=e.split(" ").filter(x=>x.length>=3),hits=tokens.filter(x=>hay.split(" ").includes(x)).length;if(tokens.length&&hits/tokens.length>=0.75)score=Math.max(score,60)}
        var y=(row.text.match(/\b(?:19|20)\d{2}\b/)||[])[0];if(lane==="movie"&&year&&y){if(Math.abs(Number(y)-year)>1)continue;score+=Number(y)===year?30:10}
        if(score>0){seen[row.url]=1;out.push({url:row.url,score:score,text:row.text})}
      }
      out.sort((a,b)=>b.score-a.score);return out;
    }
    function episodeUrl(detailHtml,detailUrl,season,episode){
      var s=Math.floor(Number(season)||0),e=Math.floor(Number(episode)||0);if(s<=0||e<=0)return "";
      var exact=new RegExp("/streaming/episodes/[^/?#]+-saison-"+s+"-episode-"+e+"/?(?:[?#]|$)","i");
      for(var row of anchors(detailHtml,detailUrl))if(exact.test(row.url))return row.url;
      try{var p=new URL(detailUrl),m=p.pathname.match(/^\/streaming\/series\/([^/?#]+)\/?$/i);if(!m)return "";return p.origin+"/streaming/episodes/"+m[1]+"-saison-"+s+"-episode-"+e+"/"}catch(_e){return ""}
    }
    function lecteurUrls(html,base){
      var out=[],seen=Object.create(null),src=String(html||"").replace(/&amp;|&#038;/gi,"&"),m,re=/https?:\/\/lecteurvideo\.com\/embed\.php\?[^"'<>\s]+/gi;
      while((m=re.exec(src))&&out.length<12){var u=_absolute(m[0],base);if(u&&!seen[u]){seen[u]=1;out.push(u)}}
      return out;
    }
    function decode64(input){
      var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",cleaned=String(input||"").replace(/[^A-Za-z0-9+/=]/g,""),out="",i=0;
      while(i<cleaned.length){var a=chars.indexOf(cleaned.charAt(i++)),b=chars.indexOf(cleaned.charAt(i++)),c0=cleaned.charAt(i++),d0=cleaned.charAt(i++),c=c0==="="?64:chars.indexOf(c0),d=d0==="="?64:chars.indexOf(d0);if(a<0||b<0)break;out+=String.fromCharCode((a<<2)|(b>>4));if(c!==64&&c>=0)out+=String.fromCharCode(((b&15)<<4)|(c>>2));if(d!==64&&d>=0)out+=String.fromCharCode(((c&3)<<6)|d)}
      try{return decodeURIComponent(out.split("").map(ch=>"%"+("0"+ch.charCodeAt(0).toString(16)).slice(-2)).join(""))}catch(_e){return out}
    }
    function playerUrls(html){
      var out=[],seen=Object.create(null),m,re=/showVideo\(\s*["']([^"']+)["']\s*,/gi;
      while((m=re.exec(String(html||"")))&&out.length<12){var u=decode64(m[1]);if(!/^https?:\/\//i.test(u)||seen[u])continue;try{var p=new URL(u),h=p.hostname.toLowerCase(),path=p.pathname.toLowerCase();if(!/(?:xtremestream|emmmmbed|uqload|lulustream|luluvdo|vidmoly|waaw|veev)/i.test(h)&&!/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))continue}catch(_e){continue}seen[u]=1;out.push(u)}
      return out;
    }
    async function current(tmdbId,mediaType,season,episode){
      var lane=String(mediaType||"").toLowerCase();lane=lane==="movie"?"movie":((lane==="tv"||lane==="series")?"tv":"");if(!lane)return [];
      var m=await meta(tmdbId,lane);if(!m||!m.title)return [];
      var search=BASE+"?s="+encodeURIComponent(m.title),sr=await _fetch(search,{headers:hdr(BASE)}),sh=await sr.text(),candidates=workCandidates(sh,sr.url||search,m,lane);if(!candidates.length)return [];
      for(var i=0;i<Math.min(candidates.length,4);i++){
        try{
          var dr=await _fetch(candidates[i].url,{headers:hdr(search)}),detailUrl=dr.url||candidates[i].url,dh=await dr.text(),contentUrl=detailUrl,contentHtml=dh;
          if(lane==="tv"){
            var ep=episodeUrl(dh,detailUrl,season,episode);if(!ep)continue;var er=await _fetch(ep,{headers:hdr(detailUrl)});if(!er||!er.ok)continue;contentUrl=er.url||ep;contentHtml=await er.text();
          }
          var lecteurs=lecteurUrls(contentHtml,contentUrl);if(!lecteurs.length)continue;var players=[],seen=Object.create(null);
          for(var j=0;j<Math.min(lecteurs.length,4)&&players.length<8;j++){
            var lr=await _fetch(lecteurs[j],{headers:hdr(contentUrl)}),lu=lr.url||lecteurs[j],lh=await lr.text();for(var u of playerUrls(lh)){if(!seen[u]){seen[u]=1;players.push({url:u,referer:lu})}}
          }
          if(players.length){var name=NIAKVIO_PROVIDER_MODEL.displayName||"WookaFR";return players.slice(0,8).map(function(row,index){return {name:name,title:name+(index?" #"+(index+1):""),url:row.url,headers:{Referer:row.referer},__nuvioCorrelatedPlayerFallbackV1:{url:row.url}}})}
        }catch(_e){}
      }
      return [];
    }
    var wrapped=async function(tmdbId,mediaType,season,episode){try{var rows=await current(tmdbId,mediaType,season,episode);if(rows.length)return rows}catch(_e){}try{return await original(tmdbId,mediaType,season,episode)}catch(_e){return []}};
    wrapped.__niakvioWookaCurrentV2=true;wrapped.__niakvioOriginal=original;_spv4GetStreams=wrapped;
    try{if(typeof module!=="undefined"&&module.exports&&typeof module.exports==="object")module.exports.getStreams=wrapped}catch(_e){}
  }catch(_e){}
})();
'''

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return replace_managed_fix(text, MANAGED_FIX_ID, WRAPPER, data={
        "scope": "provider-local-current-wp-search-typed-work-exact-episode-lecteurvideo",
        "providerBaseModified": False,
        "fixtureIdsHardcoded": False,
        "searchRoute": "/?s={title}",
        "movieIdentity": "title+year+non-series-route",
        "tvIdentity": "title+series-route+season+episode",
        "playerContract": "lecteurvideo-showVideo-base64-exact-correlated-embed",
    })

if __name__ == "__main__":
    raise SystemExit("patch module only")
