#!/usr/bin/env python3
"""Castle identity hardening.

Castle search may return unrelated rows. The upstream-shaped fallback to the
first row is forbidden: a title match is required before any movieId is used.
"""
from __future__ import annotations

import re
from typing import Any


def _replace_named_function(text: str, name: str, replacement: str) -> tuple[str, bool]:
    match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return text, False
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch in "\r\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
        else:
            if ch in ("'", '"', "`"):
                quote = ch
            elif ch == "/" and nxt == "/":
                line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                block_comment = True
                i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[:match.start()] + replacement + text[i + 1 :], True
        i += 1
    raise ValueError("unterminated Castle findCastleMovieId function")


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if "NUVIO_CASTLE_STRICT_IDENTITY_V1" in text:
        return text
    replacement = r'''async function findCastleMovieId(secKey,meta){
/* NUVIO_CASTLE_STRICT_IDENTITY_V1 */
function norm(v){var x=String(v==null?"":v);try{x=x.normalize("NFD").replace(/[\u0300-\u036f]/g,"")}catch(_e){}return x.toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
var title=String(meta&&meta.title||"").trim();
if(!title)throw new Error("Castle identity: missing target title");
var keyword=meta&&meta.year?title+" "+meta.year:title;
var response=await searchCastle(secKey,keyword),data=extractDataBlock(response)||{};
var rows=Array.isArray(data.rows)?data.rows:Array.isArray(data.results)?data.results:Array.isArray(data.list)?data.list:[];
if(!rows.length)throw new Error("Castle identity: no search results");
var target=norm(title),best=null,bestScore=0;
for(var i=0;i<rows.length;i++){
  var row=rows[i]||{},name=String(row.title||row.name||"").trim(),candidate=norm(name);
  if(!candidate)continue;
  var score=0;
  if(candidate===target)score=100;
  else if(candidate.length>=4&&target.length>=4&&(candidate.indexOf(target)>=0||target.indexOf(candidate)>=0)){
    var ratio=Math.min(candidate.length,target.length)/Math.max(candidate.length,target.length);
    if(ratio>=0.72)score=80+Math.round(ratio*10);
  }
  var expectedYear=Number(meta&&meta.year||0),rowYear=Number(row.year||row.releaseYear||row.release_year||0);
  if(expectedYear&&rowYear){if(expectedYear===rowYear)score+=10;else score-=30}
  if(score>bestScore){bestScore=score;best=row}
}
if(!best||bestScore<80)throw new Error("Castle identity: no sufficiently close title match");
var id=best.id||best.redirectId||best.redirectIdStr;
if(id==null||String(id).trim()==="")throw new Error("Castle identity: matched row has no id");
return String(id);
}'''
    output, changed = _replace_named_function(text, "findCastleMovieId", replacement)
    if not changed:
        raise ValueError("Castle strict identity patch could not find findCastleMovieId")
    return output


if __name__ == "__main__":
    raise SystemExit("patch module only")
