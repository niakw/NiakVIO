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
assert set(out["selectedProviders"])=={"b","e","solo"},out
assert set(out["deferredProviders"])=={"a","c","d"},out
assert all(row["providerFilter"]==row["provider"] for row in out["cohorts"])
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
assert len(large_out["selectedProviders"])==8,large_out
assert len(large_out["deferredProviders"])==992,large_out

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
