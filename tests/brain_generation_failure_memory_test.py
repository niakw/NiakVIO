#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "brain_repair_runtime.py"
spec = importlib.util.spec_from_file_location("brain_repair_runtime_generation_failure_test", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    output = root / "out"
    output.mkdir()
    report_path = output / "repair-report.json"
    report_path.write_text(json.dumps({
        "rounds": [{
            "round": 1,
            "attempts": [{
                "parent_key": "published:showbox",
                "profile": "adaptive_runtime_recovery",
                "status": "not_generated",
                "reason": "no_executable_runtime_options",
            }],
            "accepted": [],
            "rejected": [],
        }]
    }), encoding="utf-8")

    mod.OVERRIDES_PATH = root / "provider-overrides.json"
    mod.REPAIR_MEMORY_PATH = root / "brain-repair-memory.json"
    mod.OVERRIDES_PATH.write_text(json.dumps({
        "runtime_repair": {"learned_skills": {}}
    }), encoding="utf-8")
    mod.REPAIR_MEMORY_PATH.write_text(json.dumps({
        "schemaVersion": 1,
        "entries": [],
    }), encoding="utf-8")
    mod.PLANS.clear()
    mod.PLANS["published:showbox"] = {
        "providerId": "showbox",
        "brainVersion": 7,
        "failureClass": "route_proven_gap",
        "signature": "same-signature",
        "experimentVariant": 0,
        "capabilityStrategy": "html_scraper",
        "observedPipelineStage": "detail",
        "repairScope": "capability",
        "hypotheses": [],
        "allowedProfiles": ["adaptive_runtime_recovery"],
    }
    mod.policy = lambda: {
        "identity": {"name": "NiakVIO Brain"},
        "production": {
            "learningOnValidatedRepair": True,
            "negativeExperimentMemory": {
                "enabled": True,
                "maxEntries": 1000,
            },
        },
        "skillMaturity": {},
    }

    brain = mod.annotate_and_learn(output, "deep")
    memory = json.loads(mod.REPAIR_MEMORY_PATH.read_text(encoding="utf-8"))
    entries = memory.get("entries") or []
    assert len(entries) == 1, entries
    row = entries[0]
    assert row["providerId"] == "showbox", row
    assert row["failureClass"] == "route_proven_gap", row
    assert row["signature"] == "same-signature", row
    assert row["profile"] == "adaptive_runtime_recovery", row
    assert row["experimentVariant"] == 0, row
    assert row["failures"] == 1, row
    assert row["consecutiveFailures"] == 1, row
    assert row["successes"] == 0, row
    assert row["lastOutcome"] == "not_generated", row
    assert row["lastReason"] == "no_executable_runtime_options", row
    assert brain["negativeExperimentEvents"] == 1, brain

print("Brain candidate-generation negative-memory contract passed")
