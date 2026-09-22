#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "engine_v2" / "scripts" / "plan-repairs.mjs"

spec = importlib.util.spec_from_file_location(
    "brain_cross_phase_runtime",
    ROOT / "scripts" / "brain_repair_runtime.py",
)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

candidate = {
    "canonical_id": "cross-phase-demo",
    "censusPrior": {
        "status": "CHAIN REACHED",
        "dominantIssue": "provider_network_zero_result",
        "evidenceDepth": ["anime=chain_reached"],
    },
    "metadata": {"supportedTypes": ["anime"]},
}
result = {
    "status": "no_streams",
    "evidence": {"streams_playable": 0, "streams_returned": 0},
    "tests": [{
        "fixture": {"mediaType": "anime", "category": "anime", "title": "Synthetic"},
        "failure_class": "content_lookup_completed_no_streams",
        "status": "no_streams",
        "network_observations": [],
        "streams_playable": 0,
        "stream_count": 0,
    }],
}
policy = {
    "production": {
        "negativeExperimentMemory": {
            "rotateExperimentAfterFailures": 1,
            "maxVariantsPerSignature": 5,
            "finalVariantGeneration": 2,
            "maxLearningGenerationsPerSignature": 5,
        },
        "maxHypotheses": 3,
        "maxMutationsPerProvider": 2,
        "maxRepeatedSignature": 2,
        "maxGeneratedBytesPerProvider": 180000,
        "maxElapsedMsPerProvider": 45000,
    },
    "skillMaturity": {},
}

SIGNATURE = ""


def row(variant: int, generation: int = 1) -> dict:
    profile = "adaptive_runtime_recovery"
    if variant == 4 and generation >= 2:
        profile = "chain_terminal_extractor_v1" if generation == 2 else f"chain_terminal_extractor_v1_g{generation}"
    return {
        "providerId": "cross-phase-demo",
        "providerVersion": "*",
        "failureClass": "chain_terminal_gap",
        "signature": SIGNATURE,
        "profile": profile,
        "experimentVariant": variant,
        "experimentGeneration": generation,
        "failures": 1,
        "consecutiveFailures": 1,
        "successes": 0,
    }

def plan(memory: list[dict], mode: str) -> dict:
    payload = {
        "mode": mode,
        "policy": policy,
        "learnedSkills": {},
        "historicalSolutions": [],
        "negativeMemory": memory,
        "items": [{
            "key": "published:cross-phase-demo",
            "candidate": candidate,
            "result": result,
            "state": {},
        }],
    }
    completed = subprocess.run(
        ["node", str(PLANNER)],
        cwd=ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return next(iter((json.loads(completed.stdout).get("plans") or {}).values()))

SIGNATURE = plan([], "learning")["signature"]
assert SIGNATURE

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    base = td / "production-memory.json"
    learning = td / "learning-memory.json"

    # Production knows the four generic variants plus the old generation-1
    # terminal slot. It must still consider generation 2 fresh.
    base.write_text(json.dumps({
        "schemaVersion": 1,
        "entries": [row(0), row(1), row(2), row(3), row(4, 1)],
    }), encoding="utf-8")

    # The previous isolated Learning phase failed generation 2. This state is
    # explicitly read-only and must affect only the next Learning phase.
    learning.write_text(json.dumps({
        "schemaVersion": 1,
        "publicationAllowed": False,
        "productionWritesAllowed": False,
        "experimentMemory": {
            "schemaVersion": 1,
            "entries": [row(4, 2)],
        },
    }), encoding="utf-8")

    old_base = brain.REPAIR_MEMORY_PATH
    old_learning = brain.LEARNING_MEMORY_PATH
    old_mode = os.environ.get("NUVIO_BRAIN_PLANNER_MODE")
    brain.REPAIR_MEMORY_PATH = base
    brain.LEARNING_MEMORY_PATH = learning
    try:
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
        learning_memory = brain.planner_negative_memory("learning")
        assert any(
            x["experimentVariant"] == 4 and x["experimentGeneration"] == 2
            for x in learning_memory
        ), learning_memory
        next_learning = plan(learning_memory, "learning")
        assert next_learning["experimentVariant"] == 4, next_learning
        assert next_learning["experimentGeneration"] == 3, next_learning
        assert next_learning["experimentExhausted"] is False, next_learning
        assert next_learning["allowedProfiles"] == ["chain_terminal_extractor_v1_g3"], next_learning

        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "repair"
        production_memory = brain.planner_negative_memory("repair")
        assert not any(
            x["experimentVariant"] == 4 and x["experimentGeneration"] == 2
            for x in production_memory
        ), production_memory
        next_production = plan(production_memory, "repair")
        assert next_production["experimentGeneration"] == 2, next_production
        assert next_production["experimentExhausted"] is False, next_production
    finally:
        brain.REPAIR_MEMORY_PATH = old_base
        brain.LEARNING_MEMORY_PATH = old_learning
        if old_mode is None:
            os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
        else:
            os.environ["NUVIO_BRAIN_PLANNER_MODE"] = old_mode

queue_source = (ROOT / "scripts" / "run_brain_learning_queue.py").read_text(encoding="utf-8")
lab_source = (ROOT / "engine_v2" / "scripts" / "learning-lab.mjs").read_text(encoding="utf-8")
assert 'env["NIAKVIO_BRAIN_LEARNING_MEMORY"] = str(previous_state_path)' in queue_source
assert "experimentVariant: nonNegative(raw.experimentVariant)" in lab_source
assert "experimentGeneration: Math.max(1, nonNegative(raw.experimentGeneration) || 1)" in lab_source
assert "`g${Math.max(1, nonNegative(row.experimentGeneration) || 1)}`" in lab_source
assert "`v${nonNegative(row.experimentVariant)}`" in lab_source

print("Brain cross-phase experiment-memory progression contract passed")
