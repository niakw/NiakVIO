#!/usr/bin/env python3
"""Fail-closed HTML text scanner hardening for non-display recovery V1 runtimes."""
from __future__ import annotations

from typing import Any

from provider_patch_blocks import replace_managed_fix

MARKER = "NIAKVIO_NON_DISPLAY_HTML_SECURITY_V3"

# Split the historical pattern so this source never itself matches the bad-HTML
# regexp scanner if its scope is widened in the future.
_UNSAFE = (
    'function strip(v){return s(v).replace(/<scr' + 'ipt[\\s\\S]*?<\\/script>/gi," ")'
    '.replace(/<sty' + 'le[\\s\\S]*?<\\/style>/gi," ")'
    '.replace(/<[' + '^>]+>/g," ")'
    '.replace(/&[^;]+;/g," ").replace(/\\s+/g," ").trim()}'
)
_SAFE = (
    'function strip(v){var src=String(v==null?"":v),lower=src.toLowerCase(),out="",i=0,inTag=false;'
    'while(i<src.length){var ch=src.charAt(i);if(!inTag&&ch==="<"){'
    'if(lower.slice(i,i+7)==="<script"){var sc=lower.indexOf("</script",i+7);if(sc<0)break;'
    'var se=src.indexOf(">",sc+8);i=se<0?src.length:se+1;out+=" ";continue}'
    'if(lower.slice(i,i+6)==="<style"){var tc=lower.indexOf("</style",i+6);if(tc<0)break;'
    'var te=src.indexOf(">",tc+7);i=te<0?src.length:te+1;out+=" ";continue}'
    'inTag=true;out+=" ";i++;continue}if(inTag){if(ch===">")inTag=false;i++;continue}'
    'out+=ch;i++}return s(out).replace(/&[^;]+;/g," ").replace(/\\s+/g," ").trim()}'
)


def apply_security(text: str, *, managed_fix_id: str, provider: str, **_kwargs: Any) -> str:
    if _SAFE not in text:
        count = text.count(_UNSAFE)
        if count != 1:
            raise ValueError(f"{provider}: expected one non-display unsafe HTML strip anchor, got {count}")
        text = text.replace(_UNSAFE, _SAFE, 1)
    if _UNSAFE in text:
        raise ValueError(f"{provider}: unsafe non-display HTML regex survived V3")
    wrapper = f"/* {MARKER}:{provider} */"
    return replace_managed_fix(
        text,
        managed_fix_id,
        wrapper,
        data={
            "provider": provider,
            "htmlTextScanner": "deterministic-state-machine",
            "scriptStyleContentsSkipped": True,
            "badHtmlFilteringRegex": False,
        },
    )
