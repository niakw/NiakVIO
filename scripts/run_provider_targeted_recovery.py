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
import re
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


def merge_previous_provider_snapshot(
    previous:dict[str,Any],
    payload:dict[str,Any],
    *,
    selected_targets:set[str],
    source_census_run_id:object,
)->dict[str,Any]:
    """Retain unselected provider evidence only within the same census authority.

    Explicit targeted runs update a subset of providers. Replacing the complete
    latest snapshot with that subset silently turns every other provider into
    "not-probed" on the next refinement pass. Retain those rows only when they
    were produced for the same census run; a new census intentionally starts a
    fresh evidence epoch.
    """
    if not isinstance(previous,dict):
        return payload
    if str(previous.get("sourceCensusRunId") or "") != str(source_census_run_id or ""):
        return payload
    previous_rows=previous.get("providers")
    current_rows=payload.get("providers")
    if not isinstance(previous_rows,dict) or not isinstance(current_rows,dict):
        return payload

    retained={
        str(provider).casefold():row
        for provider,row in previous_rows.items()
        if str(provider).casefold() not in selected_targets and isinstance(row,dict)
    }
    if not retained:
        return payload

    merged=dict(retained)
    merged.update(current_rows)
    payload["providers"]={key:merged[key] for key in sorted(merged)}
    payload["retainedProviders"]=sorted(retained)
    payload["retainedProviderCount"]=len(retained)
    payload["providerEvidenceCount"]=len(merged)
    payload["verifiedProviders"]=[
        key for key,row in sorted(merged.items())
        if row.get("verifiedLanes")
    ]
    payload["verifiedProviderCount"]=len(payload["verifiedProviders"])
    payload["contradictionProviders"]=[
        key for key,row in sorted(merged.items())
        if int(row.get("contradictions") or 0)>0
    ]
    return payload


def shard_for(provider:str, count:int)->int:
    digest=hashlib.sha256(provider.encode("utf-8")).digest()
    return int.from_bytes(digest[:8],"big")%count


def compact_response_shape(value:Any)->dict[str,Any]:
    if not isinstance(value,dict):
        return {}
    kind=str(value.get("kind") or "")[:24]
    if kind not in {"json","html","javascript"}:
        return {}
    out:dict[str,Any]={"kind":kind}
    if kind=="json":
        top=str(value.get("top") or "")[:24]
        if top: out["top"]=top
        for key in ("keys","itemKeys","dataKeys","dataItemKeys","resultsKeys","resultsItemKeys","resultKeys","resultItemKeys","episodeKeys","episodeItemKeys","showsKeys","showsItemKeys","sourcesKeys","sourcesItemKeys","linksKeys","linksItemKeys"):
            rows=value.get(key)
            if isinstance(rows,list):
                out[key]=[
                    str(item)[:48] for item in rows[:16]
                    if str(item) and all(ch.isalnum() or ch in "_.:-" for ch in str(item))
                ]
        for key in ("lengthBucket","dataType","resultsType","resultType","episodeType","showsType","sourcesType","linksType"):
            if value.get(key) is not None:
                out[key]=str(value.get(key))[:24]
        return out
    for key in ("sampleBytes","forms","iframes","videos","sources","scripts","anchors","functions","fetchCalls"):
        raw=value.get(key)
        if isinstance(raw,int):
            out[key]=max(0,min(raw,65536 if key=="sampleBytes" else 99))
    for key,limit in (("classTokens",16),("idTokens",12)):
        rows=value.get(key)
        if isinstance(rows,list):
            safe=[]
            for item in rows[:limit]:
                token=str(item)[:48]
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,47}",token):
                    safe.append(token)
            if safe:
                out[key]=safe
    facts=value.get("classFacts")
    if isinstance(facts,list):
        safe_facts=[]
        allowed_signals={"movie","series","season","episode","download","4k","1080p","720p","year"}
        for row in facts[:8]:
            if not isinstance(row,dict):
                continue
            token=str(row.get("token") or "")[:48]
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,47}",token):
                continue
            tags=[
                str(tag)[:16].lower() for tag in (row.get("tags") or [])[:4]
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,15}",str(tag))
            ]
            signals=[str(sig) for sig in (row.get("signals") or [])[:9] if str(sig) in allowed_signals]
            safe_facts.append({
                "token":token,
                "count":max(0,min(int(row.get("count") or 0),12)),
                "tags":tags,
                "selfHref":max(0,min(int(row.get("selfHref") or 0),12)),
                "nestedAnchors":max(0,min(int(row.get("nestedAnchors") or 0),24)),
                "signals":signals,
            })
        if safe_facts:
            out["classFacts"]=safe_facts
    markers=value.get("markers")
    allowed={"next-data","json-ld","player","download","episode","hls-literal","mp4-literal","turnstile","embed"}
    if isinstance(markers,list):
        out["markers"]=[str(item) for item in markers[:12] if str(item) in allowed]
    return out


