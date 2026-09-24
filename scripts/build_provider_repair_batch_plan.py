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
    # Final causal status is stronger than an older dominantIssue. A provider
    # that currently proves lookup/player depth must not regress to transport
    # merely because one lane also recorded an HTTP/network error earlier.
    if "HARNESS" in s or "CLIENT TRANSPORT GAP" in s or "WAF/ANTIBOT" in s:
        return "harness-compatibility", "compare browser/native/residential transport and route client-owned gaps away from provider mutation"
    if "CANDIDATE OK" in s:
        return "candidate-replay", "replay/rematerialize retained candidate knowledge against current bytes before new mutation"
    if "PARTIAL OK" in s:
        return "missing-lanes", "protect green lanes and batch-test only missing semantic lanes"
    if "CHAIN REACHED" in s or "chain_reached" in d:
        return "terminal-extraction", "apply/test shared terminal-player extraction profile to the whole capability family"
    if "ROUTE PROVEN" in s or "lookup_only" in d:
        return "route-to-terminal", "replay proven routes in batch and apply shared detail/player traversal profile"
    if "NETWORK BLOCKED" in s:
        return "transport", "refresh domain/upstream transport and residential/native evidence before provider-local code changes"
    # Issue-only WAF/network evidence is a fallback only when the final census
    # has no deeper semantic proof.
    if "waf_challenge" in i:
        return "harness-compatibility", "qualify browser/native/residential transport before any provider mutation"
    if "network_http_error" in i or "network_exception" in i:
        return "transport", "refresh transport authority before provider-local code changes"
    return "learning", "queue by signature for Brain learning; provider-local repair only after shared profiles fail"

def action_for_row(row:dict[str,Any], depth:str, issue:str)->tuple[str,str]:
    status=scalar(row.get("status"))
    replay=" ".join(str(value or "") for value in row.get("residentialProviderReplayEvidence") or []).casefold()
    if (
        status.upper()=="NO PROOF"
        and row.get("repairEligible") is True
        and "provider_zero_before_provider_network" in replay
    ):
        return (
            "learning",
            "residential full-provider replay disproved transport ownership; learn a provider-side request/route strategy before mutation",
        )
    return action_for(status,depth,issue)

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
        scope,action=action_for_row(row,depth,issue)
        # Normal provider failures batch broadly by repair scope + capability.
        # Harness failures are different: transport causality is already known
        # here, so browser-only/TLS divergence must never share an experiment
        # family with "challenged even through residential exit". Mixing those
        # signatures teaches contradictory client strategies.
        harness_class=scalar(row.get("harnessTransportClass"), "not-applicable")
        key=(scope,strategy,harness_class) if scope=="harness-compatibility" else (scope,strategy)
        groups[key].append({
            "provider":pid,
            "status":scalar(row.get("status")),
            "runtimeFamily":family,
            "evidenceDepth":depth,
            "issueClass":issue,
            "harnessTransportClass":scalar(row.get("harnessTransportClass"), "not-applicable"),
            "declaredLanes":row.get("declaredLanes") or [],
            "currentVerifiedLanes":row.get("currentVerifiedLanes") or [],
            "action":action,
        })
    out_groups=[]
    for key,members in groups.items():
        scope,strategy=key[:2]
        transport_signature=(key[2] if len(key)>2 else "not-applicable")
        providers=sorted(m["provider"] for m in members)
        families=sorted({scalar(m.get("runtimeFamily")) for m in members})
        depths=sorted({scalar(m.get("evidenceDepth")) for m in members})
        issues=sorted({scalar(m.get("issueClass")) for m in members})
        harness_classes=sorted({
            scalar(m.get("harnessTransportClass"))
            for m in members
            if scalar(m.get("harnessTransportClass")) != "not-applicable"
        })
        action=scalar(members[0].get("action"),"queue by signature for Brain learning")
        out_groups.append({
            "groupId":"|".join(key),
            "repairScope":scope,
            "runtimeFamilies":families,
            "capabilityStrategy":strategy,
            "evidenceDepths":depths,
            "dominantIssues":issues,
            "harnessTransportClasses":harness_classes,
            "transportSignature":transport_signature,
            "providerCount":len(providers),
            "providers":providers,
            "action":action,
            "executionPolicy":"batch-first",
            "providerLocalFallback":"only-after-shared-profile-failure",
        })
    out_groups.sort(key=lambda x:(-x["providerCount"],x["repairScope"],x["capabilityStrategy"],x.get("transportSignature",""),x["groupId"]))
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
