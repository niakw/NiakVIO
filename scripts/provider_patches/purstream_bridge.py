"""Purstream-specific adapter using the live Movix Purstream bridge as a validated fallback."""
from __future__ import annotations
MARKER="NUVIO_PURSTREAM_BRIDGE_V1"
def apply(source: str, **_kwargs) -> str:
    if MARKER in source:return source
    shim=r'''
/* NUVIO_PURSTREAM_BRIDGE_V1 */
;(function(g){
 function media(a){var o=a[0]&&typeof a[0]==="object"?a[0]:{},e=a[4]||{};return{id:o.tmdbId||o.id||a[0],type:(o.mediaType||o.type||a[1])==="tv"?"tv":"movie",season:Number(o.season||a[2])||1,episode:Number(o.episode||a[3])||1,title:o.title||o.label||e.title||e.label||""}}
 function collect(v,o){if(!v)return;if(Array.isArray(v)){v.forEach(function(x){collect(x,o)});return}if(typeof v!=="object")return;if(typeof v.url==="string")o.push(v);["streams","sources","results","data","links","players"].forEach(function(k){if(v[k])collect(v[k],o)})}
 function norm(v,m){var r=[],x=[];collect(v,r);r.forEach(function(s){if(!s.url)return;x.push({name:s.name||"Purstream",title:s.title||m.title||"Purstream",url:s.url,quality:s.quality||(/1080/i.test((s.name||"")+" "+(s.title||""))?"1080p":"HD"),language:s.language||(/dual|multi/i.test((s.name||"")+" "+(s.title||""))?"MULTI":/vostfr/i.test((s.name||"")+" "+(s.title||""))?"VOSTFR":"VF"),headers:s.headers||{"User-Agent":"Mozilla/5.0"},subtitles:s.subtitles||[],audioTracks:s.audioTracks||[]})});return x}
 function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioPurstream)return;var n=t.getStreams;t.getStreams=function(){var a=arguments,m=media(a);return Promise.resolve(n.apply(t,a)).catch(function(){return[]}).then(function(v){if(Array.isArray(v)&&v.length)return v;var p=m.type==="tv"?"/api/purstream/tv/"+m.id+"/season/"+m.season+"/episode/"+m.episode+"/stream":"/api/purstream/movie/"+m.id+"/stream";return fetch("https://api.movix.fun"+p,{headers:{Accept:"application/json",Origin:"https://movix.fun",Referer:"https://movix.fun/"}}).then(function(r){return r.ok?r.json():null}).then(function(j){return norm(j,m)}).catch(function(){return[]})})};t.getStreams.__nuvioPurstream=true}
 try{if(typeof module!=="undefined"&&module.exports)install(module.exports)}catch(_e){}try{if(g&&typeof g.getStreams==="function"){var o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return source.rstrip()+"\n"+shim+"\n"
