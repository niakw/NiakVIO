#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"plan_learning_family_dispatch.py"
spec=importlib.util.spec_from_file_location("learning_family_dispatch",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

providers=["a","b","c","d","e","solo"]
status={
    "runId":"r1",
    "providers":[
        {"provider":"a","status":"NO PROOF","evidenceDepth":["movie=lookup_only"]},
        {"provider":"b","status":"REGRESSION PROVIDER","evidenceDepth":["movie=chain_reached"]},
        {"provider":"c","status":"CHAIN REACHED","evidenceDepth":["movie=chain_reached"]},
        {"provider":"d","status":"NO PROOF","evidenceDepth":["tv=none"]},
        {"provider":"e","status":"CANDIDATE OK","evidenceDepth":["anime=lookup_only"]},
        {"provider":"solo","status":"NO PROOF","evidenceDepth":["anime=lookup_only"]},
    ],
}
plan={
    "sourceRunId":"r1",
    "groups":[
        {
            "groupId":"terminal-extraction|mixed|runtime:mixed",
            "repairScope":"terminal-extraction",
            "capabilityStrategy":"mixed_embed_resolver",
            "runtimeFamilySignature":"mixed_embed_resolver",
            "providers":["a","b","c"],
        },
        {
            "groupId":"learning|mixed|runtime:mixed",
            "repairScope":"learning",
            "capabilityStrategy":"mixed_embed_resolver",
            "runtimeFamilySignature":"mixed_embed_resolver",
            "providers":["d","e"],
        },
    ],
}
out=mod.plan(providers,plan,status,max_cohorts=8)
assert out["batchPlanCurrent"] is True,out
assert out["familyCount"]==3,out
assert out["cohortCount"]==3,out
assert set(out["selectedProviders"])=={"a","b","c","d","e","solo"},out
assert out["deferredProviders"]==[],out
assert all(row["providerFilter"].split(",")[0]==row["provider"] for row in out["cohorts"])
assert all(row["cohortProviderCount"]==len(row["cohortProviders"]) for row in out["cohorts"])
assert all(row["cohortProviderCount"]<=8 for row in out["cohorts"])
assert sum(row["cohortProviderCount"] for row in out["cohorts"])==6,out
assert out["safety"]["providerMutationAuthority"] is False
assert out["safety"]["publicationAuthority"] is False

# Bounded dispatch: even 1000 already-causally-eligible providers in 20
# independent families dispatch at most 8 family oracles in one Fast handoff.
large=[f"p{i:04d}" for i in range(1000)]
large_status={
    "runId":"scale",
    "providers":[
        {"provider":p,"status":"CHAIN REACHED","evidenceDepth":["movie=chain_reached"]}
        for p in large
    ],
}
large_plan={"sourceRunId":"scale","groups":[]}
for family in range(20):
    members=large[family*50:(family+1)*50]
    large_plan["groups"].append({
        "groupId":f"family-{family:02d}",
        "repairScope":"terminal-extraction",
        "capabilityStrategy":"mixed_embed_resolver",
        "runtimeFamilySignature":"mixed_embed_resolver",
        "providers":members,
    })
large_out=mod.plan(large,large_plan,large_status,max_cohorts=8)
assert large_out["familyCount"]==20,large_out
assert large_out["cohortCount"]==8,large_out
assert len(large_out["selectedProviders"])==64,large_out
assert len(large_out["deferredProviders"])==936,large_out
assert all(row["cohortProviderCount"]==8 for row in large_out["cohorts"]),large_out

# A later wave must not starve untouched families. Mark the first wave's eight
# oracles as recently executed in durable Learning memory: families 08..15 must
# now outrank families 00..07 even though those earlier families contain
# untested siblings. Family recency, not just member recency, owns wave fairness.
recent_memory={
    "experimentMemory":{
        "entries":[
            {
                "providerId": provider,
                "lastSeenAt": f"2026-11-28T{2 + index // 60:02d}:{index % 60:02d}:00+00:00",
            }
            for index,provider in enumerate(large_out["selectedProviders"])
        ]
    }
}
second_wave=mod.plan(
    large,
    large_plan,
    large_status,
    max_cohorts=8,
    learning_memory=recent_memory,
)
second_families={row["familyKey"] for row in second_wave["cohorts"]}
assert second_families=={f"family-{family:02d}" for family in range(8,16)},second_wave
assert second_wave["learningMemoryUsed"] is True,second_wave
assert second_wave["selectionPolicy"].startswith("least-recent-family"),second_wave

# When an already-visited family cycles back, rotate its representative instead
# of replaying the same provider forever.
all_families=mod.plan(
    large,
    large_plan,
    large_status,
    max_cohorts=16,
    learning_memory=recent_memory,
)
family0=next(row for row in all_families["cohorts"] if row["familyKey"]=="family-00")
assert family0["provider"]=="p0008",family0
assert family0["providerFilter"].split(",")[0]=="p0008",family0
assert len(family0["cohortProviders"])==8,family0
assert family0["providerLastAttemptAt"]=="",family0
assert family0["familyLastAttemptAt"],family0

# Stale family plan has no grouping authority: each provider becomes its own
# isolated cohort instead of inheriting an obsolete sibling relationship.
stale=mod.plan(
    ["a","b"],
    {**plan,"sourceRunId":"old"},
    status,
    max_cohorts=8,
)
assert stale["batchPlanCurrent"] is False,stale
assert stale["familyCount"]==2,stale
assert set(stale["selectedProviders"])=={"a","b"},stale

print("Brain Learning bounded family-dispatch planner contract passed")
