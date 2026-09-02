#!/usr/bin/env python3
"""Fail closed unless Domain Refresh changed only the provider primary site URL."""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from typing import Any

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise SystemExit(f"{path}: object required")
    return value

def strip_domain(row:dict[str,Any])->dict[str,Any]:
    out=copy.deepcopy(row)
    out.pop("official_site",None)
    return out

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--before",type=Path,required=True)
    p.add_argument("--after",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    before=load(args.before); after=load(args.after)
    for key in sorted(set(before)|set(after)):
        if key=="provider_patches": continue
        if before.get(key)!=after.get(key):
            raise SystemExit(f"domain refresh changed forbidden top-level key: {key}")
    bp=before.get("provider_patches") or {}; ap=after.get("provider_patches") or {}
    if set(bp)!=set(ap): raise SystemExit("domain refresh may not add/remove provider patches")
    changed=[]
    for pid in sorted(bp):
        b=bp[pid]; a=ap[pid]
        if b==a: continue
        if not isinstance(b,dict) or not isinstance(a,dict):
            raise SystemExit(f"{pid}: provider patch object shape changed")
        if strip_domain(b)!=strip_domain(a):
            raise SystemExit(f"{pid}: domain refresh changed DATA beyond official_site")
        before_site=str(b.get("official_site") or "").rstrip("/")
        after_site=str(a.get("official_site") or "").rstrip("/")
        if not after_site:
            raise SystemExit(f"{pid}: domain refresh may not clear official_site")
        if before_site!=after_site:
            changed.append(pid)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"changed":changed,"field":"official_site"},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"FIELD_DOMAIN_REFRESH_SCOPE providers={len(changed)} field=official_site fix_mutation=false")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