def compact_network_path(path:str)->str:
    parts=[]
    for segment in str(path or "/").split("/"):
        if not segment:
            continue
        lowered=segment.casefold()
        opaque=(
            len(segment)>64
            or segment.count("%")>=4
            or "%7b" in lowered
            or "%22" in lowered
            or bool(re.fullmatch(r"[A-Fa-f0-9]{24,}",segment))
            or bool(re.fullmatch(r"[A-Za-z0-9_-]{40,}",segment))
        )
        if opaque:
            parts.append("{opaque}")
        elif segment.isdigit():
            parts.append("{id}")
        else:
            parts.append(segment[:48])
        if len(parts)>=6:
            break
    return "/" + "/".join(parts) if parts else "/"


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
        path=compact_network_path(parsed.path or "/")
        key=(host,path,str(fetch.get("method") or "GET"),fetch.get("status"))
        if not host or key in seen: continue
        seen.add(key)
        compact_shape=compact_response_shape(fetch.get("response_shape"))
        out.append({
            "host":host,
            "path":path[:180],
            "method":str(fetch.get("method") or "GET")[:12],
            "status":fetch.get("status"),
            **({"shape":compact_shape} if compact_shape else {}),
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
    ap.add_argument("--provider",action="append",default=[])
    ap.add_argument("--include-environment",action="store_true")
    ap.add_argument("--run-id",default="")
    ap.add_argument("--sha",default="")
    args=ap.parse_args()
    if args.shard_count<1 or not 0<=args.shard_index<args.shard_count:
        raise SystemExit("invalid shard coordinates")

    status=load(args.status,{})
    plan=load(args.plan,{})
    previous_output=load(args.output,{})
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
    requested={str(value or "").strip().casefold().replace("_","-") for value in args.provider if str(value or "").strip()}
    if requested:
        targets &= requested
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
        safe_diagnostics=[]
        safe_prefix="FIELD_"+provider.upper().replace("-","_")+"_"
        for row in lanes:
            for line in str(row.get("stderr_tail") or "").splitlines():
                line=line.strip()
                if line.startswith(safe_prefix):
                    safe_diagnostics.append(line[:1200])
                    if len(safe_diagnostics)>=24:
                        break
            if len(safe_diagnostics)>=24:
                break
        summary[provider]={
            "verifiedLanes":verified,
            "playableLanes":playable,
            "statuses":{str(row.get("semantic_type")):row.get("status") for row in lanes},
            "debugStages":{str(row.get("semantic_type")):row.get("debug_stage") for row in lanes},
            "sampleTitles":{str(row.get("semantic_type")):row.get("sample_titles") for row in lanes},
            "probeErrors":{
                str(row.get("semantic_type")):str(row.get("probe_error") or "")[:240]
                for row in lanes if str(row.get("probe_error") or "").strip()
            },
            "network":network,
            "safeDiagnostics":safe_diagnostics,
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
        "requestedProviders":sorted(requested),
        "skippedEnvironmentProviders":skipped_environment,
        "groupResults":group_results,
        "providers":summary,
        "providerEvidenceCount":len(summary),
        "retainedProviderCount":0,
        "retainedProviders":[],
        "verifiedProviderCount":sum(1 for v in summary.values() if v["verifiedLanes"]),
        "verifiedProviders":[k for k,v in sorted(summary.items()) if v["verifiedLanes"]],
        "contradictionProviders":[k for k,v in sorted(summary.items()) if int(v["contradictions"] or 0)>0],
    }
    if requested:
        payload=merge_previous_provider_snapshot(
            previous_output,
            payload,
            selected_targets=selected_targets,
            source_census_run_id=status.get("runId"),
        )
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
