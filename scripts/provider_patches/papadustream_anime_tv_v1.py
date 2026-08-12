"""Allow PapaDuStream to serve anime series through the Nuvio TV contract.

NuvioTV can invoke anime entries with mediaType='anime', while PapaDuStream's
upstream resolver models episodic anime as TV.  The provider is proven to serve
Mushoku Tensei with a playable 720p HLS + external audio when invoked as TV, so
normalize only the request type and leave all other arguments untouched.
"""
from __future__ import annotations

MARKER = "NUVIO_PAPADUSTREAM_ANIME_TV_V1"


def apply(source: str, _options: dict | None = None, **_kwargs) -> str:
    if MARKER in source:
        return source
    shim = r'''
/* NUVIO_PAPADUSTREAM_ANIME_TV_V1 */
;(function(g){
  function install(t){
    if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioPapaAnimeTvV1)return;
    const native=t.getStreams;
    const wrapped=async function(){
      const a=Array.from(arguments);
      if(a[0]&&typeof a[0]==="object"){
        const o=Object.assign({},a[0]);
        const type=String(o.mediaType||o.type||"").toLowerCase();
        if(type==="anime"){
          if(Object.prototype.hasOwnProperty.call(o,"mediaType"))o.mediaType="tv";
          if(Object.prototype.hasOwnProperty.call(o,"type"))o.type="tv";
          if(!Object.prototype.hasOwnProperty.call(o,"mediaType")&&!Object.prototype.hasOwnProperty.call(o,"type"))o.mediaType="tv";
        }
        a[0]=o;
      }else if(String(a[1]||"").toLowerCase()==="anime"){
        a[1]="tv";
      }
      return native.apply(t,a);
    };
    wrapped.__nuvioPapaAnimeTvV1=true;
    wrapped.__nuvioPapaAnimeTvOriginal=native;
    t.getStreams=wrapped;
  }
  try{if(typeof module!=="undefined"&&module.exports)install(module.exports);}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){const o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams;}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
'''
    return source.rstrip() + "\n" + shim + "\n"
