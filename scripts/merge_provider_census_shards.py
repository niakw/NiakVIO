#!/usr/bin/env python3
"""Merge deterministic quick-yield census shards into the canonical report shape."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPRESENTATIVE=("movie","tv","anime")

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{path} must contain an object")
    return value

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("inputs",nargs="+",type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    reports=[load(path) for path in args.inputs]
    rows=[]
    seen=set()
    shard_meta=[]
    selected=set()
    selected_known=True
    for path,report in zip(args.inputs,reports):
        shard_meta.append({
            "file":path.name,
            "shardCount":report.get("shard_count"),
            "shardIndex":report.get("shard_index"),
            "providerCount":report.get("provider_count"),
        })
        raw_selected=report.get("selected_providers")
        if isinstance(raw_selected,list): selected.update(str(x).casefold() for x in raw_selected)
        else: selected_known=False
        for row in report.get("rows") or []:
            if not isinstance(row,dict): continue
            key=(str(row.get("provider_id") or "").casefold(),str(row.get("semantic_type") or ""))
            if key in seen:
                raise ValueError(f"duplicate provider/lane across shards: {key}")
            seen.add(key); rows.append(row)
    by_provider:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows: by_provider[str(row.get("provider_id") or "")].append(row)
    raw_providers=sorted(p for p,v in by_provider.items() if any(int(x.get("raw") or 0)>0 for x in v))
    playable=sorted(p for p,v in by_provider.items() if any(int(x.get("playable") or 0)>0 for x in v))
    accepted=sorted(p for p,v in by_provider.items() if any(int(x.get("playable") or 0)>0 and int(x.get("contradictions") or 0)==0 for x in v))
    verified=sorted(p for p,v in by_provider.items() if any(int(x.get("verified") or 0)>0 for x in v))
    wrong=sorted(p for p,v in by_provider.items() if any(str(x.get("status") or "")=="wrong_content" for x in v))
    statuses=Counter(str(x.get("status") or "unknown") for x in rows)
    stages=Counter(str(x.get("debug_stage") or "unknown") for x in rows)
    stage_providers:dict[str,set[str]]=defaultdict(set)
    for row in rows:
        if row.get("provider_id"): stage_providers[str(row.get("debug_stage") or "unknown")].add(str(row["provider_id"]))
    type_summary={}
    for media in REPRESENTATIVE:
        subset=[x for x in rows if x.get("semantic_type")==media]
        type_summary[media]={
            "tasks":len(subset),
            "raw":sum(int(x.get("raw") or 0)>0 for x in subset),
            "playable":sum(int(x.get("playable") or 0)>0 for x in subset),
            "accepted_playable":sum(int(x.get("playable") or 0)>0 and int(x.get("contradictions") or 0)==0 for x in subset),
            "verified":sum(int(x.get("verified") or 0)>0 for x in subset),
            "wrong_content":sum(int(x.get("contradictions") or 0)>0 for x in subset),
        }
    payload={
        "schema_version":6,
        "requested_scope":"sharded",
        "resolved_scope":"merged-shards",
        "selected_providers":sorted(selected) if selected_known else None,
        "environment":reports[0].get("environment") if reports else "",
        "fixture_selection_policy":reports[0].get("fixture_selection_policy") if reports else "",
        "provider_count":len(by_provider),
        "task_count":len(rows),
        "probe_count":sum(int(x.get("sample_count") or 1) for x in rows),
        "rotated_task_count":sum(1 for x in rows if x.get("adaptive_rotated") is True),
        "max_samples_per_lane":max((int(r.get("max_samples_per_lane") or 0) for r in reports),default=0),
        "raw_provider_count":len(raw_providers),
        "playable_provider_count":len(playable),
        "accepted_playable_provider_count":len(accepted),
        "verified_provider_count":len(verified),
        "wrong_content_provider_count":len(wrong),
        "raw_providers":raw_providers,
        "playable_providers":playable,
        "accepted_playable_providers":accepted,
        "verified_providers":verified,
        "wrong_content_providers":wrong,
        "type_summary":type_summary,
        "status_counts":dict(sorted(statuses.items())),
        "debug_stage_counts":dict(sorted(stages.items())),
        "debug_stage_providers":{k:sorted(v) for k,v in sorted(stage_providers.items())},
        "shards":shard_meta,
        "rows":sorted(rows,key=lambda x:(str(x.get("provider_id") or ""),str(x.get("semantic_type") or ""))),
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PROVIDER_CENSUS_SHARD_MERGE_OK shards={len(reports)} providers={payload['provider_count']} tasks={payload['task_count']}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
