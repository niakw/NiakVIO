#!/usr/bin/env python3
"""Bounded Brain negative-memory retains underrepresented repair signatures."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "scripts/brain_negative_memory_retention.py"
spec = importlib.util.spec_from_file_location("brain_negative_memory_retention", source)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(provider, signature, failures):
    return {
        "providerId": provider,
        "signature": signature,
        "profile": "runtime_response_salvage_v1",
        "failures": failures,
        "consecutiveFailures": failures,
        "experimentVariant": 4,
        "experimentGeneration": 2,
        "lastOutcome": "rejected",
    }


dominated = [row("4khdhub", f"legacy-{idx:04d}", 1000 - idx) for idx in range(1000)]
new = [
    row("animekai", "first-current-executed-timeout", 1),
    row("animesama-co", "first-new-candidate-network", 1),
    row("uhdmovies", "first-regressed-terminal-gap", 1),
]
retained = mod.select_bounded_negative_memory(dominated + new, limit=1000)
assert len(retained) == 1000
assert {r["providerId"] for r in retained} == {
    "4khdhub", "animekai", "animesama-co", "uhdmovies"
}, "newly executed providers must never disappear behind hot negative signatures"
assert len(mod.select_bounded_negative_memory(dominated + new, limit=14)) == 14
assert mod.select_bounded_negative_memory(dominated + new, limit=1000) == retained, "deterministic output"
assert len(mod.select_bounded_negative_memory(new, limit=3)) == 3
assert all(r["lastOutcome"] == "rejected" for r in retained)
# 800 new hubs x 20 executed signatures must remain representable; the old
# internal 10,000 cap silently truncated the configured 16,000-row budget.
scaled = [
    row(f"hub-{provider:04d}", f"signature-{index:02d}", index + 1)
    for provider in range(800) for index in range(20)
]
scalable = mod.select_bounded_negative_memory(scaled, limit=16000)
assert len(scalable) == 16000
assert len({r["providerId"] for r in scalable}) == 800

# The persistent runtime must not cut a hot 1000-entry ledger BEFORE merging
# a new, first-executed failure from Learning. Fair selection must see the new
# provider and the same configured budget must apply to both input streams.
runtime_path = ROOT / "scripts" / "brain_repair_runtime.py"
runtime_spec = importlib.util.spec_from_file_location("brain_repair_runtime_test", runtime_path)
assert runtime_spec and runtime_spec.loader
runtime = importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime)
old_paths = (runtime.REPAIR_MEMORY_PATH, runtime.LEARNING_MEMORY_PATH, runtime.POLICY_PATH)
old_mode = os.environ.get("NUVIO_BRAIN_PLANNER_MODE")
try:
    with tempfile.TemporaryDirectory(prefix="brain-800-provider-memory-") as tmp:
        home = Path(tmp)
        runtime.REPAIR_MEMORY_PATH = home / "memory.json"
        runtime.LEARNING_MEMORY_PATH = home / "learning.json"
        runtime.POLICY_PATH = home / "policy.json"
        runtime.REPAIR_MEMORY_PATH.write_text(
            json.dumps({"schemaVersion": 1, "entries": dominated}),
            encoding="utf-8",
        )
        runtime.LEARNING_MEMORY_PATH.write_text(json.dumps({
            "publicationAllowed": False,
            "productionWritesAllowed": False,
            "experimentMemory": {"entries": [{
                **row("animekai", "new-executed-evidence", 1),
                "executionObserved": True,
            }]},
        }), encoding="utf-8")
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
        runtime.POLICY_PATH.write_text(
            json.dumps({"production": {"negativeExperimentMemory": {"maxEntries": 1000}}}),
            encoding="utf-8",
        )
        with_new = runtime.repair_memory()["entries"]
        assert len(with_new) == 1000
        assert any(
            r.get("providerId") == "animekai"
            and r.get("signature") == "new-executed-evidence"
            for r in with_new
        ), "new Learning evidence lost to a pre-merge array slice"
        runtime.POLICY_PATH.write_text(
            json.dumps({"production": {"negativeExperimentMemory": {"maxEntries": 16000}}}),
            encoding="utf-8",
        )
        full = runtime.repair_memory()["entries"]
        assert len(full) == 1001, "policy configured capacity never reached the loader"
finally:
    runtime.REPAIR_MEMORY_PATH, runtime.LEARNING_MEMORY_PATH, runtime.POLICY_PATH = old_paths
    if old_mode is None:
        os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    else:
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = old_mode

print("Brain bounded negative memory retention tests passed")
