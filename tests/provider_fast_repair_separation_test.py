#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_fast_repair.py"
spec = importlib.util.spec_from_file_location("provider_fast_repair", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

status = {
    "repairQueue": ["a", "b"],
    "providers": [
        {"provider": "a", "status": "ROUTE PROVEN"},
        {"provider": "b", "status": "CHAIN REACHED"},
        {"provider": "c", "status": "FULL OK"},
    ],
}
assert mod.selected_targets(status, set()) == ["a", "b"]
assert mod.selected_targets(status, {"b"}) == ["b"]
try:
    mod.selected_targets(status, {"c"})
except ValueError:
    pass
else:
    raise AssertionError("explicit non-repair provider must fail closed")

source = SCRIPT.read_text(encoding="utf-8")
for required in (
    "run_provider_brain_repair.py",
    "run_provider_retest.py",
    "acceptedProgramCompiledProviders",
    "fixedInLabProviders",
):
    assert required in source, required
for forbidden in (
    "materialize_provider_v3_all.py",
    "recover_provider_routes_from_upstreams.py",
    "merge_waf_census_transport.py",
    "provider-waf-browser-session",
):
    assert forbidden not in source, forbidden


workflow = (ROOT / ".github/workflows/provider-fast-repair.yml").read_text(encoding="utf-8")
for required in (
    "Persist current unresolved Fast Brain debt into LEARN handoff",
    "scripts/provider_repair_learn_handoff_v1.py",
    "automation/provider-repair-learn-handoff-v1.json",
    ".github/triggers/brain-learning-reconstruction",
    "budget_minutes: 20",
    "learnHandoffProviders",
    "gh workflow run brain-learning-lab.yml",
    "slot_remaining_minutes=20",
    "FIELD_PROVIDER_FAST_REPAIR_LEARN_DISPATCH",
    "Import sanitized persistent Learning and Brain LLM priors",
    "scripts/import_external_brain_llm_guidance.py",
    "NiakVIO-Brain-LLM.git",
    "NIAKVIO_BRAIN_LLM_GUIDANCE=",
    "FIELD_PROVIDER_FAST_REPAIR_EXTERNAL_LLM_GUIDANCE",
):
    assert required in workflow, required
assert "workflow_run" not in workflow

print("provider fast repair separation contract passed")
