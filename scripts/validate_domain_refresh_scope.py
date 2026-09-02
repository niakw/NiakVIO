#!/usr/bin/env python3
"""Fail closed unless provider-overrides drift is strictly route-maintenance DATA."""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from typing import Any

ROUTE_KEYS={
    "official_hub","official_site","official_api","replacements",
    "runtime_domain_replacements","fixed_endpoint","api_recipe",
}
ROUTE_OPTION_FIELDS={
    "scripts/provider_patches/toflix_official_endpoint.py":{"site","fallback_api"},
    "scripts/provider_patches/vf_catalogue_recovery.py":{"base_url","api_url"},
}

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise SystemExit(f"{path}: object required")
    return value

def scrub(row:dict[str,Any])->dict[str,Any]:
    out=copy.deepcopy(row)
    for key in ROUTE_KEYS:
        out.pop(key,None)
    options=out.get("patch_script_options")
    if isinstance(options,dict):
        for script,fields in ROUTE_OPTION_FIELDS.items():
            cfg=options.get(script)
            if isinstance(cfg,dict):
                for field in fields: cfg.pop(field,None)
                if not cfg: options.pop(script,None)
        if not options: out.pop("patch_script_options",None)
    mo=out.get("manifest_overrides")
    if isinstance(mo,dict):
        mo.pop("logo",None)
        if not mo: out.pop("manifest_overrides",None)
    return out

def required_values_safe(before:dict[str,Any],after:dict[str,Any])->bool:
    b=[str(v) for v in before.get("required_values") or []]
    a=[str(v) for v in after.get("required_values") or []]
    return set(a).issubset(set(b))

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
        if b.get("patch_scripts")!=a.get("patch_scripts"):
            raise SystemExit(f"{pid}: domain refresh changed patch_scripts")
        if not required_values_safe(b,a):
            raise SystemExit(f"{pid}: domain refresh added required_values")
        bs=scrub(b); ass=scrub(a)
        bs.pop("required_values",None); ass.pop("required_values",None)
        if bs!=ass:
            raise SystemExit(f"{pid}: domain refresh changed non-route Provider DATA")
        changed.append(pid)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"changed":changed},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"FIELD_DOMAIN_REFRESH_SCOPE providers={len(changed)} fix_mutation=false")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
