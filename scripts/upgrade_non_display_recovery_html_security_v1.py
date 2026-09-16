#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "non_display_recovery_runtime_v1.py"

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


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if _SAFE in text:
        if _UNSAFE in text:
            raise SystemExit("unsafe HTML strip survived beside safe scanner")
        print("NON_DISPLAY_HTML_SECURITY_V1_ALREADY_SAFE")
        return 0
    count = text.count(_UNSAFE)
    if count != 1:
        raise SystemExit(f"expected one unsafe non-display strip anchor, got {count}")
    text = text.replace(_UNSAFE, _SAFE, 1)
    if _UNSAFE in text or _SAFE not in text:
        raise SystemExit("non-display HTML security replacement failed closed")
    TARGET.write_text(text, encoding="utf-8")
    print("NON_DISPLAY_HTML_SECURITY_V1_PATCHED deterministic_state_machine=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
