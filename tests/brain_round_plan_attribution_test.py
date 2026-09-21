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


# A sandbox-only causal gain that never reaches production acceptance must be
# durable across outer waves. Otherwise the next wave restages published bytes
# and repeats the exact same experiment.
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
            "negativeExperimentMemory": {"enabled": True, "maxEntries": 100},
        },
        "skillMaturity": {},
    }), encoding="utf-8")
    overrides.write_text("{}", encoding="utf-8")
    memory.write_text(json.dumps({"schemaVersion": 1, "entries": []}), encoding="utf-8")
    census.write_text(json.dumps({"providers": []}), encoding="utf-8")
    plan = {
        "providerId": "synthetic-plateau",
        "failureClass": "provider_transport_gap",
        "signature": "sig-plateau",
        "experimentVariant": 4,
        "experimentGeneration": 2,
        "capabilityStrategy": "iframe_player",
        "observedPipelineStage": "provider",
        "action": "probe-targeted-repair",
        "allowedProfiles": ["adaptive_runtime_recovery"],
        "hypotheses": [],
    }
    progress = {
        "parent_key": "published:synthetic-plateau",
        "profile": "adaptive_runtime_recovery",
        "reason": "sandbox_diagnostic_progress:provider-success",
        "brain_plan": plan,
    }
    (output / "repair-report.json").write_text(json.dumps({
        "rounds": [{
            "round": 1,
            "attempts": [{
                "parent_key": "published:synthetic-plateau",
                "profile": "adaptive_runtime_recovery",
                "status": "generated",
                "brain_plan": plan,
            }],
            "accepted": [],
            "exploration_progress": [progress],
            "rejected": [],
        }]
    }), encoding="utf-8")
    old = (brain.POLICY_PATH, brain.OVERRIDES_PATH, brain.REPAIR_MEMORY_PATH, brain.CENSUS_STATUS_PATH)
    brain.POLICY_PATH, brain.OVERRIDES_PATH, brain.REPAIR_MEMORY_PATH, brain.CENSUS_STATUS_PATH = (
        policy, overrides, memory, census
    )
    brain.reset_runtime_state()
    brain.PLANS["published:synthetic-plateau"] = dict(plan)
    try:
        report_brain = brain.annotate_and_learn(output, "deep")
    finally:
        brain.POLICY_PATH, brain.OVERRIDES_PATH, brain.REPAIR_MEMORY_PATH, brain.CENSUS_STATUS_PATH = old
    rows = json.loads(memory.read_text(encoding="utf-8"))["entries"]
    row = next(x for x in rows if x.get("providerId") == "synthetic-plateau")
    assert row["failures"] == 1, row
    assert row["consecutiveFailures"] == 1, row
    assert row["progresses"] == 1, row
    assert row["lastOutcome"] == "exploration_progress_nonpublishable", row
    assert row["lastReason"] == "sandbox_diagnostic_progress:provider-success", row
    assert report_brain["negativeExperimentEvents"] == 1, report_brain

# The same exploration step is not negative memory when a later round in the
# same bounded invocation reaches a strict accepted repair.
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
            "negativeExperimentMemory": {"enabled": True, "maxEntries": 100},
        },
        "skillMaturity": {},
    }), encoding="utf-8")
    overrides.write_text("{}", encoding="utf-8")
    memory.write_text(json.dumps({"schemaVersion": 1, "entries": []}), encoding="utf-8")
    census.write_text(json.dumps({"providers": []}), encoding="utf-8")
    plan = {
        "providerId": "synthetic-progress-to-success",
        "failureClass": "chain_terminal_gap",
        "signature": "sig-progress-success",
        "experimentVariant": 3,
        "experimentGeneration": 1,
        "capabilityStrategy": "direct_media",
        "observedPipelineStage": "player",
        "action": "probe-targeted-repair",
        "allowedProfiles": ["adaptive_runtime_recovery"],
        "hypotheses": [],
    }
    parent = "published:synthetic-progress-to-success"
    (output / "repair-report.json").write_text(json.dumps({
        "rounds": [
            {
                "round": 1,
                "attempts": [{"parent_key": parent, "profile": "adaptive_runtime_recovery", "status": "generated", "brain_plan": plan}],
                "accepted": [],
                "exploration_progress": [{
                    "parent_key": parent,
                    "profile": "adaptive_runtime_recovery",
                    "reason": "sandbox_diagnostic_progress:returned",
                    "brain_plan": plan,
                }],
                "rejected": [],
            },
            {
                "round": 2,
                "attempts": [{"parent_key": parent, "profile": "adaptive_runtime_recovery", "status": "generated", "brain_plan": plan}],
                "accepted": [{
                    "parent_key": parent,
                    "profile": "adaptive_runtime_recovery",
                    "reason": "strict_playable_stream_improvement",
                    "brain_plan": plan,
                }],
                "exploration_progress": [],
                "rejected": [],
            },
        ]
    }), encoding="utf-8")
    old = (brain.POLICY_PATH, brain.OVERRIDES_PATH, brain.REPAIR_MEMORY_PATH, brain.CENSUS_STATUS_PATH)
    brain.POLICY_PATH, brain.OVERRIDES_PATH, brain.REPAIR_MEMORY_PATH, brain.CENSUS_STATUS_PATH = (
        policy, overrides, memory, census
    )
    brain.reset_runtime_state()
    brain.PLANS[parent] = dict(plan)
    try:
        brain.annotate_and_learn(output, "deep")
    finally:
        brain.POLICY_PATH, brain.OVERRIDES_PATH, brain.REPAIR_MEMORY_PATH, brain.CENSUS_STATUS_PATH = old
    rows = json.loads(memory.read_text(encoding="utf-8"))["entries"]
    row = next(x for x in rows if x.get("providerId") == "synthetic-progress-to-success")
    assert row["successes"] == 1, row
    assert row["failures"] == 0, row
    assert row["consecutiveFailures"] == 0, row
    assert row["lastOutcome"] == "accepted", row

deep = (ROOT / "scripts" / "deep_repair_loop.py").read_text(encoding="utf-8")
assert '"brain_plan": plan_snapshot' in deep
assert '"brain_plan": copy.deepcopy(candidate_variant.get("brain_repair_plan") or {})' in deep

print("Brain multi-round causal plan attribution contract passed")
