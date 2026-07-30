#!/usr/bin/env python3
"""Inject a provider-specific failover for obsolete site/API hosts.

The wrapper does not rewrite stream outputs. It only retries the exact request
(path, query, method and headers preserved) against explicitly configured peer
origins for that provider. A candidate is accepted only when the request itself
returns a non-obsolete HTTP status. This lets each provider keep its own parser,
routes and response semantics.
"""
from __future__ import annotations

import base64
import json

MARKER = "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1"


def apply(text: str, *, options=None, context=None) -> str:
    options = options or {}
    groups = options.get("groups") or []
    normalized = []
    for item in groups:
        if not isinstance(item, dict):
            continue
        hosts = [str(v).lower().strip() for v in item.get("hosts") or [] if str(v).strip()]
        candidates = [str(v).rstrip("/") for v in item.get("candidates") or [] if str(v).startswith(("http://", "https://"))]
        if hosts and candidates:
            normalized.append({"hosts": hosts, "candidates": candidates})
    if not normalized:
        return text
    payload = base64.b64encode(
        json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode()
    ).decode()

    # Idempotency is essential because the deep pipeline can apply build
    # profiles more than once to the same staged/published artifact. If the
    # existing block already carries the exact deterministic payload, preserve
    # the bytes unchanged. When the configuration evolved, remove the old block
    # together with only its owned separator before injecting the new one.
    begin = f"/* {MARKER}:BEGIN */"
    end = f"/* {MARKER}:END */"
    if begin in text and end in text:
        a = text.index(begin)
        b = text.index(end, a) + len(end)
        existing = text[a:b]
        if f'"{payload}"' in existing:
            return text
        suffix = text[b:]
        if suffix.startswith("\r\n"):
            suffix = suffix[2:]
        elif suffix.startswith("\n") or suffix.startswith("\r"):
            suffix = suffix[1:]
        text = text[:a] + suffix
        while begin in text and end in text:
            a = text.index(begin)
            b = text.index(end, a) + len(end)
            suffix = text[b:]
            if suffix.startswith("\r\n"):
                suffix = suffix[2:]
            elif suffix.startswith("\n") or suffix.startswith("\r"):
                suffix = suffix[1:]
            text = text[:a] + suffix
    bootstrap = r'''/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */
;(function(g,encoded){
  if(!g||typeof g.fetch!=="function"||g.__nuvioAdaptiveDomainRecoveryV1)return;
  var nativeFetch=g.fetch.bind(g), groups=[];
  try{groups=JSON.parse(typeof atob==="function"?atob(encoded):Buffer.from(encoded,"base64").toString("utf8"));}catch(_e){return;}
  var cache=Object.create(null);
  function obsolete(status){return status===404||status===410||status===451||status===521||status===522||status===523;}
  function groupFor(host){
    host=String(host||"").toLowerCase();
    for(var i=0;i<groups.length;i++)if(groups[i].hosts.indexOf(host)!==-1)return groups[i];
    return null;
  }
  function rebuild(raw,origin){
    var source=new URL(raw), target=new URL(origin);
    target.pathname=source.pathname; target.search=source.search; target.hash=source.hash;
    return target.toString();
  }
  function cloneInput(input,url){
    try{return typeof Request!=="undefined"&&input instanceof Request?new Request(url,input):url;}catch(_e){return url;}
  }
  function attempt(input,init,raw,group,index){
    if(index>=group.candidates.length)return nativeFetch(input,init);
    var origin=group.candidates[index], url;
    try{url=rebuild(raw,origin);}catch(_e){return attempt(input,init,raw,group,index+1);}
    return nativeFetch(cloneInput(input,url),init).then(function(response){
      if(response&&!obsolete(response.status)){
        try{cache[new URL(raw).hostname.toLowerCase()]=origin;}catch(_e){}
        return response;
      }
      return attempt(input,init,raw,group,index+1);
    },function(){return attempt(input,init,raw,group,index+1);});
  }
  g.fetch=function(input,init){
    var raw;
    try{raw=typeof Request!=="undefined"&&input instanceof Request?input.url:String(input);}catch(_e){return nativeFetch(input,init);}
    var parsed, group;
    try{parsed=new URL(raw);group=groupFor(parsed.hostname);}catch(_e){return nativeFetch(input,init);}
    if(!group)return nativeFetch(input,init);
    var remembered=cache[parsed.hostname.toLowerCase()];
    if(remembered){
      var preferred=[remembered], rest=[];
      for(var i=0;i<group.candidates.length;i++)if(group.candidates[i]!==remembered)rest.push(group.candidates[i]);
      group={hosts:group.hosts,candidates:preferred.concat(rest)};
    }
    return attempt(input,init,raw,group,0);
  };
  g.__nuvioAdaptiveDomainRecoveryV1=true;
})(typeof globalThis!=="undefined"?globalThis:this,"'''+payload+r'''");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */
'''
    return bootstrap + "\n" + text
