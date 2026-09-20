#!/usr/bin/env python3
"""Stage many providers atomically as disabled/pending NiakVIO entries.

This is the high-volume onboarding path. It intentionally performs no per-provider
network discovery, branding fetch, native client Lab, or activation. Those steps
belong to the sharded census / batch-repair / proof-driven activation pipeline.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import add_provider
import provider_base_store

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


def preflight(rows:list[dict[str,Any]], allow_replace_existing:bool)->dict[str,Any]:
    manifest=add_provider.load_json(add_provider.MANIFEST,{})
    existing={
        add_provider.norm_id(row.get("id"))
        for row in manifest.get("scrapers") or []
        if isinstance(row,dict) and str(row.get("id") or "").strip()
    }
    replacing=[]
    new=[]
    strategies=Counter()
    type_counts=Counter()
    for row in rows:
        pid=str(row["id"])
        replace=add_provider.bool_value(row.get("replace_existing"),False)
        if replace and not allow_replace_existing:
            raise ValueError(f"{pid}: replace_existing requires --allow-replace-existing in bulk mode")
        if pid in existing and not replace:
            raise ValueError(f"{pid}: provider already exists; bulk import refuses silent overwrite")
        (replacing if pid in existing else new).append(pid)
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
    }


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
            staged.append({
                "id":normalized["id"],
                "name":normalized["name"],
                "types":normalized["types"],
                "strategy":normalized["strategy"],
                "site":normalized.get("site") or None,
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
