#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_brain_learning_sandbox.py"
spec = importlib.util.spec_from_file_location("brain_learning_unexecuted_evolved", SCRIPT)
assert spec and spec.loader
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)

state = {
    "experimentMemory": {
        "entries": [
            {
                "providerId": "demo",
                "signature": "sig",
                "profile": "terminal_transition_graph_v1",
                "successes": 0,
                "failures": 1,
                "consecutiveFailures": 1,
                "lastOutcome": "profile_unavailable",
                "executionObserved": False,
            },
            {
                "providerId": "demo",
                "signature": "sig",
                "profile": "terminal_request_program_inference_v1",
                "successes": 0,
                "failures": 1,
                "consecutiveFailures": 1,
                "lastOutcome": "profile_unavailable",
                "executionObserved": True,
            },
            {
                "providerId": "demo",
                "signature": "sig",
                "profile": "adaptive_runtime_recovery",
                "successes": 0,
                "failures": 2,
                "consecutiveFailures": 2,
                "lastOutcome": "rejected",
            },
        ]
    }
}

rows = sandbox._negative_entries(state)
profiles = [row["profile"] for row in rows]
assert "terminal_transition_graph_v1" not in profiles, rows
assert "terminal_request_program_inference_v1" in profiles, rows
assert "adaptive_runtime_recovery" in profiles, rows

source = SCRIPT.read_text(encoding="utf-8")
assert 'row.get("executionObserved") is not True' in source
assert "POST_EXHAUSTION_STRATEGY_PROFILES" in source

print("Brain Learning unexecuted evolved-strategy suppression migration passed")
