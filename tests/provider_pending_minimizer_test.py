#!/usr/bin/env python3
"""Bulk-staged pending providers must be exact minimizer fixed-points before live proof."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str((ROOT/"scripts").resolve()))
from provider_v3_minimizer import minimize_text, validate_transform

stage=json.loads((ROOT/"automation/provider-bulk-onboarding-stage.json").read_text(encoding="utf-8"))
manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
vf=json.loads((ROOT/"vf/manifest.json").read_text(encoding="utf-8"))
provenance=json.loads((ROOT/"PROVENANCE.json").read_text(encoding="utf-8"))
rows={}
for source,prefix in ((manifest,""),(vf,"../")):
    for row in source.get("scrapers") or []:
        if not isinstance(row,dict):
            continue
        pid=str(row.get("id") or "").strip().casefold().replace("_","-")
        if pid and pid not in rows:
            rows[pid]=row

checked=[]
for item in stage.get("providers") or []:
    if not isinstance(item,dict):
        continue
    pid=str(item.get("id") or "").strip().casefold().replace("_","-")
    row=rows.get(pid)
    assert row is not None, pid
    assert row.get("enabled") is False, pid
    relative=str(row.get("filename") or "").replace("../","",1)
    assert relative.startswith("provider-disabled/"), (pid,relative)
    path=ROOT/relative
    assert path.is_file(), (pid,relative)
    text=path.read_text(encoding="utf-8")
    result=minimize_text(text)
    validate_transform(text,result.text)
    assert result.text==text, f"{pid}: pending bytes are not minimizer fixed-point"
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    meta=(provenance.get("providers") or {}).get(pid) or {}
    assert str(meta.get("sha256") or "").casefold()==digest, (pid,"provenance-sha")
    assert str(meta.get("published_filename") or "")==relative, (pid,"provenance-path")
    assert item.get("pendingFixedPoint") is True, (pid,item)
    assert str(item.get("pendingSha256") or "").casefold()==digest, (pid,"stage-sha")
    checked.append(pid)

assert checked, "bulk stage contains no providers"
print("PENDING_PROVIDER_MINIMIZER_OK providers="+",".join(sorted(checked)))
