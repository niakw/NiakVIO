#!/usr/bin/env python3
"""Drop already failed Brain advisor fingerprints from sanitized Learning guidance."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0,str(SCRIPT_DIR))

from import_external_brain_llm_guidance import filter_failed_guidance_files


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(f"guidance payload must be an object: {path}")
    rows=value.get("rows")
    if not isinstance(rows,list):
        raise ValueError(f"guidance rows missing: {path}")
    return value


def filter_guidance(payload:dict[str,Any],negative_memories:list[Path])->tuple[dict[str,Any],int]:
    # Copy through JSON to avoid mutating caller-owned nested rows.
    current=json.loads(json.dumps(payload))
    current,dropped=filter_failed_guidance_files(current,negative_memories)
    current["providerCount"]=len({
        str(row.get("providerId") or "").strip().casefold().replace("_","-")
        for row in current.get("rows") or []
        if isinstance(row,dict) and str(row.get("providerId") or "").strip()
    })
    return current,dropped


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--negative-memory",type=Path,action="append",default=[])
    a=p.parse_args()

    payload=load(a.input)
    filtered,dropped=filter_guidance(payload,list(a.negative_memory or []))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(filtered,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(
        "FIELD_BRAIN_LEARNING_GUIDANCE_NEGATIVE_FILTER "
        f"providers={filtered.get('providerCount',0)} rows={len(filtered.get('rows') or [])} "
        f"dropped_failed_fingerprints={dropped} memories={len(a.negative_memory or [])}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
