#!/usr/bin/env python3
"""Activate bulk-staged providers only after a current FULL OK census proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"manifest.json"
CATALOG=ROOT/"provider_catalog.json"
OVERRIDES=ROOT/"provider-overrides.json"
PROVENANCE=ROOT/"PROVENANCE.json"
HUBS=ROOT/"provider-hubs.json"
STATUS=ROOT/"automation/provider-census-status.json"
OUTPUT=ROOT/"automation/provider-bulk-activation-latest.json"

def load(path:Path, default:Any)->Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def write(path:Path, value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def norm(value:Any)->str:
    return re.sub(r"[^a-z0-9._-]+","-",str(value or "").strip().casefold()).strip("-")


def _move_exact(source:Path,target:Path,*,dry_run:bool=False)->None:
    if not source.is_file():
        raise RuntimeError(f"missing pending artifact: {source}")
    if target.exists() and source.read_bytes()!=target.read_bytes():
        raise RuntimeError(f"activation artifact collision: {target}")
    if dry_run:
        return
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        source.unlink()
    else:
        source.replace(target)

def restore_pending_artifacts(
    pid:str,
    manifest_row:dict[str,Any],
    provenance_row:dict[str,Any],
    *,
    dry_run:bool=False,
)->str:
    """Restore one FULL-OK bulk candidate to executable directories."""
    filename=str(manifest_row.get("filename") or "").strip()
    if filename.startswith("../"):
        filename=filename[3:]
    if not filename.startswith("provider-disabled/"):
        raise RuntimeError(f"{pid}: pending provider path is not disabled: {filename}")
    source=(ROOT/filename).resolve()
    target=(ROOT/"providers"/source.name).resolve()
    base_relative=str(provenance_row.get("base_filename") or "").strip()
    if not base_relative.startswith("provider-bases/"):
        raise RuntimeError(f"{pid}: pending ProviderBase reference invalid: {base_relative}")
    base_target=(ROOT/base_relative).resolve()
    base_source=(ROOT/"provider-disabled"/"provider-bases"/base_target.name).resolve()
    _move_exact(source,target,dry_run=dry_run)
    _move_exact(base_source,base_target,dry_run=dry_run)
    active_relative=target.relative_to(ROOT).as_posix()
    manifest_row["filename"]=active_relative
    provenance_row["published_filename"]=active_relative
    return active_relative

def main()->int:
    ap=argparse.ArgumentParser(description="Activate only bulk-pending providers with current FULL OK proof")
    ap.add_argument("--status",type=Path,default=STATUS)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()

    status=load(args.status,{})
    manifest=load(MANIFEST,{"scrapers":[]})
    catalog=load(CATALOG,{"providers":[]})
    overrides=load(OVERRIDES,{})
    provenance=load(PROVENANCE,{"providers":{}})
    hubs=load(HUBS,{"providers":{}})

    status_map={
        norm(row.get("provider")):row
        for row in status.get("providers") or []
        if isinstance(row,dict) and norm(row.get("provider"))
    }
    manifest_map={
        norm(row.get("id")):row
        for row in manifest.get("scrapers") or []
        if isinstance(row,dict) and norm(row.get("id"))
    }
    catalog_map={
        norm(entry.get("canonicalId") or ((entry.get("scraper") or {}).get("id") if isinstance(entry.get("scraper"),dict) else "")):entry
        for entry in catalog.get("providers") or [] if isinstance(entry,dict)
    }
    prov_map=provenance.get("providers") if isinstance(provenance.get("providers"),dict) else {}
    patches=overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"),dict) else {}
    capabilities=overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"),dict) else {}
    hub_map=hubs.get("providers") if isinstance(hubs.get("providers"),dict) else {}

    pending=sorted(
        norm(pid)
        for pid,row in prov_map.items()
        if isinstance(row,dict) and str(row.get("activation_mode") or "")=="bulk_onboarding_pending"
    )
    activated=[]
    blocked=[]
    run_id=status.get("runId")
    trigger_sha=status.get("triggerSha")
    for pid in pending:
        proof=status_map.get(pid)
        if not isinstance(proof,dict):
            blocked.append({"provider":pid,"reason":"missing_current_census_row"})
            continue
        if str(proof.get("status") or "")!="FULL OK":
            blocked.append({"provider":pid,"reason":"not_full_ok","status":proof.get("status")})
            continue
        if proof.get("testedThisRun") is not True:
            blocked.append({"provider":pid,"reason":"full_ok_not_fresh_this_run"})
            continue
        declared={str(x).strip().lower() for x in proof.get("declaredLanes") or [] if str(x).strip()}
        verified={str(x).strip().lower() for x in proof.get("currentVerifiedLanes") or [] if str(x).strip()}
        if not declared or not declared.issubset(verified):
            blocked.append({
                "provider":pid,
                "reason":"declared_lanes_not_currently_verified",
                "declaredLanes":sorted(declared),
                "currentVerifiedLanes":sorted(verified),
            })
            continue
        if proof.get("brainCheckRequired") is True:
            blocked.append({"provider":pid,"reason":"brain_check_still_required"})
            continue
        manifest_row=manifest_map.get(pid)
        catalog_entry=catalog_map.get(pid)
        scope="global"
        if not isinstance(manifest_row,dict) and isinstance(catalog_entry,dict):
            projections=catalog_entry.get("projections") if isinstance(catalog_entry.get("projections"),dict) else {}
            if projections.get("general") is False and projections.get("vf") is True and isinstance(catalog_entry.get("scraper"),dict):
                manifest_row=catalog_entry["scraper"]
                scope="france"
        patch=patches.get(pid)
        prov=prov_map.get(pid)
        if not isinstance(manifest_row,dict) or not isinstance(patch,dict) or not isinstance(prov,dict):
            blocked.append({"provider":pid,"reason":"canonical_provider_state_missing"})
            continue
        try:
            restore_pending_artifacts(pid,manifest_row,prov,dry_run=args.dry_run)
        except RuntimeError as exc:
            blocked.append({"provider":pid,"reason":"pending_artifact_state_invalid","detail":str(exc)})
            continue
        active_path=ROOT/active_relative
        active_sha=hashlib.sha256(active_path.read_bytes()).hexdigest()
        recorded_sha=str(prov.get("sha256") or "").strip().casefold()
        if len(recorded_sha)==64 and recorded_sha!=active_sha:
            blocked.append({"provider":pid,"reason":"pending_artifact_hash_mismatch"})
            continue
        manifest_row["enabled"]=True
        patch.setdefault("manifest_overrides",{})["enabled"]=True
        capability=capabilities.get(pid)
        if isinstance(capability,dict):
            capability["validation"]="bulk_census_full_ok"
        hub=hub_map.get(pid)
        if isinstance(hub,dict):
            hub["manifest_status"]="Active"
        prov["checked_at"]=prov.get("checked_at")
        prov["check_mode"]="bulk_sharded_census"
        prov["check_status"]="healthy"
        prov["activation_eligible"]=True
        prov["strict_activation_eligible"]=True
        prov["runtime_evidence_eligible"]=True
        prov["activation_mode"]="bulk_census_full_ok"
        prov["activation_blockers"]=[]
        prov["bulk_activation_proof"]={
            "scope":scope,
            "runId":run_id,
            "triggerSha":trigger_sha,
            "status":"FULL OK",
            "declaredLanes":sorted(declared),
            "verifiedLanes":sorted(verified),
            "providerSha256":active_sha,
            "proofSource":"onboarding-pending-status",
        }
        activated.append(pid)

    payload={
        "schemaVersion":1,
        "sourceRunId":run_id,
        "sourceTriggerSha":trigger_sha,
        "pendingBulkProviderCount":len(pending),
        "activationCount":len(activated),
        "activatedProviders":activated,
        "activationScopes":{pid:("global" if pid in manifest_map else "france") for pid in activated},
        "blockedCount":len(blocked),
        "blockedProviders":blocked,
        "policy":"fresh FULL OK (testedThisRun) + every declared lane currently verified + no remaining Brain check",
        "dryRun":bool(args.dry_run),
    }
    if not args.dry_run and activated:
        write(MANIFEST,manifest)
        write(CATALOG,catalog)
        write(OVERRIDES,overrides)
        write(PROVENANCE,provenance)
        write(HUBS,hubs)
    write(args.output,payload)
    print(
        "PROVIDER_BULK_ACTIVATION "
        f"pending={len(pending)} activated={len(activated)} blocked={len(blocked)} "
        f"dry_run={str(args.dry_run).lower()}"
    )
    return 0

if __name__=="__main__":
    raise SystemExit(main())
