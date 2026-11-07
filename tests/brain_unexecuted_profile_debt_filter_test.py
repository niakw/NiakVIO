#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "brain_unexecuted_profile_runtime",
    ROOT / "scripts" / "brain_repair_runtime.py",
)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

with tempfile.TemporaryDirectory() as td:
    memory = Path(td) / "memory.json"
    stale = {
        "providerId": "allanime",
        "providerVersion": "*",
        "failureClass": "chain_terminal_gap",
        "signature": "legacy-unexecuted",
        "profile": "chain_terminal_extractor_v1",
        "experimentVariant": 4,
        "experimentGeneration": 2,
        "failures": 1,
        "consecutiveFailures": 1,
        "successes": 0,
        "lastOutcome": "profile_unavailable",
        "lastReason": "planned_profile_not_applicable_to_current_bytes",
    }
    executed = {
        **stale,
        "providerId": "mallumv",
        "signature": "real-negative",
        "lastOutcome": "rejected",
        "lastReason": "playback_gate_failed",
        "executionObserved": True,
    }
    # Historical writers sometimes recorded executionObserved=True despite
    # never producing a candidate. Both cases must remain non-executed.
    legacy_unavailable = {
        **stale, "providerId": "vidfast", "signature": "legacy-false-execution",
        "executionObserved": True,
    }
    missing_candidate = {
        **stale, "providerId": "moviebox", "signature": "generation-only",
        "lastOutcome": "not_generated", "lastReason": "no_candidate_bytes",
        "executionObserved": True,
    }
    memory.write_text(json.dumps({
        "schemaVersion": 1,
        "entries": [stale, executed, legacy_unavailable, missing_candidate],
    }), encoding="utf-8")
    old = brain.REPAIR_MEMORY_PATH
    brain.REPAIR_MEMORY_PATH = memory
    try:
        production = brain.planner_negative_memory("repair")
        assert [row["providerId"] for row in production] == ["mallumv"], production
        assert production[0]["executionObserved"] is True, production

        deep = brain.planner_negative_memory("deep")
        assert [row["providerId"] for row in deep] == ["mallumv"], deep

        learning = brain.planner_negative_memory("learning")
        assert {row["providerId"] for row in learning} == {
            "allanime", "mallumv", "vidfast", "moviebox",
        }, learning
        for provider in ("allanime", "vidfast", "moviebox"):
            unexecuted = next(row for row in learning if row["providerId"] == provider)
            assert unexecuted["executionObserved"] is False, unexecuted
        generation = next(row for row in learning if row["providerId"] == "moviebox")
        assert generation["lastOutcome"] == "not_generated", generation
        assert generation["generationAttemptObserved"] is True, generation
    finally:
        brain.REPAIR_MEMORY_PATH = old

# This is a behavioral gate. Counting assignment statements in the Brain
# source was non-representative and broke a safe refactor without exposing any
# genuine execution failure. Only the observed runtime memory output matters.
print("Brain unexecuted profile debt filter contract passed")
