#!/usr/bin/env python3
"""Compile the causal census/batch plan into machine-owned execution lanes.

This is the control-plane router above individual repair scripts. It does not
mutate providers or dispatch workflows itself. It decides which subsystem owns
each unresolved causal class and records the safe fallback if that lane fails.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/"automation/provider-repair-batch-plan-latest.json"
STATUS=ROOT/"automation/provider-census-status.json"
OUTPUT=ROOT/"automation/provider-execution-plan-latest.json"


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(f"{path} must contain an object")
    return value


def lane_for(group:dict[str,Any])->dict[str,Any]:
    scope=str(group.get("repairScope") or "learning")
    transport=str(group.get("transportSignature") or "not-applicable")

    if scope=="candidate-replay":
        return {
            "owner":"PROVIDER_BYTES",
            "lane":"REMAT_TEST",
            "workflow":"provider-remat-test.yml",
            "dispatchAllowed":True,
            "mutatesProduction":False,
            "fallbackLane":"FAST_REPAIR",
            "decision":"prove whether current structured DATA already rebuilds a better candidate before inventing new repair",
        }
    if scope in {"route-to-terminal","terminal-extraction","missing-lanes"}:
        return {
            "owner":"PROVIDER_REPAIR",
            "lane":"FAST_REPAIR",
            "workflow":"provider-fast-repair.yml",
            "dispatchAllowed":True,
            "mutatesProduction":"validated-candidate-only",
            "fallbackLane":"BRAIN_LEARNING",
            "decision":"repair only at/after the deepest current semantic proof",
        }
    if scope=="transport":
        return {
            "owner":"DOMAIN_TRANSPORT",
            "lane":"DOMAIN_REFRESH",
            "workflow":"domain-refresh.yml",
            "dispatchAllowed":True,
            "mutatesProduction":"validated-domain-transaction-only",
            "fallbackLane":"WAF_TRANSPORT",
            "decision":"refresh provider-owned domain/transport authority before provider mutation",
        }
    if scope=="harness-compatibility":
        strategy={
            "browser-profile-only":"browser_session_transport_bridge_v1",
            "browser-profile-only-both-networks":"native_tls_browser_differential_v1",
            "residential-exit-all-challenged":"persistent_challenge_session_boundary_v1",
        }.get(transport,"harness_transport_differential_v1")
        return {
            "owner":"CORE_CLIENT_TRANSPORT",
            "lane":"CORE_CLIENT_LEARNING",
            "workflow":None,
            "dispatchAllowed":False,
            "mutatesProduction":False,
            "fallbackLane":None,
            "strategyBlueprint":strategy,
            "decision":"client/harness causal gap: learn/propose Core-client transport architecture; never hide it with provider JS mutation",
            "blocker":"architecture proposal exists but no autonomous validated Core/client application lane yet",
        }
    return {
        "owner":"BRAIN_LEARNING",
        "lane":"BRAIN_LEARNING",
        "workflow":"brain-learning-lab.yml",
        "dispatchAllowed":True,
        "mutatesProduction":False,
        "fallbackLane":None,
        "decision":"no safe deterministic repair lane remains; learn a new bounded strategy",
    }


def build(batch:dict[str,Any],status:dict[str,Any])->dict[str,Any]:
    current_repair={str(x).strip().casefold() for x in status.get("repairQueue") or [] if str(x).strip()}
    current_environment={str(x).strip().casefold() for x in status.get("environmentQueue") or [] if str(x).strip()}
    executions=[]
    provider_owner:dict[str,str]={}
    for group in batch.get("groups") or []:
        if not isinstance(group,dict):
            continue
        providers=sorted({
            str(x).strip().casefold()
            for x in group.get("providers") or []
            if str(x).strip()
        })
        if not providers:
            continue
        route=lane_for(group)
        row={
            "groupId":str(group.get("groupId") or ""),
            "repairScope":str(group.get("repairScope") or ""),
            "providers":providers,
            "providerCount":len(providers),
            "capabilityStrategy":str(group.get("capabilityStrategy") or ""),
            "transportSignature":str(group.get("transportSignature") or "not-applicable"),
            **route,
        }
        # Fail closed if a provider appears in a lane inconsistent with the
        # canonical queues. Harness is environment-owned; provider mutation
        # lanes require current repair eligibility.
        if row["lane"]=="CORE_CLIENT_LEARNING":
            unexpected=[p for p in providers if p not in current_environment]
        else:
            unexpected=[p for p in providers if p not in current_repair]
        row["queueConsistent"]=not unexpected
        row["queueMismatchProviders"]=unexpected
        if unexpected:
            row["dispatchAllowed"]=False
            row["blocker"]="batch/census queue mismatch; rebuild Retest before dispatch"
        for provider in providers:
            existing=provider_owner.get(provider)
            if existing and existing!=row["lane"]:
                raise ValueError(f"{provider}: multiple causal owners {existing} / {row['lane']}")
            provider_owner[provider]=row["lane"]
        executions.append(row)

    priority={
        "DOMAIN_REFRESH":0,
        "REMAT_TEST":1,
        "FAST_REPAIR":2,
        "CORE_CLIENT_LEARNING":3,
        "BRAIN_LEARNING":4,
    }
    executions.sort(key=lambda row:(priority.get(str(row.get("lane")),99),str(row.get("groupId"))))
    executable=[row for row in executions if row.get("dispatchAllowed") is True]
    blocked=[row for row in executions if row.get("dispatchAllowed") is not True]
    return {
        "schemaVersion":1,
        "sourceCensusRunId":status.get("runId"),
        "sourceCensusSha":status.get("triggerSha"),
        "sourceBatchRunId":batch.get("sourceRunId"),
        "executionModel":{
            "controlPlane":"causal-owner-router",
            "rule":"deepest-current-proof-owns-lane",
            "providerMutation":"only-provider-repair-lane-after-current-proof",
            "memory":"prior-only; current census remains authority",
            "automaticCoreMutation":False,
        },
        "providerCount":len(provider_owner),
        "executionCount":len(executions),
        "dispatchableExecutionCount":len(executable),
        "blockedExecutionCount":len(blocked),
        "providersByLane":{
            lane:sorted(p for p,owner in provider_owner.items() if owner==lane)
            for lane in sorted(set(provider_owner.values()))
        },
        "executions":executions,
        "blockedExecutions":[row["groupId"] for row in blocked],
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--batch-plan",type=Path,default=BATCH)
    ap.add_argument("--status",type=Path,default=STATUS)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    args=ap.parse_args()
    payload=build(load(args.batch_plan),load(args.status))
    output=args.output if args.output.is_absolute() else ROOT/args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "FIELD_PROVIDER_EXECUTION_PLAN "
        f"providers={payload['providerCount']} executions={payload['executionCount']} "
        f"dispatchable={payload['dispatchableExecutionCount']} blocked={payload['blockedExecutionCount']}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
