#!/usr/bin/env python3
"""Update only PROVIDER.*.CONFIG.V1 officialSite for authoritative hub domain changes.

No Provider/Core patch is executed. Bytes outside the CONFIG Lego must remain
identical. The content-addressed provider filename, manifest reference and
materialization inventory are updated deterministically.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any
from provider_patch_blocks import decode_managed_data, owned_span, replace_provider_fix, validate_managed_fixes

ROOT=Path(__file__).resolve().parents[1]

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise SystemExit(f"{path}: object required")
    return value

def write(path:Path,value:Any)->None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def canonical(v)->str:
    return str(v or "").strip().casefold()

def component(pid:str)->str:
    return re.sub(r"[^A-Z0-9_.:-]+","_",pid.upper()).strip("_.:-")

def data_digest(data:dict[str,Any])->str:
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def generation(rows:list[dict[str,Any]])->str:
    h=hashlib.sha256()
    for row in rows:
        pid=canonical(row.get("provider")); sha=str(row.get("sha256") or "")
        if not pid or not re.fullmatch(r"[0-9a-f]{64}",sha):
            raise SystemExit(f"invalid materialization row: {pid!r}")
        h.update(pid.encode("utf-8")); h.update(bytes.fromhex(sha))
    return h.hexdigest()

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--changes",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=ROOT/"manifest.json")
    p.add_argument("--overrides",type=Path,default=ROOT/"provider-overrides.json")
    p.add_argument("--materialization",type=Path,default=ROOT/"provider-v3-materialization.json")
    args=p.parse_args()
    changes=load(args.changes)
    if changes.get("field")!="official_site":
        raise SystemExit("domain updater accepts official_site changes only")
    requested=[canonical(v) for v in changes.get("changed") or [] if canonical(v)]
    if len(requested)!=len(set(requested)):
        raise SystemExit("duplicate domain change provider id")
    if not requested:
        print("FIELD_PROVIDER_DOMAIN_CONFIG_UPDATE providers=0 reconstruction=false")
        return 0

    manifest=load(args.manifest); overrides=load(args.overrides); material=load(args.materialization)
    mrows=manifest.get("scrapers") or []; rrows=material.get("providers") or []
    if len(mrows)!=96 or len(rrows)!=96:
        raise SystemExit("domain update requires 96/96 published Provider v3 state")
    mb={canonical(r.get("id")):r for r in mrows if isinstance(r,dict)}
    rb={canonical(r.get("provider")):r for r in rrows if isinstance(r,dict)}
    patches=overrides.get("provider_patches") or {}
    updated=[]

    for pid in requested:
        row=mb.get(pid); report=rb.get(pid); patch=patches.get(pid)
        if not isinstance(row,dict) or not isinstance(report,dict) or not isinstance(patch,dict):
            raise SystemExit(f"{pid}: missing manifest/materialization/provider DATA")
        site=str(patch.get("official_site") or "").rstrip("/")
        if not re.match(r"^https?://[^/]+",site):
            raise SystemExit(f"{pid}: invalid official_site {site!r}")
        old_rel=str(row.get("filename") or ""); old=ROOT/old_rel
        if not old_rel.startswith("providers/") or not old.is_file():
            raise SystemExit(f"{pid}: published provider missing {old_rel}")
        before=old.read_text(encoding="utf-8")
        fix_id=f"PROVIDER.{component(pid)}.CONFIG.V1"
        sb=owned_span(before,fix_id)
        if sb is None: raise SystemExit(f"{pid}: CONFIG Lego missing")
        data=decode_managed_data(before,fix_id)
        if canonical(data.get("providerId"))!=pid:
            raise SystemExit(f"{pid}: CONFIG providerId mismatch")
        if str(data.get("officialSite") or "").rstrip("/")==site:
            continue
        next_data=dict(data); next_data["officialSite"]=site
        payload=json.dumps(next_data,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        after=replace_provider_fix(before,fix_id,f"const NIAKVIO_PROVIDER_MODEL = Object.freeze({payload});",data=next_data)
        validate_managed_fixes(after)
        sa=owned_span(after,fix_id)
        if sa is None: raise SystemExit(f"{pid}: CONFIG Lego lost")
        if before[:sb[0]]+before[sb[1]:] != after[:sa[0]]+after[sa[1]:]:
            raise SystemExit(f"{pid}: domain update escaped CONFIG Lego")
        raw=after.encode("utf-8"); sha=hashlib.sha256(raw).hexdigest()
        new_rel=f"providers/{pid}-{sha[:16]}.js"; new=ROOT/new_rel
        new.write_bytes(raw)
        row["filename"]=new_rel
        report["file"]=new_rel; report["sha256"]=sha; report["providerDataSha256"]=data_digest(next_data)
        if old!=new and old.exists(): old.unlink()
        updated.append(pid)

    if updated:
        material["generation"]=generation(rrows)
        material["providerCount"]=96; material["expectedProviderCount"]=96
        material["domainConfigOnlyUpdate"]=True; material["domainConfigUpdatedProviders"]=updated
        write(args.manifest,manifest); write(args.materialization,material)
    print(f"FIELD_PROVIDER_DOMAIN_CONFIG_UPDATE providers={len(updated)} ids={','.join(updated)} reconstruction=false core_mutation=false")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
