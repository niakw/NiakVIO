#!/usr/bin/env python3
"""Run current-byte targeted recovery probes from the repair batch plan.

The runner is horizontally shardable. It selects unresolved code-repair providers
from the current batch plan, excludes pure environment/WAF groups by default,
then executes the existing adaptive quick-yield engine concurrently.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import audit_provider_quick_yield as audit

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"automation/provider-census-status.json"
PLAN=ROOT/"automation/provider-repair-batch-plan-latest.json"
HISTORY=ROOT/"automation/provider-census-proof-history.json"
OUTPUT=ROOT/"automation/provider-targeted-regression-recovery-latest.json"


def load(path:Path, default:Any)->Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def shard_for(provider:str, count:int)->int:
    digest=hashlib.sha256(provider.encode("utf-8")).digest()
    return int.from_bytes(digest[:8],"big")%count


def compact_network(row:dict[str,Any])->list[dict[str,Any]]:
    out=[]; seen=set()
    for fetch in row.get("debug_fetches") or []:
        if not isinstance(fetch,dict): continue
        raw=str(fetch.get("response_url") or fetch.get("url") or "")
        try:
            parsed=urlparse(raw)
        except Exception:
            continue
        host=(parsed.hostname or "").casefold()
        path=parsed.path or "/"
        key=(host,path,str(fetch.get("method") or "GET"),fetch.get("status"))
        if not host or key in seen: continue
        seen.add(key)
        out.append({
            "host":host,
            "path":path[:180],
            "method":str(fetch.get("method") or "GET")[:12],
            "status":fetch.get("status"),
        })
        if len(out)>=16: break
    return out


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--status",type=Path,default=STATUS)
    ap.add_argument("--plan",type=Path,default=PLAN)
    ap.add_argument("--history",type=Path,default=HISTORY)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    ap.add_argument("--shard-count",type=int,default=1)
    ap.add_argument("--shard-index",type=int,default=0)
    ap.add_argument("--max-workers",type=int,default=20)
    ap.add_argument("--include-environment",action="store_true")
    ap.add_argument("--run-id",default="")
    ap.add_argument("--sha",default="")
    args=ap.parse_args()
    if args.shard_count<1 or not 0<=args.shard_index<args.shard_count:
        raise SystemExit("invalid shard coordinates")

    status=load(args.status,{})
    plan=load(args.plan,{})
    unresolved={
        str(row.get("provider") or "").strip().casefold()
        for row in status.get("providers") or []
        if isinstance(row,dict)
        and str(row.get("status") or "") not in {"FULL OK","PARTIAL OK"}
        and str(row.get("provider") or "").strip()
    }
    plan_current=str(plan.get("sourceRunId") or "")==str(status.get("runId") or "")
    groups=[
        row for row in plan.get("groups") or []
        if isinstance(row,dict)
        and (args.include_environment or str(row.get("repairScope") or "")!="environment")
    ] if plan_current else []
    planned={
        str(pid).strip().casefold()
        for group in groups for pid in group.get("providers") or []
        if str(pid).strip()
    }
    targets=(planned if groups else unresolved)&unresolved
    skipped_environment=sorted(unresolved-targets) if groups else []
    selected_targets={
        pid for pid in targets if shard_for(pid,args.shard_count)==args.shard_index
    }

    history=load(args.history,{})
    tasks,_=audit.build_tasks(selected_targets,history=history) if selected_targets else ([],0)
    observed={str(task.get("provider_id") or "").casefold() for task in tasks}
    if observed!=selected_targets:
        raise SystemExit(
            f"target/task mismatch missing={sorted(selected_targets-observed)} "
            f"unexpected={sorted(observed-selected_targets)}"
        )
    rows=[]
    if tasks:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(1,args.max_workers),len(tasks))) as pool:
            futures=[pool.submit(audit.run,task) for task in tasks]
            for future in concurrent.futures.as_completed(futures):
                rows.append(future.result())

    by:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows:
        by[str(row.get("provider_id") or "").casefold()].append(row)
    summary={}
    for provider in sorted(selected_targets):
        lanes=by[provider]
        verified=sorted({
            str(row.get("semantic_type"))
            for row in lanes
            if int(row.get("verified") or 0)>0 and int(row.get("contradictions") or 0)==0
        })
        playable=sorted({
            str(row.get("semantic_type"))
            for row in lanes
            if int(row.get("playable") or 0)>0 and int(row.get("contradictions") or 0)==0
        })
        network={}
        for row in lanes:
            network[str(row.get("semantic_type"))]=compact_network(row)
        summary[provider]={
            "verifiedLanes":verified,
            "playableLanes":playable,
            "statuses":{str(row.get("semantic_type")):row.get("status") for row in lanes},
            "debugStages":{str(row.get("semantic_type")):row.get("debug_stage") for row in lanes},
            "sampleTitles":{str(row.get("semantic_type")):row.get("sample_titles") for row in lanes},
            "network":network,
            "contradictions":sum(int(row.get("contradictions") or 0) for row in lanes),
        }

    group_results=[]
    for group in groups:
        members=sorted(
            set(str(x).strip().casefold() for x in group.get("providers") or [] if str(x).strip())
            & selected_targets
        )
        if not members: continue
        group_results.append({
            "groupId":group.get("groupId"),
            "repairScope":group.get("repairScope"),
            "providerCount":len(members),
            "providers":members,
            "verifiedProviders":[p for p in members if summary.get(p,{}).get("verifiedLanes")],
            "playableProviders":[p for p in members if summary.get(p,{}).get("playableLanes")],
            "contradictionProviders":[p for p in members if int(summary.get(p,{}).get("contradictions") or 0)>0],
        })

    payload={
        "schemaVersion":3,
        "runId":args.run_id or None,
        "triggerSha":args.sha or None,
        "sourceCensusRunId":status.get("runId"),
        "executionModel":"batch-plan concurrent provider probes",
        "shardCount":args.shard_count,
        "shardIndex":args.shard_index,
        "maxWorkers":min(max(1,args.max_workers),20),
        "selectedProviderCount":len(selected_targets),
        "selectedProviders":sorted(selected_targets),
        "skippedEnvironmentProviders":skipped_environment,
        "groupResults":group_results,
        "providers":summary,
        "verifiedProviderCount":sum(1 for v in summary.values() if v["verifiedLanes"]),
        "verifiedProviders":[k for k,v in sorted(summary.items()) if v["verifiedLanes"]],
        "contradictionProviders":[k for k,v in sorted(summary.items()) if int(v["contradictions"] or 0)>0],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(
        "PROVIDER_TARGETED_RECOVERY "
        f"shard={args.shard_index}/{args.shard_count} providers={len(selected_targets)} "
        f"verified={payload['verifiedProviderCount']}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
