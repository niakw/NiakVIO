"""Force Purstream TV requests through an exact TMDB/season/episode route.

The historical Purstream provider can return a non-empty stream list whose
metadata describes the requested episode while the underlying media belongs to
another title.  A non-empty native result therefore is not sufficient identity
proof for TV.  This wrapper uses the Movix Purstream bridge keyed by the exact
TMDB id + season + episode and fails closed when that exact route has no result.
Movies are left to the native provider.
"""
from __future__ import annotations

MARKER = "NUVIO_PURSTREAM_EXACT_TV_V2"


def apply(source: str, _options: dict | None = None, **_kwargs) -> str:
    if MARKER in source:
        return source
    shim = r'''
/* NUVIO_PURSTREAM_EXACT_TV_V2 */
;(function(g){
  function req(a){
    var o=a[0]&&typeof a[0]==="object"?a[0]:{};
    return {
      id:String(o.tmdbId||o.id||a[0]||""),
      type:String(o.mediaType||o.type||a[1]||"movie").toLowerCase()==="tv"?"tv":"movie",
      season:Number(o.season??a[2]??1)||1,
      episode:Number(o.episode??a[3]??1)||1,
      title:String(o.title||o.label||"")
    };
  }
  function collect(v,out){
    if(!v)return;
    if(Array.isArray(v)){v.forEach(function(x){collect(x,out)});return;}
    if(typeof v!=="object")return;
    if(typeof v.url==="string"&&/^https?:\/\//i.test(v.url))out.push(v);
    ["streams","sources","results","data","links","players"].forEach(function(k){if(v[k])collect(v[k],out)});
  }
  function norm(v,m){
    var raw=[],out=[];collect(v,raw);
    raw.forEach(function(s){
      if(!s||!s.url)return;
      out.push({
        name:s.name||("Purstream • S"+m.season+"E"+m.episode),
        title:s.title||m.title||("Purstream S"+m.season+"E"+m.episode),
        url:s.url,
        quality:s.quality||"HD",
        language:s.language||(/vostfr/i.test(String(s.name||"")+" "+String(s.title||""))?"VOSTFR":/multi|dual/i.test(String(s.name||"")+" "+String(s.title||""))?"MULTI":"VF"),
        headers:s.headers||{"User-Agent":"Mozilla/5.0"},
        subtitles:s.subtitles||[],
        audioTracks:s.audioTracks||[]
      });
    });
    return out;
  }
  async function exactTv(m){
    if(!/^\d+$/.test(m.id)||m.season<1||m.episode<1)return [];
    var path="/api/purstream/tv/"+encodeURIComponent(m.id)+"/season/"+m.season+"/episode/"+m.episode+"/stream";
    try{
      var r=await fetch("https://api.movix.fun"+path,{headers:{Accept:"application/json",Origin:"https://movix.fun",Referer:"https://movix.fun/"}});
      if(!r.ok)return [];
      return norm(await r.json(),m);
    }catch(_e){return [];}
  }
  function install(t){
    if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioPurstreamExactTvV2)return;
    var native=t.getStreams;
    var wrapped=async function(){
      var a=arguments,m=req(a);
      if(m.type!=="tv")return native.apply(t,a);
      // TV is intentionally fail-closed: never fall back to a native non-empty
      // result whose media identity cannot be tied to the requested episode.
      return exactTv(m);
    };
    wrapped.__nuvioPurstreamExactTvV2=true;
    wrapped.__nuvioPurstreamExactTvOriginal=native;
    t.getStreams=wrapped;
  }
  try{if(typeof module!=="undefined"&&module.exports)install(module.exports);}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){var o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams;}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return source.rstrip() + "\n" + shim + "\n"
