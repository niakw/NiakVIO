#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"automation/provider-repair-survival-registry.json"
OV=ROOT/"provider-overrides.json"
MANIFEST=ROOT/"manifest.json"

MANAGED_FIX_RE=re.compile(r'^\s*MANAGED_FIX_ID\s*=\s*["\']([^"\']+)["\']',re.M)


def canonical(value: object) -> str:
    return str(value or "").strip().casefold()


def managed_fix_id(script_path: Path) -> str:
    text=script_path.read_text(encoding="utf-8")
    m=MANAGED_FIX_RE.search(text)
    if not m:
        raise ValueError(f"{script_path.relative_to(ROOT)}: MANAGED_FIX_ID missing")
    return m.group(1)


def main()->int:
    reg=json.loads(REG.read_text(encoding="utf-8"))
    ov=json.loads(OV.read_text(encoding="utf-8"))
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    patches=ov.get("provider_patches") or {}
    manifest_rows={
        canonical(row.get("id")):row
        for row in manifest.get("scrapers") or manifest.get("providers") or []
        if isinstance(row,dict) and canonical(row.get("id"))
    }
    errors=[]
    checked=0
    bundle_checked=0
    for provider,rule in sorted((reg.get("providers") or {}).items()):
        row=patches.get(provider)
        if not isinstance(row,dict):
            errors.append(f"{provider}: missing override row")
            continue
        manifest_row=manifest_rows.get(canonical(provider))
        if not isinstance(manifest_row,dict):
            errors.append(f"{provider}: missing manifest row")
            continue
        rel=str(manifest_row.get("filename") or "").replace("../","").lstrip("/")
        bundle=ROOT/rel
        if not rel or not bundle.is_file():
            errors.append(f"{provider}: published bundle missing: {rel or '<empty>'}")
            continue
        bundle_text=bundle.read_text(encoding="utf-8")
        scripts=set(row.get("provider_lego_scripts") or [])
        for script in rule.get("requiredScripts") or []:
            checked+=1
            script_path=ROOT/script
            if script not in scripts:
                errors.append(f"{provider}: required repair script missing from authority: {script}")
                continue
            if not script_path.is_file():
                errors.append(f"{provider}: repair script path not found: {script}")
                continue
            try:
                fix_id=managed_fix_id(script_path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            bundle_checked+=1
            if fix_id not in bundle_text:
                errors.append(
                    f"{provider}: authority/bundle drift required={script} "
                    f"managed_fix={fix_id} bundle={rel}"
                )
        forbidden=set(rule.get("forbiddenScripts") or [])
        leaked=sorted(forbidden & scripts)
        for script in leaked:
            errors.append(f"{provider}: superseded script leaked into authority: {script}")
        for script in forbidden:
            script_path=ROOT/script
            if not script_path.is_file():
                continue
            try:
                fix_id=managed_fix_id(script_path)
            except ValueError:
                continue
            if fix_id in bundle_text:
                errors.append(
                    f"{provider}: superseded managed fix leaked into published bundle: "
                    f"{fix_id} bundle={rel}"
                )
    if errors:
        for e in errors:
            print("FIELD_PROVIDER_REPAIR_SURVIVAL_ERROR "+e)
        raise SystemExit(f"provider repair survival failed errors={len(errors)}")
    print(
        f"FIELD_PROVIDER_REPAIR_SURVIVAL_OK providers={len(reg.get('providers') or {})} "
        f"required_scripts={checked} published_fix_markers={bundle_checked}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
