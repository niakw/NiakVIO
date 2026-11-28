#!/usr/bin/env python3
"""Prune retained generated provider versions from the CodeQL workspace only."""
from __future__ import annotations
import argparse, json
from pathlib import Path
MANIFESTS=("manifest.json","vf/manifest.json","no-anime/manifest.json","vf-no-anime/manifest.json")
def published_provider_paths(root:Path)->set[str]:
    active:set[str]=set()
    for relative in MANIFESTS:
        data=json.loads((root/relative).read_text(encoding="utf-8"))
        rows=data.get("scrapers") if isinstance(data,dict) else None
        if not isinstance(rows,list): raise ValueError(f"{relative}: scrapers must be a list")
        for row in rows:
            if not isinstance(row,dict): continue
            filename=str(row.get("filename") or "").strip().replace("\\","/")
            if not filename: continue
            path=Path(filename)
            if path.is_absolute() or ".." in path.parts or path.suffix!=".js":
                raise ValueError(f"{relative}: invalid provider filename {filename!r}")
            if len(path.parts)==2 and path.parts[0] in {"provider-disabled","provider-old"}:
                continue
            if len(path.parts)!=2 or path.parts[0]!="providers":
                raise ValueError(f"{relative}: unexpected published-provider path {filename!r}")
            active.add(path.as_posix())
    if not active: raise ValueError("production manifests expose no provider JS")
    missing=sorted(path for path in active if not (root/path).is_file())
    if missing: raise FileNotFoundError("published provider JS missing: "+",".join(missing[:10]))
    return active
def prune_workspace(root:Path)->tuple[int,int]:
    active=published_provider_paths(root); provider_root=root/"providers"; removed=0
    for path in sorted(provider_root.glob("*.js")):
        if path.is_file() and path.relative_to(root).as_posix() not in active:
            path.unlink(); removed+=1
    remaining={path.relative_to(root).as_posix() for path in provider_root.glob("*.js") if path.is_file()}
    if remaining!=active: raise RuntimeError("CodeQL active-provider projection does not equal production manifests")
    return len(active),removed
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(".")); args=ap.parse_args()
    active,removed=prune_workspace(args.root.resolve())
    print(f"FIELD_CODEQL_ACTIVE_PROVIDER_SCOPE active={active} retained_removed_from_workspace={removed} repository_retention_unchanged=true")
    return 0
if __name__=="__main__": raise SystemExit(main())
