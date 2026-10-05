#!/usr/bin/env python3
"""Fill or advance targeted Learning guidance with deterministic Brain meta-gap synthesis.

This is a hypothesis-only bridge: it never mutates provider/publication bytes and
never grants proof/publication authority. It is used only after cached/Qwen rows
were sanitized and negative-memory filtered. Targeted providers may receive the
next bounded already-sandboxed executor selected from current census and canonical
Repair memory even when an older, now-causally-exhausted row for that provider is
already present. This closes Learning-runtime -> persisted-guidance handoff.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0,str(SCRIPT_DIR))

from brain_layers.declarative_gap_strategy import synthesize_rows

ROW_FIELDS={
    "providerId","failureClass","targetLayer","strategy","profile",
    "confidence","priorOnly","experiment","experimentFingerprint",
}
SHA40=re.compile(r"^[0-9a-f]{40}$")


def canon(value:object)->str:
    return str(value or "").strip().casefold().replace("_","-")


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict) or not isinstance(value.get("rows"),list):
        raise ValueError(f"invalid guidance payload: {path}")
    return value


def public_row(raw:dict[str,Any])->dict[str,Any]:
    row={key:raw.get(key) for key in ROW_FIELDS}
    if (
        not canon(row.get("providerId"))
        or row.get("targetLayer")!="provider"
        or row.get("priorOnly") is not True
        or not str(row.get("profile") or "").strip()
        or not re.fullmatch(r"[0-9a-f]{64}",str(row.get("experimentFingerprint") or "").strip().casefold())
        or not isinstance(row.get("experiment"),dict)
    ):
        raise ValueError("unsafe synthesized Learning guidance row")
    return row


def fill(
    payload:dict[str,Any],
    *,
    providers:list[str],
    current_sha:str,
    census:dict[str,Any],
    memory:dict[str,Any],
)->tuple[dict[str,Any],list[str]]:
    wanted=[]
    seen_wanted=set()
    for raw in providers:
        provider=canon(raw)
        if provider and provider not in seen_wanted:
            seen_wanted.add(provider);wanted.append(provider)
    out=json.loads(json.dumps(payload))
    rows=[row for row in out.get("rows") or [] if isinstance(row,dict)]
    existing_keys={
        (
            canon(row.get("providerId")),
            str(row.get("profile") or "").strip().casefold(),
            str(row.get("experimentFingerprint") or "").strip().casefold(),
        )
        for row in rows
    }

    synthesized=synthesize_rows(census=census,memory=memory,current_sha=current_sha,max_rows=128)
    by_provider={}
    for raw in synthesized:
        if not isinstance(raw,dict):
            continue
        provider=canon(raw.get("providerId"))
        if provider in seen_wanted and provider not in by_provider:
            by_provider[provider]=public_row(raw)

    added=[]
    for provider in wanted:
        row=by_provider.get(provider)
        if row is None:
            continue
        key=(
            provider,
            str(row.get("profile") or "").strip().casefold(),
            str(row.get("experimentFingerprint") or "").strip().casefold(),
        )
        if key in existing_keys:
            continue
        rows.append(row)
        existing_keys.add(key)
        added.append(provider)
    out["rows"]=rows
    out["providerCount"]=len({canon(row.get("providerId")) for row in rows if canon(row.get("providerId"))})
    if SHA40.fullmatch(str(current_sha or "").strip().casefold()):
        out["sourceSha"]=str(current_sha).strip().casefold()
    return out,added


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--provider",action="append",default=[])
    p.add_argument("--providers",default="")
    p.add_argument("--current-sha",required=True)
    p.add_argument("--census",type=Path,default=Path("automation/provider-census-status.json"))
    p.add_argument("--memory",type=Path,default=Path("automation/brain-repair-memory.json"))
    a=p.parse_args()
    providers=[*a.provider,*str(a.providers or "").split(",")]
    payload=load(a.input)
    census=json.loads(a.census.read_text(encoding="utf-8"))
    memory=json.loads(a.memory.read_text(encoding="utf-8"))
    output,added=fill(payload,providers=providers,current_sha=a.current_sha,census=census,memory=memory)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(
        "FIELD_BRAIN_LEARNING_GUIDANCE_GAP_FILL "
        f"requested={len({canon(x) for x in providers if canon(x)})} "
        f"advanced={len(added)} providers={','.join(added) or 'none'} "
        f"final={output.get('providerCount',0)}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
