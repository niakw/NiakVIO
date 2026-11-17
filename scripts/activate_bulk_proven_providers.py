#!/usr/bin/env python3
"""Activate bulk-staged providers only after a current FULL OK census proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from provider_v3_minimizer import minimize_text, validate_transform
from reconcile_provider_static_authority import exact_provider_lego_identity_contract, persist_static_from_bundle, refresh_static_counts

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"manifest.json"
CATALOG=ROOT/"provider_catalog.json"
OVERRIDES=ROOT/"provider-overrides.json"
PROVENANCE=ROOT/"PROVENANCE.json"
HUBS=ROOT/"provider-hubs.json"
STATUS=ROOT/"automation/provider-census-status.json"
OUTPUT=ROOT/"automation/provider-bulk-activation-latest.json"
STATIC_KNOWLEDGE=ROOT/"automation/provider-v3-static-knowledge.json"
VERSION_FLOORS=ROOT/"provider-version-floors.json"

def load(path:Path, default:Any)->Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def write(path:Path, value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def norm(value:Any)->str:
    return re.sub(r"[^a-z0-9._-]+","-",str(value or "").strip().casefold()).strip("-")


def canonical_catalog_scraper(row:dict[str,Any])->dict[str,Any]:
    """Store semantic capability in provider_catalog, never manifest transport aliases."""
    scraper=dict(row)
    scraper["disabledPlatforms"]=[]
    semantic=scraper.pop("canonicalSupportedTypes",None)
    if isinstance(semantic,list) and semantic:
        scraper["supportedTypes"]=list(semantic)
    return scraper


def _semver(value:Any)->tuple[int,int,int] | None:
    match=re.fullmatch(r"(\d+)\.(\d+)\.(\d+)",str(value or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def load_version_floor_payload()->dict[str,Any]:
    payload=load(VERSION_FLOORS,{"schema_version":1,"providers":{}})
    if not isinstance(payload,dict) or int(payload.get("schema_version") or 0)!=1:
        raise RuntimeError("provider version floor registry schema is invalid")
    if not isinstance(payload.get("providers"),dict):
        raise RuntimeError("provider version floor registry providers map is invalid")
    return payload


def ensure_activation_version_floor(
    provider_id:str,
    manifest_row:dict[str,Any],
    floor_payload:dict[str,Any],
)->dict[str,Any]:
    """Seed a first-exposure floor and keep activation strictly above retained history."""
    pid=norm(provider_id)
    providers=floor_payload.get("providers")
    if not isinstance(providers,dict):
        raise RuntimeError("provider version floor registry providers map is invalid")
    current_text=str(manifest_row.get("version") or "").strip()
    current=_semver(current_text)
    if current is None:
        raise RuntimeError(f"{pid}: activation provider version is not semver: {current_text!r}")
    floor_text=str(providers.get(pid) or "").strip()
    floor=_semver(floor_text) if floor_text else None
    seeded=False
    bumped=False
    if floor is None:
        floor_text="0.0.0"
        floor=(0,0,0)
        providers[pid]=floor_text
        seeded=True
    if current <= floor:
        base=max(current,floor)
        current_text=f"{base[0]}.{base[1]}.{base[2]+1}"
        manifest_row["version"]=current_text
        bumped=True
    return {
        "provider":pid,
        "floor":floor_text,
        "version":current_text,
        "seeded":seeded,
        "bumped":bumped,
    }



def proof_source_artifact_digest(trigger_sha:str, relative:str)->str:
    sha=str(trigger_sha or "").strip().casefold()
    rel=str(relative or "").strip().replace("\\","/")
    if not re.fullmatch(r"[0-9a-f]{40}",sha):
        raise RuntimeError("pending proof trigger SHA is invalid")
    if rel.startswith("../") or not rel.startswith("provider-disabled/"):
        raise RuntimeError("pending proof artifact path is unsafe")
    proc=subprocess.run(["git","show",f"{sha}:{rel}"],cwd=ROOT,capture_output=True,timeout=30,check=False)
    if proc.returncode!=0:
        raise RuntimeError("pending proof source artifact is unavailable")
    return hashlib.sha256(proc.stdout).hexdigest()


def pending_artifact_digest(path:Path)->str:
    if not path.is_file():
        raise RuntimeError(f"missing pending artifact: {path}")
    text=path.read_text(encoding="utf-8")
    result=minimize_text(text)
    validate_transform(text,result.text)
    if result.text != text:
        raise RuntimeError("pending artifact is not provider-v3 minimizer fixed-point")
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    if not source.is_file() or not base_source.is_file():
        raise RuntimeError(f"{pid}: pending provider/base artifact missing")
    expected_base=str(provenance_row.get("base_sha256") or "").strip().casefold()
    if len(expected_base)==64 and hashlib.sha256(base_source.read_bytes()).hexdigest()!=expected_base:
        raise RuntimeError(f"{pid}: pending ProviderBase hash mismatch")
    if target.exists() and source.read_bytes()!=target.read_bytes():
        raise RuntimeError(f"activation artifact collision: {target}")
    if base_target.exists() and base_source.read_bytes()!=base_target.read_bytes():
        raise RuntimeError(f"activation artifact collision: {base_target}")
    _move_exact(source,target,dry_run=dry_run)
    _move_exact(base_source,base_target,dry_run=dry_run)
    active_relative=target.relative_to(ROOT).as_posix()
    manifest_row["filename"]=active_relative
    provenance_row["published_filename"]=active_relative
    return active_relative


def portfolio_targets(policy:dict[str,Any])->tuple[int,int]:
    portfolio=policy.get("portfolio") if isinstance(policy.get("portfolio"),dict) else {}
    target_global=int(portfolio.get("target_global_active") or 60)
    target_france=int(portfolio.get("target_france_active") or 60)
    if target_global < 1 or target_france < 1:
        raise RuntimeError("provider portfolio projection targets must be positive")
    return target_global,target_france


def onboarding_priority(batch:dict[str,Any])->dict[str,tuple[int,float,str]]:
    """Return deterministic onboarding rank without granting health authority."""
    result:dict[str,tuple[int,float,str]]={}
    candidates=[]
    for key in ("providers","deferredProviders"):
        rows=batch.get(key) if isinstance(batch.get(key),list) else []
        candidates.extend(row for row in rows if isinstance(row,dict))
    for row in candidates:
        pid=norm(row.get("id"))
        if not pid:
            continue
        try:
            rank=int(row.get("inventory_rank") or row.get("inventoryRank") or 1_000_000)
        except (TypeError,ValueError):
            rank=1_000_000
        try:
            score=float(row.get("inventory_score") or row.get("inventoryScore") or 0)
        except (TypeError,ValueError):
            score=0.0
        key=(rank,-score,pid)
        previous=result.get(pid)
        if previous is None or key < previous:
            result[pid]=key
    return result


def projection_active_counts(catalog:dict[str,Any])->tuple[int,int]:
    global_count=0
    france_count=0
    for entry in catalog.get("providers") or []:
        if not isinstance(entry,dict):
            continue
        scraper=entry.get("scraper") if isinstance(entry.get("scraper"),dict) else {}
        if scraper.get("enabled") is False:
            continue
        projections=entry.get("projections") if isinstance(entry.get("projections"),dict) else {}
        if projections.get("general") is True:
            global_count+=1
        if projections.get("vf") is True:
            france_count+=1
    return global_count,france_count


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
    static_knowledge=load(STATIC_KNOWLEDGE,{"schemaVersion":1,"providers":{}})
    version_floor_payload=load_version_floor_payload()
    version_floor_updates=[]
    portfolio_policy=load(ROOT/".github/provider-portfolio-policy.json",{})
    onboarding_batch=load(ROOT/".github/provider-onboarding/batch.json",{})
    target_global,target_france=portfolio_targets(portfolio_policy)
    active_global,active_france=projection_active_counts(catalog)
    active_global_before,active_france_before=active_global,active_france
    priority=onboarding_priority(onboarding_batch)

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
        (
            norm(pid)
            for pid,row in prov_map.items()
            if isinstance(row,dict) and str(row.get("activation_mode") or "")=="bulk_onboarding_pending"
        ),
        key=lambda pid:priority.get(pid,(1_000_000,0.0,pid)),
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
        if pid not in priority:
            blocked.append({
                "provider":pid,
                "reason":"portfolio_priority_missing",
                "priorityAuthority":".github/provider-onboarding/batch.json",
            })
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
        projections=catalog_entry.get("projections") if isinstance(catalog_entry,dict) and isinstance(catalog_entry.get("projections"),dict) else {}
        wants_global=projections.get("general") is True
        wants_france=projections.get("vf") is True
        if not wants_global and not wants_france:
            blocked.append({"provider":pid,"reason":"production_projection_missing"})
            continue
        capacity_reached=[]
        if wants_global and active_global >= target_global:
            capacity_reached.append("global")
        if wants_france and active_france >= target_france:
            capacity_reached.append("france")
        if capacity_reached:
            blocked.append({
                "provider":pid,
                "reason":"portfolio_projection_capacity_reached",
                "projections":capacity_reached,
                "activeGlobal":active_global,
                "targetGlobal":target_global,
                "activeFrance":active_france,
                "targetFrance":target_france,
            })
            continue
        filename=str(manifest_row.get("filename") or "").replace("../","",1)
        pending_path=(ROOT/filename).resolve()
        try:
            pending_sha=pending_artifact_digest(pending_path)
        except Exception as exc:
            blocked.append({"provider":pid,"reason":"pending_artifact_not_fixed_point","detail":str(exc)})
            continue
        recorded_sha=str(prov.get("sha256") or "").strip().casefold()
        if len(recorded_sha)==64 and recorded_sha!=pending_sha:
            blocked.append({"provider":pid,"reason":"pending_artifact_hash_mismatch"})
            continue
        try:
            proof_sha=proof_source_artifact_digest(str(trigger_sha or ""),filename)
        except Exception as exc:
            blocked.append({"provider":pid,"reason":"pending_proof_source_unavailable","detail":str(exc)})
            continue
        if proof_sha!=pending_sha:
            blocked.append({"provider":pid,"reason":"pending_proof_source_byte_drift"})
            continue
        try:
            lego_identity=exact_provider_lego_identity_contract(pid,pending_path,patch)
        except (RuntimeError,ValueError) as exc:
            blocked.append({"provider":pid,"reason":"pending_provider_lego_identity_invalid","detail":str(exc)})
            continue
        try:
            active_relative=restore_pending_artifacts(pid,manifest_row,prov,dry_run=args.dry_run)
        except RuntimeError as exc:
            blocked.append({"provider":pid,"reason":"pending_artifact_state_invalid","detail":str(exc)})
            continue
        active_path=ROOT/active_relative
        active_sha=pending_sha if args.dry_run else hashlib.sha256(active_path.read_bytes()).hexdigest()
        if scope=="global":
            source_path=pending_path if args.dry_run else active_path
            persist_static_from_bundle(
                static_knowledge,pid,source_path,source="activation-static-config",overwrite=True,
            )
        if active_sha!=pending_sha:
            raise RuntimeError(f"{pid}: activation changed provider bytes after proof")
        if lego_identity is not None:
            patch["identity_input"]=lego_identity
        version_floor_updates.append(
            ensure_activation_version_floor(pid,manifest_row,version_floor_payload)
        )
        manifest_row["enabled"]=True
        # provider_catalog.json is the projection authority. Global activation
        # must advance its scraper copy before render-manifests-from-catalog.
        if isinstance(catalog_entry,dict):
            catalog_entry["scraper"]=canonical_catalog_scraper(manifest_row)
        manifest_overrides=patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"),dict) else {}
        manifest_overrides.pop("enabled",None)
        if manifest_overrides:
            patch["manifest_overrides"]=manifest_overrides
        else:
            patch.pop("manifest_overrides",None)
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
        if wants_global:
            active_global+=1
        if wants_france:
            active_france+=1

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
        "portfolio":{
            "targetGlobal":target_global,
            "targetFrance":target_france,
            "activeGlobalBefore":active_global_before,
            "activeFranceBefore":active_france_before,
            "activeGlobalAfter":active_global,
            "activeFranceAfter":active_france,
            "priorityAuthority":".github/provider-onboarding/batch.json inventory rank/score; health authority remains current FULL proof",
        },
        "versionFloorUpdates":version_floor_updates,
        "policy":"fresh FULL OK + all declared lanes current + no Brain check + current structured onboarding priority + ranked projection capacity; unranked/over-cap FULL stays pending",
        "dryRun":bool(args.dry_run),
    }
    if not args.dry_run and activated:
        write(MANIFEST,manifest)
        write(CATALOG,catalog)
        write(OVERRIDES,overrides)
        write(PROVENANCE,provenance)
        write(HUBS,hubs)
        write(VERSION_FLOORS,version_floor_payload)
        refresh_static_counts(static_knowledge)
        write(STATIC_KNOWLEDGE,static_knowledge)
    write(args.output,payload)
    print(
        "PROVIDER_BULK_ACTIVATION "
        f"pending={len(pending)} activated={len(activated)} blocked={len(blocked)} "
        f"dry_run={str(args.dry_run).lower()}"
    )
    return 0

if __name__=="__main__":
    raise SystemExit(main())
