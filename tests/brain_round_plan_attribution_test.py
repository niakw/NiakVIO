#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "brain_repair_runtime.py"
spec = importlib.util.spec_from_file_location("brain_runtime_round_plan", SCRIPT)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    output = root / "output"
    output.mkdir()
    policy = root / "policy.json"
    overrides = root / "overrides.json"
    memory = root / "memory.json"
    census = root / "census.json"

    policy.write_text(json.dumps({
        "identity": {"name": "Test Brain"},
        "production": {
            "learningOnValidatedRepair": True,
            "negativeExperimentMemory": {
                "enabled": True,
                "maxEntries": 100,
            },
        },
        "skillMaturity": {},
    }), encoding="utf-8")
    overrides.write_text("{}", encoding="utf-8")
    memory.write_text(json.dumps({"schemaVersion": 1, "entries": []}), encoding="utf-8")
    census.write_text(json.dumps({"providers": []}), encoding="utf-8")

    plan1 = {
        "providerId": "synthetic-rounds",
        "failureClass": "chain_terminal_gap",
        "signature": "sig-round-1",
        "experimentVariant": 4,
        "experimentGeneration": 1,
        "capabilityStrategy": "html_scraper",
        "observedPipelineStage": "player",
        "action": "probe-targeted-repair",
        "allowedProfiles": ["adaptive_runtime_recovery"],
        "hypotheses": [],
    }
    plan2 = {
        **plan1,
        "signature": "sig-round-2",
        "experimentGeneration": 2,
        "observedPipelineStage": "terminal",
    }
    report = {
        "rounds": [
            {
                "round": 1,
                "attempts": [{
                    "parent_key": "published:synthetic-rounds",
                    "profile": "adaptive_runtime_recovery",
                    "status": "generated",
                    "brain_plan": plan1,
                }],
                "accepted": [],
                "exploration_progress": [],
                "rejected": [{
                    "parent_key": "published:synthetic-rounds",
                    "profile": "adaptive_runtime_recovery",
                    "reason": "round1-rejected",
                    "brain_plan": plan1,
                }],
            },
            {
                "round": 2,
                "attempts": [{
                    "parent_key": "published:synthetic-rounds",
                    "profile": "adaptive_runtime_recovery",
                    "status": "generated",
                    "brain_plan": plan2,
                }],
                "accepted": [],
                "exploration_progress": [],
                "rejected": [{
                    "parent_key": "published:synthetic-rounds",
                    "profile": "adaptive_runtime_recovery",
                    "reason": "round2-rejected",
                    "brain_plan": plan2,
                }],
            },
        ]
    }
    (output / "repair-report.json").write_text(json.dumps(report), encoding="utf-8")

    old = (
        brain.POLICY_PATH,
        brain.OVERRIDES_PATH,
        brain.REPAIR_MEMORY_PATH,
        brain.CENSUS_STATUS_PATH,
    )
    brain.POLICY_PATH = policy
    brain.OVERRIDES_PATH = overrides
    brain.REPAIR_MEMORY_PATH = memory
    brain.CENSUS_STATUS_PATH = census
    brain.reset_runtime_state()
    # Deliberately leave only the FINAL replanned decision in mutable PLANS.
    # Round 1 must still retain sig-round-1/generation 1 from its event snapshot.
    brain.PLANS["published:synthetic-rounds"] = dict(plan2)
    try:
        brain.annotate_and_learn(output, "deep")
    finally:
        (
            brain.POLICY_PATH,
            brain.OVERRIDES_PATH,
            brain.REPAIR_MEMORY_PATH,
            brain.CENSUS_STATUS_PATH,
        ) = old

    rows = json.loads(memory.read_text(encoding="utf-8"))["entries"]
    observed = {
        (
            row.get("signature"),
            int(row.get("experimentVariant") or 0),
            int(row.get("experimentGeneration") or 1),
            row.get("lastReason"),
        )
        for row in rows
        if row.get("providerId") == "synthetic-rounds"
        and row.get("profile") == "adaptive_runtime_recovery"
    }
    assert ("sig-round-1", 4, 1, "round1-rejected") in observed, observed
    assert ("sig-round-2", 4, 2, "round2-rejected") in observed, observed

deep = (ROOT / "scripts" / "deep_repair_loop.py").read_text(encoding="utf-8")
assert '"brain_plan": plan_snapshot' in deep
assert '"brain_plan": copy.deepcopy(candidate_variant.get("brain_repair_plan") or {})' in deep

print("Brain multi-round causal plan attribution contract passed")
