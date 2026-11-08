#!/usr/bin/env python3
"""Real Deep import-order + adaptive-transport FORCE regression.

Witness: FORCE 42500072566 executed route_transition_graph_v50 on 4khdhub,
but the saved plan lacked forcePreferredRequested/Selected. The adaptive
planner transport shadowed the base module and omitted the request field.
No media playback is inferred by this test.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTIVE = SCRIPTS / "adaptive_runtime"
PROFILE = "route_transition_graph_v50"
KEY = "published:4khdhub"

sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "niakvio_deep_real_adaptive_brain", ADAPTIVE / "brain_repair_runtime.py"
)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)
assert brain._BASE.__file__ == str((SCRIPTS / "brain_repair_runtime.py").resolve())
assert brain.PLANS is brain._BASE.PLANS
assert brain.bind_explicit_deep_force_profile is brain._BASE.bind_explicit_deep_force_profile

candidate = {"key": KEY, "canonical_id": "4khdhub", "upstream_id": "4khdhub"}
result = {"key": KEY, "status": "no_streams", "evidence": {
    "streams_returned": 0, "streams_playable": 0,
}}
item = {"key": KEY, "candidate": brain._BASE._planner_candidate(candidate),
        "result": brain._BASE._planner_result(result),
        "state": brain._BASE._public_state(candidate, KEY)}
with patch.dict(os.environ, {
    "NUVIO_BRAIN_EXPLORATION_CHAIN": "1",
    "NUVIO_BRAIN_FORCE_PREFERRED_PROFILE": PROFILE,
}, clear=False):
    os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    brain.reset_runtime_state()
    brain.bind_explicit_deep_force_profile(PROFILE)
    os.environ.pop("NUVIO_BRAIN_FORCE_PREFERRED_PROFILE", None)
    assert brain._BASE._force_preferred_strategy("deep") == PROFILE

    # Execute actual adaptive overlay -> actual JS planner. A minimal report
    # can reject the strategy causally; it MUST record requested intent.
    base_payload = {
        "mode": "deep", "explorationChain": True,
        "forcePreferredStrategy": brain._BASE._force_preferred_strategy("deep"),
        "policy": {}, "negativeMemory": [], "historicalSolutions": [],
        "llmGuidance": [], "learnedSkills": [],
    }
    real_plans = brain._run_planner_batch(base_payload, [item])
    assert real_plans[KEY]["forcePreferredRequested"] == PROFILE, real_plans

    # Check the real path used by Deep for its first health-run planning.
    with tempfile.TemporaryDirectory(prefix="brain-force-adaptive-") as tmp:
        registry = Path(tmp) / "candidates.json"
        registry.write_text(json.dumps({"candidates": [candidate]}), encoding="utf-8")
        from_health = brain.update_plans(registry, {"results": [result]}, "deep")
        assert from_health[KEY]["forcePreferredRequested"] == PROFILE, from_health
        # The exploration parent uses a different adapter entrypoint.
        replanned = brain.replan_observation(candidate, result, plan_key=KEY, mode="deep")
        assert replanned["forcePreferredRequested"] == PROFILE, replanned

    # A fake adapter result without the requested intent must raise, not be
    # downgraded to a valid profile or a transferable negative experiment.
    def dropped_intent(*_args, **_kwargs):
        return SimpleNamespace(stdout=json.dumps({"plans": {
            KEY: {"providerId": "4khdhub", "action": "probe-targeted-repair",
                  "allowedProfiles": [PROFILE],
                  "postExhaustionStrategyProfile": PROFILE,
                  "forcePreferredRequested": "",
                  "forcePreferredSelected": False}
        }}).encode("utf-8"))
    with patch.object(brain.subprocess, "run", side_effect=dropped_intent):
        try:
            brain._run_planner_batch(base_payload, [item])
        except RuntimeError as exc:
            assert "dropped explicit FORCE strategy" in str(exc), str(exc)
        else:
            raise AssertionError("adaptive transport allowed the real 42500072566 false plan")

    try:
        brain._run_planner_batch(base_payload, [item, dict(item, key="published:other")])
    except RuntimeError as exc:
        assert "one representative" in str(exc)
    else:
        raise AssertionError("multi-provider explicit FORCE transport accepted")

    # Nested incompatible scope cannot erase forcePreferredRequested.
    for field, value in (("explorationChain", False), ("mode", "learning")):
        bad = dict(base_payload, **{field: value})
        try:
            brain._run_planner_batch(bad, [item])
        except RuntimeError:
            pass
        else:
            raise AssertionError("out-of-scope adaptive FORCE planner accepted")

brain.reset_runtime_state()
assert brain._BASE._force_preferred_strategy("deep") == ""
deep_src = (SCRIPTS / "run_adaptive_deep_repair.py").read_text(encoding="utf-8")
assert "sys.path.insert(0, str(ADAPTIVE))" in deep_src
assert "import brain_repair_runtime as brain" in deep_src

print("BRAIN_FORCE_ADAPTIVE_PLANNER_BRIDGE_OK actual_adapter=true JS_plan=true baseline=true replan=true dropped_intent_rejected=true media_not_proven=true")
