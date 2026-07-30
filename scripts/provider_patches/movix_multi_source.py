"""Movix-specific adapter: prefer the documented Purstream bridge, retain native fallback."""
from __future__ import annotations

MARKER = "NUVIO_MOVIX_MULTI_SOURCE_V1"

def apply(source: str, **_kwargs) -> str:
    if MARKER in source:
        return source
    shim = r'''
/* NUVIO_MOVIX_MULTI_SOURCE_V1 */
;(function(g){
  function text(v){return v==null?"":String(v)}
  function media(args){
    var a=args[0], b=args[1], c=args[2], d=args[3], e=args[4]||{};
    var obj=(a&&typeof a==="object")?a:{};
    var id=obj.tmdbId||obj.tmdb_id||(obj.tmdb&&obj.tmdb.id)||obj.id||a;
    var type=obj.mediaType||obj.media_type||obj.type||b||"movie";
    var season=obj.season||obj.seasonNumber||c||1;
    var episode=obj.episode||obj.episodeNumber||d||1;
    var title=obj.title||obj.label||e.title||e.label||"";
    return {id:id,type:type==="tv"?"tv":"movie",season:Number(season)||1,episode:Number(episode)||1,title:title};
  }
  function quality(s){var h=(text(s.quality)+" "+text(s.name)+" "+text(s.title)+" "+text(s.size)).toLowerCase();var m=h.match(/(?:^|\D)(2160|1440|1080|720|576|540|480|360)(?:p|\D|$)/);return m?m[1]+"p":(/4k|uhd/.test(h)?"2160p":text(s.quality)||"HD")}
  function language(s){var h=(text(s.language)+" "+text(s.name)+" "+text(s.title)+" "+text(s.size)).toUpperCase();if(/DUAL|MULTI/.test(h))return"MULTI";if(/VOSTFR/.test(h))return"VOSTFR";if(/VFQ/.test(h))return"VFQ";if(/VFF|\bVF\b|FRENCH/.test(h))return"VF";return text(s.language)||""}
  function collect(v,out){
    if(!v)return;
    if(Array.isArray(v)){for(var i=0;i<v.length;i++)collect(v[i],out);return}
    if(typeof v!=="object")return;
    if(typeof v.url==="string"&&/^https?:\/\//i.test(v.url))out.push(v);
    var keys=["streams","sources","results","data","links","players"];
    for(var k=0;k<keys.length;k++)if(v[keys[k]])collect(v[keys[k]],out);
  }
  function normalize(v,m){var raw=[];collect(v,raw);var seen={},out=[];for(var i=0;i<raw.length;i++){var s=raw[i];if(seen[s.url])continue;seen[s.url]=1;out.push({name:s.name||("Movix | "+quality(s)+(language(s)?" | "+language(s):"")),title:s.title||m.title||"Movix",url:s.url,quality:quality(s),language:language(s),size:s.size||s.title||"",headers:s.headers||{"User-Agent":"Mozilla/5.0"},subtitles:s.subtitles||[],audioTracks:s.audioTracks||[]})}return out}
  function rank(s){var q=parseInt(quality(s),10)||0;var direct=/\.m3u8(?:\?|$)|\.mp4(?:\?|$)/i.test(s.url)?5000:0;var lang=language(s)==="MULTI"?500:language(s)==="VF"||language(s)==="VFQ"?400:0;return direct+q+lang}
  function install(target){
    if(!target||typeof target.getStreams!=="function"||target.getStreams.__nuvioMovix)return;
    var native=target.getStreams;
    var wrapped=function(){var args=arguments,m=media(args);var route=m.type==="tv"?"/api/purstream/tv/"+m.id+"/season/"+m.season+"/episode/"+m.episode+"/stream":"/api/purstream/movie/"+m.id+"/stream";var bridge=fetch("https://api.movix.fun"+route,{headers:{Accept:"application/json",Origin:"https://movix.fun",Referer:"https://movix.fun/"}}).then(function(r){return r.ok?r.json():null}).then(function(v){return normalize(v,m)}).catch(function(){return[]});var fallback=Promise.resolve().then(function(){return native.apply(target,args)}).then(function(v){return Array.isArray(v)?v:[]}).catch(function(){return[]});return Promise.all([bridge,fallback]).then(function(all){var joined=all[0].concat(all[1]),seen={},out=[];joined.sort(function(a,b){return rank(b)-rank(a)});for(var i=0;i<joined.length;i++){if(joined[i]&&joined[i].url&&!seen[joined[i].url]){seen[joined[i].url]=1;out.push(joined[i])}}return out})};
    wrapped.__nuvioMovix=true;target.getStreams=wrapped;
  }
  try{if(typeof module!=="undefined"&&module.exports)install(module.exports)}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){var obj={getStreams:g.getStreams};install(obj);g.getStreams=obj.getStreams}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return source.rstrip()+"\n"+shim+"\n"
