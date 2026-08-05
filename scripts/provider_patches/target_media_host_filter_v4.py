#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from typing import Any

MARKER = "NUVIO_TARGET_MEDIA_HOST_FILTER_V4"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "allowedMediaHosts": [str(value).lower().lstrip(".") for value in cfg.get("allowed_media_hosts", [])],
        "blockedHosts": [str(value).lower().lstrip(".") for value in cfg.get("blocked_hosts", [])],
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    javascript = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function host(u){try{return new URL(s(u)).hostname.toLowerCase()}catch(_){return""}}
function matches(h,rule){return h===rule||h.endsWith("."+rule)}
function blocked(u){var h=host(u);if(!h)return true;for(var i=0;i<c.blockedHosts.length;i++)if(matches(h,c.blockedHosts[i]))return true;if(!c.allowedMediaHosts.length)return false;for(var j=0;j<c.allowedMediaHosts.length;j++)if(matches(h,c.allowedMediaHosts[j]))return false;return true}
function rows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){for(var i=0;i<["streams","results","data"].length;i++){var key=["streams","results","data"][i];if(Array.isArray(value[key]))return value[key]}}return[]}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTargetHostFilterV4)return false;var old=obj[key];var wrap=async function(){var value=await old.apply(this,arguments),out=rows(value).filter(function(row){return row&&row.url&&!blocked(row.url)});return out};wrap.__nuvioTargetHostFilterV4=true;wrap.__nuvioOriginal=old;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + javascript.lstrip()
