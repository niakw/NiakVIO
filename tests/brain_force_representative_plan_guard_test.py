#!/usr/bin/env python3
"""Real-run negative witness plus exact selected-profile positive control."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "representative_guard",ROOT/"scripts/brain_force_representative_plan_guard.py"
)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
actual=json.loads(
    (ROOT/"automation/provider-brain-repair-42414140056.json").read_text(encoding="utf-8")
)
RUN_ID="42414140056"
SOURCE_SHA="8b5ef622df9c558e028ba646351c0779ee3de0fd"
assert actual["sourceCensusRunId"]==RUN_ID+"-pre-repair"
assert actual["experienceMemory"]["sourceSha"]==SOURCE_SHA
assert actual["processedProviders"]==["allanime"] and actual["acceptedRepairCount"]==0
try:
    mod.verify(actual,provider="allanime",profile="terminal_transition_graph_v9")
except ValueError as exc:
    assert "not selected" in str(exc),exc
else:
    raise AssertionError("Historical wrong-profile FORCE replay became green")
positive=copy.deepcopy(actual)
plan=positive["waves"][0]["batches"][0]["brain"]["plans"]["published:allanime"]
plan["forcePreferredSelected"]=True
plan["postExhaustionStrategyProfile"]="terminal_transition_graph_v9"
plan["allowedProfiles"]=["terminal_transition_graph_v9"]
assert mod.verify(positive,provider="allanime",profile="terminal_transition_graph_v9",run_id=RUN_ID,source_sha=SOURCE_SHA)==1
for wrong in ("terminal_transition_graph_v8","unknown_v900"):
    try:
        mod.verify(positive,provider="allanime",profile=wrong)
    except ValueError:pass
    else:raise AssertionError("Nonselected strategy accepted")
for broken in (
    {**positive,"processedProviders":["allanime","4khdhub"]},
    {**positive,"schemaVersion":None},
    {**positive,"waves":[]},
):
    try:
        mod.verify(broken,provider="allanime",profile="terminal_transition_graph_v9")
    except ValueError:pass
    else:raise AssertionError("Unverified mixed/malformed FORCE report accepted")
# Copying the exact accepted-looking plan onto a stale "latest" artifact
# must fail on provenance even for the same provider and profile.
for wrong_run, wrong_sha in (
    ("42413160855", SOURCE_SHA),
    (RUN_ID, "b"*40),
    ("not-a-github-run", SOURCE_SHA),
):
    try:
        mod.verify(
            positive, provider="allanime", profile="terminal_transition_graph_v9",
            run_id=wrong_run, source_sha=wrong_sha,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("stale-run or wrong-SHA FORCE report accepted")
print("FORCE representative plan selection gate passed; playable media unproven")
