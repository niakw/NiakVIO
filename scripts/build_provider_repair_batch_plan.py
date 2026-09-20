#!/usr/bin/env python3
"""Build a scalable repair queue grouped by failure signature and provider family."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"automation/provider-census-status.json"
OVERRIDES=ROOT/"provider-overrides.json"
OUTPUT=ROOT/"automation/provider-repair-batch-plan.json"

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{path} must contain an object")
    return value

def scalar(value:Any, default:str="unknown")->str:
    text=str(value or "").strip()
    return text or default

def action_for(status:str, depth:str, issue:str)->tuple[str,str]:
    s=status.upper(); d=depth.lower(); i=issue.lower()
    if "HARNESS" in s or "WAF/ANTIBOT" in s or "waf_challenge" in i:
        return "harness-compatibility", "compare GitHub Node/Chromium transport with representative TV/mobile client; never mutate provider code solely to hide a CI challenge"
    if "NETWORK BLOCKED" in s or "network_http_error" in i or "network_exception" in i:
        return "transport", "domain/upstream transport refresh across the whole capability family before provider-local code changes"
    if "CANDIDATE OK" in s:
        return "candidate-replay", "replay retained candidate proofs against current bytes in batch"
    if "PARTIAL OK" in s:
        return "missing-lanes", "protect green lanes and batch-test only missing semantic lanes"
    if "CHAIN REACHED" in s or "chain_reached" in d:
        return "terminal-extraction", "apply/test shared terminal-player extraction profile to the whole capability family"
    if "ROUTE PROVEN" in s or "lookup_only" in d:
        return "route-to-terminal", "replay proven routes in batch and apply shared detail/player traversal profile"
    return "learning", "queue by signature for Brain learning; provider-local repair only after shared profiles fail"

def depth_class(values:list[str])->str:
    lowered={str(v).split("=",1)[-1].strip().lower() for v in values if str(v).strip()}
    if "chain_reached" in lowered: return "chain"
    if "lookup_only" in lowered: return "lookup"
    if lowered-{ "none" }: return "other"
    return "none"

def issue_class(value:str)->str:
    text=value.lower().split("×",1)[0].strip()
    if "waf_challenge" in text: return "waf_challenge"
    if "network_http_error" in text: return "network_http_error"
    if "network_exception" in text: return "network_exception"
    if "network_zero_result" in text: return "network_zero_result"
    return text or "unknown"

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--status",type=Path,default=STATUS)
    ap.add_argument("--overrides",type=Path,default=OVERRIDES)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    args=ap.parse_args()
    status=load(args.status); overrides=load(args.overrides)
    patches=overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"),dict) else {}
    caps=overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"),dict) else {}
    groups:dict[tuple[str,...],list[dict[str,Any]]]=defaultdict(list)
    rows=status.get("providers") if isinstance(status.get("providers"),list) else []
    for row in rows:
        if not isinstance(row,dict) or not row.get("brainCheckRequired"): continue
        pid=scalar(row.get("provider"),"").casefold()
        if not pid: continue
        patch=patches.get(pid) if isinstance(patches.get(pid),dict) else {}
        cap=caps.get(pid) if isinstance(caps.get(pid),dict) else {}
        family=scalar(patch.get("source_runtime_family") or patch.get("runtime_family") or patch.get("capability") or cap.get("strategy"))
        strategy=scalar(cap.get("strategy") or patch.get("capability"))
        depth=depth_class(list(row.get("evidenceDepth") or []))
        issue=issue_class(scalar(row.get("dominantIssue")))
        scope,action=action_for(scalar(row.get("status")),depth,issue)
        # First-pass batch identity is deliberately broad: repair scope +
        # capability strategy only. Evidence depth, issue class and exact runtime
        # families remain metadata. The post-probe refiner is responsible for
        # splitting a broad hypothesis when observed network/runtime signatures
        # actually diverge.
        key=(scope,strategy)
        groups[key].append({
            "provider":pid,
            "status":scalar(row.get("status")),
            "runtimeFamily":family,
            "evidenceDepth":depth,
            "issueClass":issue,
            "declaredLanes":row.get("declaredLanes") or [],
            "currentVerifiedLanes":row.get("currentVerifiedLanes") or [],
        })
    out_groups=[]
    for key,members in groups.items():
        scope,strategy=key
        providers=sorted(m["provider"] for m in members)
        families=sorted({scalar(m.get("runtimeFamily")) for m in members})
        depths=sorted({scalar(m.get("evidenceDepth")) for m in members})
        issues=sorted({scalar(m.get("issueClass")) for m in members})
        _,action=action_for(
            members[0]["status"],
            depths[0] if len(depths)==1 else "mixed",
            issues[0] if len(issues)==1 else "mixed",
        )
        out_groups.append({
            "groupId":"|".join(key),
            "repairScope":scope,
            "runtimeFamilies":families,
            "capabilityStrategy":strategy,
            "evidenceDepths":depths,
            "dominantIssues":issues,
            "providerCount":len(providers),
            "providers":providers,
            "action":action,
            "executionPolicy":"batch-first",
            "providerLocalFallback":"only-after-shared-profile-failure",
        })
    out_groups.sort(key=lambda x:(-x["providerCount"],x["repairScope"],x["capabilityStrategy"],x["groupId"]))
    payload={
        "schemaVersion":1,
        "sourceRunId":status.get("runId"),
        "sourceTriggerSha":status.get("triggerSha"),
        "unresolvedProviderCount":sum(x["providerCount"] for x in out_groups),
        "groupCount":len(out_groups),
        "executionModel":{
            "default":"family/signature batch",
            "liveProbeConcurrency":"audit_provider_quick_yield ThreadPool",
            "fixturePolicy":"adaptive rotating corpus per lane",
            "providerLocalRepair":"exception path only",
        },
        "groups":out_groups,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PROVIDER_REPAIR_BATCH_PLAN_OK providers={payload['unresolvedProviderCount']} groups={payload['groupCount']}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
