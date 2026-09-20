#!/usr/bin/env python3
"""Execute census probes for repair-plan groups, never provider-by-provider."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_PLAN=ROOT/"automation/provider-repair-batch-plan-latest.json"
AUDIT=ROOT/"scripts/audit_provider_quick_yield.py"

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{path} must contain an object")
    return value

def main()->int:
    ap=argparse.ArgumentParser(description="Run one concurrent quick-yield pass for selected repair batches")
    ap.add_argument("--plan",type=Path,default=DEFAULT_PLAN)
    ap.add_argument("--group-id",action="append",default=[])
    ap.add_argument("--repair-scope",action="append",default=[])
    ap.add_argument("--output",type=Path,default=ROOT/"automation/provider-repair-batch-run.json")
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    plan=load(args.plan)
    wanted_ids={str(v) for raw in args.group_id for v in str(raw).split(",") if str(v)}
    wanted_scopes={str(v) for raw in args.repair_scope for v in str(raw).split(",") if str(v)}
    groups=[]
    for row in plan.get("groups") or []:
        if not isinstance(row,dict): continue
        if wanted_ids and str(row.get("groupId")) not in wanted_ids: continue
        if wanted_scopes and str(row.get("repairScope")) not in wanted_scopes: continue
        groups.append(row)
    if not groups:
        raise SystemExit("no repair groups selected")
    providers=sorted({
        str(pid).strip().casefold()
        for row in groups for pid in (row.get("providers") or [])
        if str(pid).strip()
    })
    if not providers:
        raise SystemExit("selected repair groups contain no providers")
    meta={
        "schemaVersion":1,
        "sourcePlanRunId":plan.get("sourceRunId"),
        "selectedGroupIds":[str(row.get("groupId")) for row in groups],
        "providerCount":len(providers),
        "providers":providers,
        "execution":"single concurrent audit_provider_quick_yield pass",
    }
    if args.dry_run:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"PROVIDER_REPAIR_BATCH_DRY_RUN providers={len(providers)} groups={len(groups)}")
        return 0
    cmd=[
        sys.executable,str(AUDIT),
        "--scope","all",
        "--output",str(args.output),
        "--provider",",".join(providers),
    ]
    subprocess.run(cmd,cwd=ROOT,check=True)
    print(f"PROVIDER_REPAIR_BATCH_OK providers={len(providers)} groups={len(groups)} output={args.output}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
