#!/usr/bin/env python3
"""Refine coarse repair batches from observed runtime/network signatures."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"automation/provider-repair-batch-plan-latest.json"
VERDICT=ROOT/"automation/provider-targeted-regression-recovery-latest.json"
OUTPUT=ROOT/"automation/provider-repair-batch-refined-latest.json"

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{path} must contain an object")
    return value

def signature(provider:str, verdict:dict[str,Any])->dict[str,Any]:
    row=(verdict.get("providers") or {}).get(provider)
    if not isinstance(row,dict):
        return {"key":"not-probed","debugStages":[],"network":[]}
    stages=sorted({str(v or "unknown") for v in (row.get("debugStages") or {}).values()})
    observations=[]
    for lane,items in sorted((row.get("network") or {}).items()):
        for item in items or []:
            if not isinstance(item,dict): continue
            host=str(item.get("host") or "").casefold()
            status=str(item.get("status") if item.get("status") is not None else "")
            method=str(item.get("method") or "GET").upper()
            path=str(item.get("path") or "/")
            # Preserve route family, not fixture-specific ids/slugs.
            parts=[p for p in path.split("/") if p]
            shape="/"+"/".join(
                "{id}" if p.isdigit() or (len(p)>12 and any(ch.isdigit() for ch in p)) else p[:48]
                for p in parts[:4]
            )
            observations.append(f"{lane}:{method}:{host}:{status}:{shape}")
    observations=sorted(set(observations))[:24]
    key=";".join(stages)+"||"+";".join(observations)
    return {"key":key or "empty","debugStages":stages,"network":observations}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--plan",type=Path,default=PLAN)
    ap.add_argument("--verdict",type=Path,default=VERDICT)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    args=ap.parse_args()
    plan=load(args.plan); verdict=load(args.verdict)
    refined=[]
    for group in plan.get("groups") or []:
        if not isinstance(group,dict): continue
        members=[str(x).casefold() for x in (group.get("providers") or []) if str(x)]
        buckets:dict[str,list[str]]=defaultdict(list)
        details={}
        for provider in members:
            sig=signature(provider,verdict)
            buckets[sig["key"]].append(provider)
            details[sig["key"]]=sig
        for index,(key,providers) in enumerate(sorted(buckets.items(),key=lambda kv:(-len(kv[1]),kv[0]))):
            sig=details[key]
            refined.append({
                "groupId":f"{group.get('groupId')}#r{index+1}",
                "parentGroupId":group.get("groupId"),
                "repairScope":group.get("repairScope"),
                "capabilityStrategy":group.get("capabilityStrategy"),
                "transportSignature":group.get("transportSignature") or "not-applicable",
                "evidenceDepths":list(group.get("evidenceDepths") or []),
                "dominantIssues":list(group.get("dominantIssues") or []),
                "providerCount":len(providers),
                "providers":sorted(providers),
                "networkSignature":key,
                "debugStages":sig["debugStages"],
                "networkShape":sig["network"],
                "splitReason":"observed-signature-divergence" if len(buckets)>1 else "shared-signature",
                "executionPolicy":"batch-first",
            })
    refined.sort(key=lambda x:(-x["providerCount"],str(x["parentGroupId"]),str(x["groupId"])))
    payload={
        "schemaVersion":1,
        "sourceRunId":plan.get("sourceRunId"),
        "sourceTriggerSha":plan.get("sourceTriggerSha"),
        "sourcePlanRunId":plan.get("sourceRunId"),
        "sourceVerdictRunId":verdict.get("runId"),
        "providerCount":sum(x["providerCount"] for x in refined),
        "groupCount":len(refined),
        "groups":refined,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PROVIDER_REPAIR_BATCH_REFINED_OK providers={payload['providerCount']} groups={payload['groupCount']}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
