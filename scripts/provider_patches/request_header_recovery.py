"""Generic deep-repair profile for provider-origin HTTP 403 responses.

The profile is selected from runtime evidence, never by provider name. It adds
only missing request headers and is retained only after a strict deep retest
improves the provider. The bootstrap deliberately uses Promise/ES5-compatible
syntax because provider files are evaluated dynamically by Nuvio.
"""
from __future__ import annotations

import json
import re
from typing import Any

MARKER = "NUVIO_REQUEST_HEADER_RECOVERY_V1"
END_MARKER = "NUVIO_REQUEST_HEADER_RECOVERY_END"


def apply(
    source: str,
    *,
    options: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    options = dict(options or {})
    cleaned = re.sub(
        rf"/\* {MARKER} \*/[\s\S]*?/\* {END_MARKER} \*/\s*",
        "",
        source,
        count=1,
    )
    payload = json.dumps(
        {
            "user_agent": options.get("user_agent")
            or "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36",
            "accept": options.get("accept") or "*/*",
            "accept_language": options.get("accept_language") or "en-US,en;q=0.9",
            "same_origin_context": options.get("same_origin_context", True),
        },
        separators=(",", ":"),
    )
    bootstrap = r'''/* NUVIO_REQUEST_HEADER_RECOVERY_V1 */
;(function(g,policy){
  if(!g||typeof g.fetch!=="function")return;
  var key="__nuvioRequestHeaderRecoveryV1",state=g[key];
  function copy(out,source){
    if(!source)return out;
    try{if(typeof source.forEach==="function"){source.forEach(function(v,k){out[String(k)]=String(v)});return out}}catch(_e){}
    if(Object.prototype.toString.call(source)==="[object Array]"){
      for(var i=0;i<source.length;i++){var p=source[i];if(p&&p.length>1)out[String(p[0])]=String(p[1])}
      return out;
    }
    if(typeof source==="object"){for(var k in source)if(Object.prototype.hasOwnProperty.call(source,k)&&source[k]!=null)out[String(k)]=String(source[k])}
    return out;
  }
  function has(headers,name){name=String(name).toLowerCase();for(var k in headers)if(Object.prototype.hasOwnProperty.call(headers,k)&&String(k).toLowerCase()===name)return true;return false}
  function setMissing(headers,name,value){if(value&&!has(headers,name))headers[name]=String(value)}
  if(!state){
    state={native:g.fetch.bind(g),policy:policy||{}};g[key]=state;
    g.fetch=function(input,init){
      var sourceInit=init&&typeof init==="object"?init:{},nextInit={},k;
      for(k in sourceInit)if(Object.prototype.hasOwnProperty.call(sourceInit,k))nextInit[k]=sourceInit[k];
      var headers={};
      try{if(typeof Request!=="undefined"&&input instanceof Request)copy(headers,input.headers)}catch(_e){}
      copy(headers,sourceInit.headers);
      setMissing(headers,"User-Agent",state.policy.user_agent);
      setMissing(headers,"Accept",state.policy.accept);
      setMissing(headers,"Accept-Language",state.policy.accept_language);
      if(state.policy.same_origin_context){
        try{
          var raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);
          var match=/^(https?:\/\/[^\/]+)/i.exec(raw),origin=match?match[1]:"";
          setMissing(headers,"Origin",origin);
          setMissing(headers,"Referer",origin?origin+"/":"");
        }catch(_e){}
      }
      nextInit.headers=headers;
      return state.native(input,nextInit);
    };
  }
  state.policy=policy||{};
})(typeof globalThis!=="undefined"?globalThis:this,__POLICY__);
/* NUVIO_REQUEST_HEADER_RECOVERY_END */
'''.replace("__POLICY__", payload)
    return bootstrap + "\n" + cleaned.lstrip()
