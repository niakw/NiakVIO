#!/usr/bin/env python3
"""Activate bulk-staged providers only after a current FULL OK census proof."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"manifest.json"
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

def main()->int:
    ap=argparse.ArgumentParser(description="Activate only bulk-pending providers with current FULL OK proof")
    ap.add_argument("--status",type=Path,default=STATUS)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()

    status=load(args.status,{})
    manifest=load(MANIFEST,{"scrapers":[]})
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
        patch=patches.get(pid)
        prov=prov_map.get(pid)
        if not isinstance(manifest_row,dict) or not isinstance(patch,dict) or not isinstance(prov,dict):
            blocked.append({"provider":pid,"reason":"canonical_provider_state_missing"})
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
            "runId":run_id,
            "triggerSha":trigger_sha,
            "status":"FULL OK",
            "declaredLanes":sorted(declared),
            "verifiedLanes":sorted(verified),
        }
        activated.append(pid)

    payload={
        "schemaVersion":1,
        "sourceRunId":run_id,
        "sourceTriggerSha":trigger_sha,
        "pendingBulkProviderCount":len(pending),
        "activationCount":len(activated),
        "activatedProviders":activated,
        "blockedCount":len(blocked),
        "blockedProviders":blocked,
        "policy":"FULL OK + every declared lane currently verified + no remaining Brain check",
        "dryRun":bool(args.dry_run),
    }
    if not args.dry_run and activated:
        write(MANIFEST,manifest)
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
