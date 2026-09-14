#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DLE = ROOT / "scripts" / "provider_patches" / "dle_anime_runtime_v1.py"
NEKO = ROOT / "scripts" / "provider_patches" / "neko_sama_runtime_v1.py"
MARKER = "NIAKVIO_HTML_FILTER_SCANNER_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    dle = DLE.read_text(encoding="utf-8")
    dle = replace_once(
        dle,
        '  function stripTags(v){return s(v).replace(/<[^>]+>/g," ").replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\\s+/g," ").trim()}\n',
        '  function stripTags(v){var src=String(v==null?"":v),out="",inTag=false;for(var i=0;i<src.length;i++){var ch=src.charAt(i);if(ch==="<"){inTag=true;out+=" ";continue}if(ch===">"){inTag=false;continue}if(!inTag)out+=ch}return s(out).replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\\s+/g," ").trim()}\n',
        "DLE stripTags scanner",
    )
    if MARKER not in dle:
        dle = dle.replace('MARKER = "NIAKVIO_DLE_ANIME_RUNTIME_V1"\n', 'MARKER = "NIAKVIO_DLE_ANIME_RUNTIME_V1"\nSECURITY_MARKER = "NIAKVIO_HTML_FILTER_SCANNER_V1"\n', 1)
    DLE.write_text(dle, encoding="utf-8")

    neko = NEKO.read_text(encoding="utf-8")
    old = '    while((gm=groupRe.exec(html||""))!==null&&out.length<20){var block=gm[1],lm=block.match(/<label[^>]*>([\\s\\S]*?)<\\/label>/i),label=lm?s(lm[1].replace(/<[^>]+>/g," ")).toUpperCase():"",language=/^VF\\b|FRENCH/.test(label)?"VF":/SUB|VOSTFR/.test(label)?"VOSTFR":"VOSTFR",re=/loadMi\\(\\{\\s*value\\s*:\\s*[\'\"]([A-Za-z0-9+/=]{20,})[\'\"]\\s*\\}\\)/g,m;\n'
    new = '    while((gm=groupRe.exec(html||""))!==null&&out.length<20){var block=gm[1],lm=block.match(/<label[^>]*>([\\s\\S]*?)<\\/label>/i),label=lm?nekoVisibleText(lm[1]).toUpperCase():"",language=/^VF\\b|FRENCH/.test(label)?"VF":/SUB|VOSTFR/.test(label)?"VOSTFR":"VOSTFR",re=/loadMi\\(\\{\\s*value\\s*:\\s*[\'\"]([A-Za-z0-9+/=]{20,})[\'\"]\\s*\\}\\)/g,m;\n'
    if new not in neko:
        count = neko.count(old)
        if count != 1:
            raise SystemExit(f"Neko label anchor count={count}")
        scanner = '  function nekoVisibleText(v){var src=String(v==null?"":v),out="",inTag=false;for(var i=0;i<src.length;i++){var ch=src.charAt(i);if(ch==="<"){inTag=true;out+=" ";continue}if(ch===">"){inTag=false;continue}if(!inTag)out+=ch}return s(out).replace(/&(?:nbsp|amp|quot|#0*39);/gi," ").replace(/\\s+/g," ").trim()}\n'
        anchor = '  function nekoButtons(html){\n'
        if neko.count(anchor) != 1:
            raise SystemExit(f"Neko buttons anchor count={neko.count(anchor)}")
        neko = neko.replace(anchor, scanner + anchor, 1).replace(old, new, 1)
    NEKO.write_text(neko, encoding="utf-8")
    print("NIAKVIO_HTML_FILTER_SCANNER_V1_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
