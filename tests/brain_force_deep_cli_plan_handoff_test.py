#!/usr/bin/env python3
"""Regress retained FORCE 42495157046: Deep got v50, saved plan lost intent.

The fallback must NEVER turn an unrelated strategy into a successful repair:
this checks caller intent and truthful selected=false, not media acceptance.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import brain_repair_runtime as brain

PROFILE = "route_transition_graph_v50"
KEY = "published:4khdhub"
items = [{
    "key": KEY,
    "candidate": {"canonical_id": "4khdhub", "upstream_id": "4khdhub"},
    "result": {"status": "no_streams"},
    "state": {"mutationCount": 0},
}]

def run_fake_planner(*_args, **kwargs):
    source = Path(kwargs["env"]["NUVIO_BRAIN_PLANNER_INPUT_FILE"])
    payload = json.loads(source.read_text(encoding="utf-8"))
    assert payload["forcePreferredStrategy"] == PROFILE, payload
    assert payload["explorationChain"] is True
    # The requested profile can legitimately be rejected by causal evidence.
    row = {
        "providerId": "4khdhub",
        "action": "probe-targeted-repair",
        "forcePreferredRequested": PROFILE,
        "forcePreferredSelected": False,
        "postExhaustionStrategyProfile": "route_transition_graph_v49",
        "allowedProfiles": ["route_transition_graph_v49"],
    }
    return SimpleNamespace(stdout=json.dumps({"plans": {KEY: row}}).encode())

with patch.dict(os.environ, {
    "NUVIO_BRAIN_EXPLORATION_CHAIN": "1",
    "NUVIO_BRAIN_FORCE_PREFERRED_PROFILE": PROFILE,
}, clear=False):
    os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    brain.reset_runtime_state()
    brain.bind_explicit_deep_force_profile(PROFILE)
    assert brain._force_preferred_strategy("deep") == PROFILE
    # Simulate the exact failure class: an ambient runtime stage lost the var.
    os.environ.pop("NUVIO_BRAIN_FORCE_PREFERRED_PROFILE", None)
    assert brain._force_preferred_strategy("deep") == PROFILE
    with patch.object(brain.subprocess, "run", side_effect=run_fake_planner):
        plans = brain._execute_planner(items, "deep")
    assert plans[KEY]["forcePreferredRequested"] == PROFILE
    assert plans[KEY]["forcePreferredSelected"] is False

    # The planner may never accept a report that silently erases intent.
    def wrong_planner(*_args, **kwargs):
        row = {"providerId": "4khdhub", "forcePreferredRequested": "",
               "forcePreferredSelected": False}
        return SimpleNamespace(stdout=json.dumps({"plans": {KEY: row}}).encode())
    with patch.object(brain.subprocess, "run", side_effect=wrong_planner):
        try:
            brain._execute_planner(items, "deep")
        except RuntimeError as exc:
            assert "dropped explicitly requested FORCE strategy" in str(exc)
        else:
            raise AssertionError("missing FORCE intent was not rejected")
    os.environ["NUVIO_BRAIN_FORCE_PREFERRED_PROFILE"] = "route_transition_graph_v49"
    try:
        brain._force_preferred_strategy("deep")
    except RuntimeError:
        pass
    else:
        raise AssertionError("conflicting ambient FORCE profile accepted")
    del os.environ["NUVIO_BRAIN_FORCE_PREFERRED_PROFILE"]

    try:
        brain._force_preferred_strategy("learning")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Deep FORCE preference accepted by Learning")

    os.environ["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "0"
    try:
        brain._force_preferred_strategy("deep")
    except RuntimeError:
        pass
    else:
        raise AssertionError("FORCE intent silently downgraded outside exploration")

brain.reset_runtime_state()
assert brain._force_preferred_strategy("deep") == ""

deep = (ROOT / "scripts/run_adaptive_deep_repair.py").read_text(encoding="utf-8")
assert "brain.reset_runtime_state()" in deep
assert "brain.bind_explicit_deep_force_profile(preferred)" in deep
assert deep.index("brain.reset_runtime_state()") < deep.index("brain.bind_explicit_deep_force_profile(preferred)") < deep.index("loop.main()")

# Actual JS planner separately proves that the FORCE field survives serialization.
with tempfile.TemporaryDirectory(prefix="niakvio-force-plan-") as directory:
    payload = {
        "mode": "deep",
        "explorationChain": True,
        "forcePreferredStrategy": PROFILE,
        "policy": {},
        "items": items,
        "negativeMemory": [],
        "historicalSolutions": [],
        "learnedSkills": [],
        "llmGuidance": [],
    }
    input_file = Path(directory) / "planner.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")
    child = subprocess.run(
        ["node", str(ROOT / "engine_v2/scripts/plan-repairs.mjs")],
        cwd=ROOT,
        env={**os.environ, "NUVIO_BRAIN_PLANNER_INPUT_FILE": str(input_file)},
        capture_output=True, text=True, timeout=30,
    )
    assert child.returncode == 0, child.stderr
    real = json.loads(child.stdout)["plans"][KEY]
    assert real.get("forcePreferredRequested") == PROFILE, real
    assert real.get("explorationChainEnabled") is True, real

print("BRAIN_FORCE_DEEP_CLI_HANDOFF_OK explicit_cli_bound=true env_loss_recovered=true conflicting_intent_rejected=true JS_intent_preserved=true playable_not_claimed=true")
