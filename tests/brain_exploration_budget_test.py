#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "brain_budget_contract",
    SCRIPTS / "brain_repair_runtime.py",
)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

old_chain = os.environ.pop("NUVIO_BRAIN_EXPLORATION_CHAIN", None)
old_mode = os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
try:
    normal = brain._production_budget()
    assert normal["maxMutationsPerProvider"] == 2, normal
    assert normal["maxElapsedMsPerProvider"] == 45000, normal

    os.environ["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "1"
    exploration = brain._production_budget()
    assert exploration["maxMutationsPerProvider"] == 3, exploration
    assert exploration["maxElapsedMsPerProvider"] >= 180000, exploration
    assert exploration["maxGeneratedBytesPerProvider"] >= normal["maxGeneratedBytesPerProvider"], exploration

    candidate = {"key": "published:demo", "canonical_id": "demo"}
    plan = {"signature": "sig-demo", "action": "probe-targeted-repair"}
    brain.reset_runtime_state()
    state = brain._ensure_state(candidate, "published:demo")
    state["mutationCount"] = 2
    state["generatedBytes"] = 0
    state["signatureCounts"] = {}
    state["firstSeenMonotonic"] = time.monotonic() - 60
    assert brain._budget_error(candidate, "published:demo", plan) is None

    state["mutationCount"] = 3
    assert brain._budget_error(candidate, "published:demo", plan) == "brain_mutation_budget_exhausted"

    # Learning remains governed by the global Learning deadline rather than
    # production/exploration per-provider budgets.
    os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
    state["mutationCount"] = 999
    assert brain._budget_error(candidate, "published:demo", plan) is None
finally:
    if old_chain is None:
        os.environ.pop("NUVIO_BRAIN_EXPLORATION_CHAIN", None)
    else:
        os.environ["NUVIO_BRAIN_EXPLORATION_CHAIN"] = old_chain
    if old_mode is None:
        os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    else:
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = old_mode

planner = (ROOT / "engine_v2" / "scripts" / "plan-repairs.mjs").read_text(encoding="utf-8")
adaptive = (SCRIPTS / "adaptive_runtime" / "brain_repair_runtime.py").read_text(encoding="utf-8")
assert "input.explorationChain === true" in planner
# Both adaptive transports must inherit the canonical Brain context;
# duplicating explorationChain/forcePreferredStrategy caused a real FORCE
# execution with a missing preferred intent on run 42500072566.
canonical = (SCRIPTS / "brain_repair_runtime.py").read_text(encoding="utf-8")
assert 'def _planner_base_payload(' in canonical
assert canonical.count('"explorationChain": _exploration_chain_enabled()') == 1
assert adaptive.count("_BASE._planner_base_payload(") == 2, adaptive
assert '"explorationChain": _BASE._exploration_chain_enabled()' not in adaptive, adaptive

print("Brain exploration-chain budget contract passed")
