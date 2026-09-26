#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

runtime = load_module("causal_runtime_contract", ROOT / "scripts/adaptive_runtime/runtime_repair.py")
expected = {
    "provider_transport_gap": "provider_origin_failover_v1",
    "route_proven_gap": "proven_route_terminal_traversal_v1",
    "chain_terminal_gap": "chain_terminal_extractor_v1",
    "candidate_replay_gap": "retained_candidate_replay_v1",
    "media_extraction_gap": "player_media_extractor_v1",
}
for failure, strategy in expected.items():
    assert runtime._new_strategy_id(failure, 4) == strategy

planner = (ROOT / "engine_v2/scripts/plan-repairs.mjs").read_text(encoding="utf-8")
for status, failure in [
    ("CHAIN REACHED", "chain_terminal_gap"),
    ("ROUTE PROVEN", "route_proven_gap"),
    ("CANDIDATE OK", "candidate_replay_gap"),
    ("PROVIDER NETWORK BLOCKED", "provider_transport_gap"),
]:
    pos = planner.index(f'if (status === "{status}")')
    assert failure in planner[pos:pos+650]

policy = json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))
negative = policy["production"]["negativeExperimentMemory"]
assert int(negative["maxVariantsPerSignature"]) >= 5
assert int(negative["rotateExperimentAfterFailures"]) >= 1

runner = (ROOT / "scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
assert '"directSkillApplication": False' in runner
assert '"experienceMemoryRole": "prior-only-no-acceptance-authority"' in runner
assert "deferredLearningProviders" in runner

workflow = (ROOT / ".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
assert "FIELD_PROVIDER_BRAIN_LEARNING_DEBT" in workflow
assert "learning_dispatch=false owner=scheduled-learning-slot" in workflow
assert "gh workflow run brain-learning-lab.yml" not in workflow[workflow.index("- name: Persist Repair census state"):]
assert "FIELD_PROVIDER_BRAIN_FORCE_DEBT" in workflow
assert "resume_mode=force" in workflow

print("causal Brain intelligence contract passed")
