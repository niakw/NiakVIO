#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/select_provider_repair_resume_scope.py"
WORKFLOW=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("provider_repair_resume_scope",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

status={
    "repairQueue":["a","b","c","d","new"],
    "lastRepairAttempt":{
        "runId":"10","sourceCensusRunId":"10-pre-repair","timeBudgetExhausted":True,
        "selectedProviders":["a","b","c","d"],
    },
}
report={
    "resumeRecommended":True,"sourceCensusRunId":"10-pre-repair",
    "selectedProviders":["a","b","c","d"],"processedProviders":["a","b"],
    "unvisitedProviders":["c","d"],
}
targets,reason=mod.select_resume_targets(status,report)
assert targets==["c","d"] and reason=="resume-current-unvisited",(targets,reason)

resolved={**status,"repairQueue":["a","b","d","new"]}
targets,reason=mod.select_resume_targets(resolved,report)
assert targets==["d"] and reason=="resume-current-unvisited",(targets,reason)

for bad in (
    {**report,"resumeRecommended":False},
    {**report,"sourceCensusRunId":"stale"},
    {**report,"selectedProviders":["a","b","c"]},
    {**report,"processedProviders":["a","b","c"],"unvisitedProviders":["c","d"]},
):
    targets,_=mod.select_resume_targets(status,bad)
    assert targets==[],(bad,targets)

assert "target_providers:" in WORKFLOW
assert 'TARGET_PROVIDERS: ${{ inputs.target_providers || \'\' }}' in WORKFLOW
assert "select_provider_repair_resume_scope.py" in WORKFLOW
assert '-f target_providers="$unvisited_csv"' in WORKFLOW
assert "FIELD_CANONICAL_REPAIR_RESUME_SCOPE" in WORKFLOW
assert "target_provider and target_providers are mutually exclusive" in WORKFLOW

print("Provider Repair deterministic resume scope contract passed")
