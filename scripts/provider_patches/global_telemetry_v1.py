#!/usr/bin/env python3
"""Privacy-minimal Core telemetry around the final getStreams() boundary."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from provider_patch_blocks import has_managed_fix, replace_managed_fix

MARKER = "NUVIO_GLOBAL_TELEMETRY_V1"
MANAGED_FIX_ID = "CORE.TELEMETRY.V1"
REVISION = "privacy-minimal-vps-telemetry-v1"


def _strip_existing(text: str) -> str:
    start = text.find(f"/* {MARKER}:")
    if start < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global telemetry wrapper")
    return (text[:start] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    if not has_managed_fix(text, MANAGED_FIX_ID):
        text = _strip_existing(text)
    context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
    provider_id = str(context.get("provider_id") or "").strip().casefold()
    payload = {
        "schemaVersion": 1,
        "implementationRevision": REVISION,
        "providerId": provider_id,
        "bridgeGlobal": "__NIAKVIO_TELEMETRY_V1__",
        "localInstallKey": "niakvio.installId.v1",
        "requiresStableInstallId": True,
        "accountIdentity": "optional-host-pseudonym-only",
        "ipIdentity": False,
        "rawMediaIdentifiers": False,
        "rawStreamData": False,
    }
    serialized = json.dumps(payload, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function bridge(){var x=g&&g.__NIAKVIO_TELEMETRY_V1__;return x&&typeof x==="object"?x:{}}
function uuid(){try{if(g&&g.crypto&&typeof g.crypto.randomUUID==="function")return g.crypto.randomUUID()}catch(_e){}return"i-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2)+Math.random().toString(36).slice(2)}
function installId(){var b=bridge(),direct=s(b.installId);if(direct)return direct;try{if(g&&g.localStorage){var k=s(c.localInstallKey)||"niakvio.installId.v1",v=s(g.localStorage.getItem(k));if(v)return v;v=uuid();g.localStorage.setItem(k,v);return v}}catch(_e){}return""}
function sessionId(){var b=bridge(),direct=s(b.sessionId);if(direct)return direct;try{if(g.__nuvioTelemetrySessionIdV1)return s(g.__nuvioTelemetrySessionIdV1);g.__nuvioTelemetrySessionIdV1=uuid();return s(g.__nuvioTelemetrySessionIdV1)}catch(_e){return uuid()}}
function endpoint(){var u=s(bridge().endpoint);return/^https?:\/\//i.test(u)?u:""}
function mediaType(args){for(var i=0;i<args.length;i++){var a=args[i];if(a&&typeof a==="object"){var v=s(a.mediaType||a.type||a.media_type).toLowerCase();if(v==="movie"||v==="tv"||v==="anime")return v}}return""}
function count(v){if(Array.isArray(v))return v.length;if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return v[k].length}}return 0}
function emit(event){try{var url=endpoint(),iid=installId();if(!url||!iid)return;var b=bridge(),body={schemaVersion:1,event:"getStreams",timestamp:new Date().toISOString(),providerId:s(c.providerId),installId:iid,sessionId:sessionId(),ok:event.ok===true,streamCount:Number(event.streamCount||0),latencyMs:Math.max(0,Math.round(Number(event.latencyMs||0))),mediaType:s(event.mediaType)};var account=s(b.accountPseudonym);if(account)body.accountPseudonym=account;var appVersion=s(b.appVersion);if(appVersion)body.appVersion=appVersion;var p=JSON.stringify(body);if(g&&typeof g.fetch==="function"){var r=g.fetch(url,{method:"POST",body:p,headers:{"Content-Type":"text/plain;charset=UTF-8"},keepalive:true});if(r&&typeof r.catch==="function")r.catch(function(){})}}catch(_e){}}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalTelemetryV1)return false;var native=o[k];var wrap=async function(){var start=Date.now(),args=arguments,mt=mediaType(args);try{var v=await native.apply(this,args);emit({ok:true,streamCount:count(v),latencyMs:Date.now()-start,mediaType:mt});return v}catch(e){emit({ok:false,streamCount:0,latencyMs:Date.now()-start,mediaType:mt});throw e}};wrap.__nuvioGlobalTelemetryV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return replace_managed_fix(text, MANAGED_FIX_ID, wrapper, data=payload)


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
