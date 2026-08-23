#!/usr/bin/env python3
"""Shared final provider branding layer for reconstructed NiakVIO providers.

Provider artwork stays in native ``scraper.logo``. Until Nuvio exposes that logo
on local stream rows, one committed emoji per provider gives the textual stream
name/title a stable identity. This layer runs *after* Core stream presentation so
it never destroys provider-returned quality/language/codec facts before they are
normalized.

Every currently published provider must exist in ``assets/providers/emojis.json``
(the repository contract checks exact 92/92 coverage). A provider discovered only
inside a future/synthetic Core probe may still pass safely with a regional-indicator
emoji derived from the first alphabetic letter of its readable provider name; it is
not publishable until the committed inventory is updated.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

MARKER = "NUVIO_GLOBAL_PROVIDER_BRANDING_V1"
ROOT = Path(__file__).resolve().parents[2]
BRANDING = ROOT / "assets" / "providers" / "emojis.json"


def _fallback_name(provider_id: str) -> str:
    parts = [part for part in re.split(r"[-_\s]+", str(provider_id or "").strip()) if part]
    return " ".join(part[:1].upper() + part[1:] for part in parts) or "Source"


def _initial_emoji(name: str) -> str:
    """Return the Unicode regional-indicator emoji for the first A-Z letter."""
    for char in str(name or "").upper():
        if "A" <= char <= "Z":
            return chr(0x1F1E6 + ord(char) - ord("A"))
    # _fallback_name always supplies Source for an empty/non-alphabetic id, so
    # this is a defensive invariant rather than a visible generic fallback.
    return chr(0x1F1E6 + ord("S") - ord("A"))


def _load_provider(provider_id: str) -> dict[str, str]:
    payload = json.loads(BRANDING.read_text(encoding="utf-8"))
    if payload.get("policy") != "committed-provider-default-emoji":
        raise ValueError("provider emoji map must declare committed-provider-default-emoji policy")
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("provider emoji map providers must be an object")
    normalized_id = str(provider_id or "").strip().casefold()
    row = providers.get(normalized_id)
    if not isinstance(row, dict):
        name = _fallback_name(normalized_id)
        return {"name": name, "emoji": _initial_emoji(name)}
    name = str(row.get("name") or "").strip()
    emoji = str(row.get("emoji") or "").strip()
    if not name or not emoji:
        raise ValueError(f"provider emoji map row is incomplete: {provider_id}")
    return {"name": name, "emoji": emoji}


def _strip_existing(text: str) -> str:
    start = text.find(f"/* {MARKER}:")
    if start < 0:
        return text
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError("unterminated global provider branding wrapper")
    return (text[:start] + text[end + 2 :]).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
    provider_id = str(context.get("provider_id") or "").strip().casefold()
    if not provider_id:
        return text
    row = _load_provider(provider_id)

    payload = {
        "providerId": provider_id,
        "providerName": row["name"],
        "providerEmoji": row["emoji"],
        "implementationRevision": "post-presentation-emoji-stream-label-v4",
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    marker = f"{MARKER}:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:12]}"
    text = _strip_existing(text)

    wrapper = r'''
/* MARKER_PLACEHOLDER */
;(function(g,c){"use strict";
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function label(){return(String(c.providerEmoji||"").trim()+" "+String(c.providerName||c.providerId||"Source").trim()).trim()}
function title(v,old){old=String(old||"").trim();if(!old)return v;var token=" • ",i=old.indexOf(token);return i>=0?v+old.slice(i):v}
function brand(r){if(!r||typeof r!=="object")return r;var o=Object.assign({},r),v=label();if(!v)return o;o.title=title(v,o.title);o.name=v;return o}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalProviderBrandingV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;return rebuild(v,x,x.list.map(brand))};wrap.__nuvioGlobalProviderBrandingV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,CONFIG_PLACEHOLDER);
'''.replace("MARKER_PLACEHOLDER", marker).replace("CONFIG_PLACEHOLDER", serialized)
    return text.rstrip() + "\n" + wrapper.strip() + "\n"
