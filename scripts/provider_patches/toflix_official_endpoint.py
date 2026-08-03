#!/usr/bin/env python3
"""Use the ToFlix terminal site and discover its current API endpoint safely."""
from __future__ import annotations

import re
from typing import Any

MARKER = "NUVIO_TOFLIX_OFFICIAL_ENDPOINT_V1"


def _replace_named_function(text: str, name: str, replacement: str) -> tuple[str, bool]:
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return text, False
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote: str | None = None
    escaped = line_comment = block_comment = False
    index = brace
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char in "\r\n": line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/": block_comment = False; index += 1
        elif quote:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == quote: quote = None
        else:
            if char in ("'", '"', "`"): quote = char
            elif char == "/" and nxt == "/": line_comment = True; index += 1
            elif char == "/" and nxt == "*": block_comment = True; index += 1
            elif char == "{": depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[:start] + replacement + text[index + 1 :], True
        index += 1
    raise ValueError(f"unterminated JavaScript function: {name}")


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    options = dict(options or {})
    site = str(options.get("site") or "https://tfx05.lol").rstrip("/")
    fallback_api = str(options.get("fallback_api") or "https://api.tfx05.lol/toflix_api.php")
    replacement = rf'''function detectToflixEndpoint(){{/* {MARKER} */
var site={site!r},fallbackApi={fallback_api!r};
if(_cachedEndpoint)return Promise.resolve(_cachedEndpoint);
return fetch(site+"/",{{headers:{{"Accept":"text/html,*/*;q=0.8"}}}}).then(function(response){{
  if(!response||!response.ok)throw new Error("ToFlix terminal site HTTP "+(response&&response.status));
  var finalSite=response.url||site+"/";
  return response.text().then(function(body){{return {{body:body,site:new URL(finalSite).origin}}}});
}}).then(function(result){{
  var decoded=String(result.body||"").split("\\/").join("/");
  var match=decoded.match(/https?:\/\/[^\s<>]+\/toflix_api\.php(?:\?[^\s<>]+)?/i);
  var api=match?match[0]:fallbackApi;
  var referer=result.site.endsWith("/")?result.site:result.site+"/";
  _cachedEndpoint={{api:api,referer:referer,zeusReferer:referer,zeus_referer:referer}};
  return _cachedEndpoint;
}}).catch(function(error){{
  console.warn("[ToFlix] terminal bootstrap failed, using validated fallback:",error&&error.message||error);
  var referer=site+"/";
  return {{api:fallbackApi,referer:referer,zeusReferer:referer,zeus_referer:referer}};
}});
}}'''
    output, changed = _replace_named_function(text, "detectToflixEndpoint", replacement)
    return output if changed else text
