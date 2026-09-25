#!/usr/bin/env python3
"""Fail if an already-published versioned badge artifact was edited or removed."""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATHSPECS=(
    "assets/badge_catalog_v*_complete.json",
    "assets/mapping_core_brain_ui_v*_complete.json",
    "assets/stream-badges-*-v*.json",
)

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",default="")
    parser.add_argument("--head",default="HEAD")
    args=parser.parse_args()
    base=str(args.base or "").strip()
    if not base or set(base)=={"0"}:
        completed=subprocess.run(["git","rev-parse",f"{args.head}^"],cwd=ROOT,text=True,capture_output=True,check=False)
        base=completed.stdout.strip() if completed.returncode==0 else ""
    if not base:
        print("FIELD_BADGE_IMMUTABILITY skipped=no-base")
        return 0
    completed=subprocess.run(["git","diff","--name-status",base,args.head,"--",*PATHSPECS],cwd=ROOT,text=True,capture_output=True,check=True)
    violations=[]
    added=[]
    for raw in completed.stdout.splitlines():
        parts=raw.split("\t")
        if not parts: continue
        status=parts[0]
        paths=parts[1:]
        if status.startswith("A"): added.extend(paths)
        else: violations.append(raw)
    if violations:
        raise SystemExit("published versioned badge artifacts are immutable; create vN+1 instead:\n"+"\n".join(violations))
    print(f"FIELD_BADGE_IMMUTABILITY ok added={len(added)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
