#!/usr/bin/env python3
"""Build an isolated exact-byte stage for lifecycle-disabled provider recovery.

The recovery queue is evidence/debt only. This script never edits manifests,
never moves provider assets, and never grants production/publication authority.
It verifies each queued asset hash before copying bytes into a disposable Lab
stage that Brain/health tooling may execute.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/"automation/provider-disabled-recovery-queue.json"
GLOBAL=ROOT/"manifest.json"
FRANCE=ROOT/"vf/manifest.json"

def load(path:Path, default:Any)->Any:
    if not path.is_file(): return default
    return json.loads(path.read_text(encoding="utf-8"))

def canon(value:Any)->str:
    return re.sub(r"[^a-z0-9._-]+","-",str(value or "").strip().casefold()).strip("-")

def manifest_rows()->dict[str,dict[str,Any]]:
    out={}
    for path in (GLOBAL,FRANCE):
        payload=load(path,{})
        for row in payload.get("scrapers") or []:
            if not isinstance(row,dict): continue
            pid=canon(row.get("id"))
            if pid and pid not in out: out[pid]=row
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--queue",type=Path,default=QUEUE)
    ap.add_argument("--stage",type=Path,default=ROOT/"staging-disabled-recovery")
    ap.add_argument("--provider",action="append",default=[])
    ap.add_argument("--max-providers",type=int,default=4)
    args=ap.parse_args()
    queue=load(args.queue,{})
    for key in ("proofAuthority","executionAuthority","publicationAuthority"):
        if queue.get(key) is not False:
            raise SystemExit(f"disabled recovery queue must keep {key}=false")
    requested={canon(x) for x in args.provider if canon(x)}
    rows=[r for r in queue.get("providers") or [] if isinstance(r,dict)]
    if requested:
        by_id={canon(r.get("provider")):r for r in rows}
        missing=sorted(requested-set(by_id))
        if missing: raise SystemExit("disabled recovery queue missing requested ids: "+",".join(missing))
        rows=[by_id[x] for x in sorted(requested)]
    else:
        rows=sorted(rows,key=lambda r:(str(r.get("family") or ""),canon(r.get("provider"))))[:max(1,args.max_providers)]
    if not rows: raise SystemExit("disabled recovery queue has no eligible providers")
    manifests=manifest_rows()
    if args.stage.exists(): shutil.rmtree(args.stage)
    (args.stage/"providers").mkdir(parents=True,exist_ok=True)
    candidates=[]
    for debt in rows:
        pid=canon(debt.get("provider"))
        if debt.get("brainLabEligible") is not True or debt.get("productionExecutionAllowed") is not False or debt.get("publicationAllowed") is not False:
            raise SystemExit(f"{pid}: recovery authority flags are unsafe")
        rel=Path(str(debt.get("asset") or ""))
        if not str(rel).replace("\\","/").startswith("provider-disabled/"):
            raise SystemExit(f"{pid}: recovery asset escaped provider-disabled")
        src=(ROOT/rel).resolve()
        src.relative_to((ROOT/"provider-disabled").resolve())
        data=src.read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        if digest!=str(debt.get("assetSha256") or "").casefold():
            raise SystemExit(f"{pid}: disabled recovery asset hash drift")
        dst=args.stage/"providers"/src.name
        dst.write_bytes(data)
        metadata=dict(manifests.get(pid) or {})
        metadata.update({
            "disabledRecovery":True,
            "disabledReason":debt.get("disabledReason"),
            "disabledFamily":debt.get("family"),
            "recoveryScopes":debt.get("scopes") or [],
            "productionExecutionAllowed":False,
            "publicationAllowed":False,
        })
        candidates.append({
            "key":f"disabled-recovery:{pid}",
            "source":"disabled-recovery-v1",
            "upstream_id":pid,
            "canonical_id":pid,
            "local_path":f"providers/{src.name}",
            "sha256":digest,
            "metadata":metadata,
            "canonical_metadata":{
                "contentLanguage":metadata.get("contentLanguage") or [],
                "formats":metadata.get("formats") or [],
                "descriptions":[metadata.get("description")] if metadata.get("description") else [],
            },
            "published_exact_bytes":False,
            "disabled_recovery_exact_bytes":True,
            "repair_allowed":True,
            "production_execution_allowed":False,
            "publication_allowed":False,
        })
    registry={
        "schema_version":1,
        "source":"disabled-provider-recovery-v1",
        "authority":"brain-disabled-recovery-lab-v1",
        "candidate_count":len(candidates),
        "excluded_count":0,
        "repair_allowed":True,
        "productionExecutionAllowed":False,
        "publicationAllowed":False,
        "proofAuthority":False,
        "candidates":candidates,
    }
    (args.stage/"candidates.json").write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FIELD_DISABLED_RECOVERY_STAGE providers="+str(len(candidates))+" ids="+",".join(x["canonical_id"] for x in candidates)+" production=false publication=false")
    return 0

if __name__=="__main__": raise SystemExit(main())
