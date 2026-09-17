#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"automation/provider-repair-survival-registry.json"
OV=ROOT/"provider-overrides.json"

def main()->int:
    reg=json.loads(REG.read_text(encoding="utf-8"))
    ov=json.loads(OV.read_text(encoding="utf-8"))
    patches=ov.get("provider_patches") or {}
    errors=[]
    checked=0
    for provider,rule in sorted((reg.get("providers") or {}).items()):
        row=patches.get(provider)
        if not isinstance(row,dict):
            errors.append(f"{provider}: missing override row"); continue
        scripts=set(row.get("provider_lego_scripts") or [])
        for script in rule.get("requiredScripts") or []:
            checked+=1
            if script not in scripts: errors.append(f"{provider}: required repair script missing: {script}")
            elif not (ROOT/script).is_file(): errors.append(f"{provider}: repair script path not found: {script}")
    if errors:
        for e in errors: print("FIELD_PROVIDER_REPAIR_SURVIVAL_ERROR "+e)
        raise SystemExit(f"provider repair survival failed errors={len(errors)}")
    print(f"FIELD_PROVIDER_REPAIR_SURVIVAL_OK providers={len(reg.get('providers') or {})} required_scripts={checked}")
    return 0
if __name__=="__main__": raise SystemExit(main())
