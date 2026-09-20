#!/usr/bin/env python3
"""Merge horizontally sharded targeted-recovery reports."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("shards",nargs="+",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--run-id",default="")
    ap.add_argument("--sha",default="")
    args=ap.parse_args()
    shards=[load(p) for p in args.shards]
    if not shards:
        raise SystemExit("no targeted recovery shards")

    source_ids={str(x.get("sourceCensusRunId") or "") for x in shards}
    source_ids.discard("")
    if len(source_ids)>1:
        raise SystemExit(f"mixed source census ids: {sorted(source_ids)}")

    providers={}
    skipped=set()
    group_acc:dict[str,dict[str,Any]]=defaultdict(lambda:{
        "repairScope":None,
        "providers":set(),
        "verifiedProviders":set(),
        "playableProviders":set(),
        "contradictionProviders":set(),
    })
    shard_count=max(int(x.get("shardCount") or 1) for x in shards)
    seen_indices=set()
    for shard in shards:
        idx=int(shard.get("shardIndex") or 0)
        if idx in seen_indices:
            raise SystemExit(f"duplicate shard index {idx}")
        seen_indices.add(idx)
        for pid,row in (shard.get("providers") or {}).items():
            key=str(pid).casefold()
            if key in providers:
                raise SystemExit(f"provider present in multiple shards: {key}")
            providers[key]=row
        skipped.update(str(x).casefold() for x in shard.get("skippedEnvironmentProviders") or [] if str(x))
        for row in shard.get("groupResults") or []:
            if not isinstance(row,dict) or not row.get("groupId"): continue
            gid=str(row["groupId"])
            acc=group_acc[gid]
            acc["repairScope"]=row.get("repairScope")
            for field in ("providers","verifiedProviders","playableProviders","contradictionProviders"):
                acc[field].update(str(x).casefold() for x in row.get(field) or [] if str(x))

    groups=[]
    for gid,acc in sorted(group_acc.items()):
        members=sorted(acc["providers"])
        groups.append({
            "groupId":gid,
            "repairScope":acc["repairScope"],
            "providerCount":len(members),
            "providers":members,
            "verifiedProviders":sorted(acc["verifiedProviders"]),
            "playableProviders":sorted(acc["playableProviders"]),
            "contradictionProviders":sorted(acc["contradictionProviders"]),
        })

    verified=[k for k,v in sorted(providers.items()) if v.get("verifiedLanes")]
    contradictions=[k for k,v in sorted(providers.items()) if int(v.get("contradictions") or 0)>0]
    payload={
        "schemaVersion":3,
        "runId":args.run_id or None,
        "triggerSha":args.sha or None,
        "sourceCensusRunId":next(iter(source_ids),None),
        "executionModel":"batch-plan sharded concurrent provider probes",
        "shardCount":shard_count,
        "shardsMerged":len(shards),
        "selectedProviderCount":len(providers),
        "selectedProviders":sorted(providers),
        "skippedEnvironmentProviders":sorted(skipped),
        "groupResults":groups,
        "providers":dict(sorted(providers.items())),
        "verifiedProviderCount":len(verified),
        "verifiedProviders":verified,
        "contradictionProviders":contradictions,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(
        "PROVIDER_TARGETED_RECOVERY_MERGED "
        f"shards={len(shards)} providers={len(providers)} verified={len(verified)}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
