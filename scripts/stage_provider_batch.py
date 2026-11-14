#!/usr/bin/env python3
"""Stage many providers atomically as disabled/pending NiakVIO entries.

This is the high-volume onboarding path. It intentionally performs no per-provider
network discovery, branding fetch, native client Lab, or activation. Those steps
belong to the sharded census / batch-repair / proof-driven activation pipeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import add_provider
import provider_base_store
from provider_v3_minimizer import minimize_text, validate_transform

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_REQUEST=ROOT/".github/provider-onboarding/batch.json"
DEFAULT_OUTPUT=ROOT/"automation/provider-bulk-onboarding-stage.json"


def load_requests(path:Path)->list[dict[str,Any]]:
    value=json.loads(path.read_text(encoding="utf-8"))
    rows=value.get("providers") if isinstance(value,dict) else value
    if not isinstance(rows,list):
        raise ValueError("bulk onboarding request must be a list or {providers:[...]}")
    if not rows:
        raise ValueError("bulk onboarding request is empty")
    if len(rows)>2000:
        raise ValueError("bulk onboarding request exceeds 2000 providers")
    out=[]
    seen=set()
    for index,row in enumerate(rows):
        if not isinstance(row,dict):
            raise ValueError(f"provider row {index} must be an object")
        pid=add_provider.norm_id(row.get("id") or row.get("provider"))
        if pid in seen:
            raise ValueError(f"duplicate provider id in bulk request: {pid}")
        seen.add(pid)
        normalized=dict(row)
        normalized["id"]=pid
        out.append(normalized)
    return out


def safe_pending_restage_ids(manifest:dict[str,Any], vf_manifest:dict[str,Any], provenance:dict[str,Any])->set[str]:
    prov=provenance.get("providers") if isinstance(provenance.get("providers"),dict) else {}
    result=set()
    for source in (manifest,vf_manifest):
        for row in source.get("scrapers") or []:
            if not isinstance(row,dict):
                continue
            pid=add_provider.norm_id(row.get("id"))
            meta=prov.get(pid) if isinstance(prov.get(pid),dict) else {}
            filename=str(row.get("filename") or "").replace("../","",1)
            if pid and row.get("enabled") is False and filename.startswith("provider-disabled/") and str(meta.get("activation_mode") or "") in {"bulk_onboarding_pending","onboarding_pending"}:
                result.add(pid)
    return result


def preflight(rows:list[dict[str,Any]], allow_replace_existing:bool)->dict[str,Any]:
    manifest=add_provider.load_json(add_provider.MANIFEST,{})
    vf_manifest=add_provider.load_json(add_provider.VF_MANIFEST,{"scrapers":[]})
    provenance=add_provider.load_json(add_provider.PROVENANCE,{"providers":{}})
    safe_pending_restage=safe_pending_restage_ids(manifest,vf_manifest,provenance)
    existing={
        add_provider.norm_id(row.get("id"))
        for row in manifest.get("scrapers") or []
        if isinstance(row,dict) and str(row.get("id") or "").strip()
    }
    vf_ids={add_provider.norm_id(row.get("id")) for row in vf_manifest.get("scrapers") or [] if isinstance(row,dict) and row.get("id")}
    france_only=vf_ids-existing
    replacing=[]
    new=[]
    strategies=Counter()
    type_counts=Counter()
    scope_counts=Counter()
    for row in rows:
        pid=str(row["id"])
        replace=add_provider.bool_value(row.get("replace_existing"),False)
        scope=add_provider.normalized_scope(row.get("scope") or row.get("manifest_scope") or "global")
        scope_counts[scope]+=1
        target_existing=existing if scope=="global" else france_only
        if scope=="france" and pid in existing:
            raise ValueError(f"{pid}: Global provider cannot be duplicated as France-only")
        if scope=="global" and pid in france_only:
            raise ValueError(f"{pid}: France-only provider cannot be duplicated in Global")
        if replace and not allow_replace_existing and pid not in safe_pending_restage:
            raise ValueError(f"{pid}: replace_existing requires --allow-replace-existing unless replacing the same disabled pending onboarding identity")
        if pid in target_existing and not replace:
            raise ValueError(f"{pid}: provider already exists in {scope} scope; bulk import refuses silent overwrite")
        (replacing if pid in target_existing else new).append(pid)
        strategy=str(row.get("strategy") or "html_scraper").strip().casefold()
        strategies[strategy]+=1
        for media in add_provider.normalized_types(row.get("types") or row.get("supportedTypes")):
            type_counts[media]+=1
    return {
        "providerCount":len(rows),
        "newProviderCount":len(new),
        "replaceProviderCount":len(replacing),
        "newProviders":sorted(new),
        "replaceProviders":sorted(replacing),
        "strategies":dict(sorted(strategies.items())),
        "declaredTypeCounts":dict(sorted(type_counts.items())),
        "scopeCounts":dict(sorted(scope_counts.items())),
        "safePendingRestageProviders":sorted(pid for pid in replacing if pid in safe_pending_restage),
    }



def finalize_staged_pending_bundle(provider_id:str, scope:str)->dict[str,Any]:
    """Put a staged pending provider at the exact safe minimizer fixed-point."""
    manifest_path=add_provider.VF_MANIFEST if scope=="france" else add_provider.MANIFEST
    manifest=add_provider.load_json(manifest_path,{"scrapers":[]})
    rows=[
        row for row in manifest.get("scrapers") or []
        if isinstance(row,dict) and add_provider.norm_id(row.get("id"))==provider_id
    ]
    if len(rows)!=1:
        raise ValueError(f"{provider_id}: pending manifest row is not unique in {scope}")
    row=rows[0]
    if row.get("enabled") is not False:
        raise ValueError(f"{provider_id}: pending minimizer refuses an enabled provider")
    relative=str(row.get("filename") or "").strip()
    local_relative=relative[3:] if relative.startswith("../") else relative
    if not local_relative.startswith("provider-disabled/"):
        raise ValueError(f"{provider_id}: pending minimizer path is not provider-disabled: {relative}")
    source=(ROOT/local_relative).resolve()
    disabled_root=(ROOT/"provider-disabled").resolve()
    if disabled_root not in source.parents or not source.is_file():
        raise ValueError(f"{provider_id}: unsafe or missing pending provider path")
    original=source.read_text(encoding="utf-8")
    result=minimize_text(original)
    validate_transform(original,result.text)
    minimized=result.text.encode("utf-8")
    with tempfile.NamedTemporaryFile("wb",suffix=".js",delete=False) as fh:
        fh.write(minimized)
        check_path=Path(fh.name)
    try:
        proc=subprocess.run(["node","--check",str(check_path)],cwd=ROOT,text=True,capture_output=True,timeout=30,check=False)
        if proc.returncode!=0:
            raise ValueError(f"{provider_id}: minimized pending JS parse failed: {proc.stdout}{proc.stderr}")
    finally:
        check_path.unlink(missing_ok=True)
    digest=hashlib.sha256(minimized).hexdigest()
    target=source.with_name(f"{provider_id}--nuvio--{digest[:16]}.js")
    if target.exists() and target.read_bytes()!=minimized:
        raise ValueError(f"{provider_id}: pending minimizer content-address collision")
    target.write_bytes(minimized)
    if target!=source:
        source.unlink()
    target_relative=target.relative_to(ROOT).as_posix()
    row["filename"]=("../"+target_relative) if scope=="france" else target_relative
    add_provider.write_json(manifest_path,manifest)
    provenance=add_provider.load_json(add_provider.PROVENANCE,{"providers":{}})
    meta=(provenance.get("providers") or {}).get(provider_id)
    if not isinstance(meta,dict):
        raise ValueError(f"{provider_id}: missing provenance during pending minimizer")
    meta["published_filename"]=target_relative
    meta["sha256"]=digest
    if "patched_sha256" in meta:
        meta["patched_sha256"]=digest
    meta["pending_minimizer"]={
        "schemaVersion":1,
        "fixedPoint":True,
        "sha256":digest,
        "savedBytes":int(result.saved_bytes),
        "transformedLines":int(result.transformed_lines),
    }
    add_provider.write_json(add_provider.PROVENANCE,provenance)
    return {"filename":target_relative,"sha256":digest,"savedBytes":int(result.saved_bytes)}


def main()->int:
    ap=argparse.ArgumentParser(description="Bulk-stage providers as disabled/pending")
    ap.add_argument("--request",type=Path,default=DEFAULT_REQUEST)
    ap.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    ap.add_argument("--allow-replace-existing",action="store_true")
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()

    rows=load_requests(args.request)
    summary=preflight(rows,args.allow_replace_existing)
    summary.update({
        "schemaVersion":1,
        "request":str(args.request),
        "mode":"dry-run" if args.dry_run else "staged-disabled-pending",
        "networkDiscoveryExecuted":False,
        "nativeLabExecuted":False,
        "activationAttempted":False,
        "nextStage":"sharded census -> repair batches -> proof-driven activation",
    })
    if args.dry_run:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"PROVIDER_BULK_ONBOARDING_DRY_RUN providers={summary['providerCount']}")
        return 0

    staged=[]
    with tempfile.TemporaryDirectory(prefix="niakvio-provider-bulk-") as td:
        temp=Path(td)
        for index,row in enumerate(rows):
            request=temp/f"{index:04d}-{row['id']}.json"
            request.write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            normalized=add_provider.stage(request,bulk=True)
            fixed=finalize_staged_pending_bundle(normalized["id"],normalized["scope"])
            staged.append({
                "id":normalized["id"],
                "name":normalized["name"],
                "types":normalized["types"],
                "strategy":normalized["strategy"],
                "site":normalized.get("site") or None,
                "scope":normalized["scope"],
                "pendingFilename":fixed["filename"],
                "pendingSha256":fixed["sha256"],
                "pendingFixedPoint":True,
            })
    # The ordinary one-provider path repairs the base store after each stage.
    # Bulk mode defers that O(N) repository sweep and performs it exactly once.
    provider_base_store.repair_legacy_bases()
    summary["providers"]=staged
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "PROVIDER_BULK_ONBOARDING_STAGED "
        f"providers={summary['providerCount']} new={summary['newProviderCount']} "
        f"replace={summary['replaceProviderCount']}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
