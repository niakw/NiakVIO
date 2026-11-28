#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "engine_v2/scripts/plan-repairs.mjs"

PARENT = "c" * 64
OTHER = "d" * 64

candidate = {
    "canonical_id": "parent-scoped-demo",
    "parentArtifactSha256": PARENT,
    "parentAuthority": "published-exact-current-bytes",
    "censusPrior": {
        "status": "CHAIN REACHED",
        "dominantIssue": "provider_network_zero_result",
        "evidenceDepth": ["movie=chain_reached"],
    },
    "metadata": {"supportedTypes": ["movie"]},
}
result = {
    "status": "no_streams",
    "evidence": {"streams_playable": 0, "streams_returned": 0},
    "tests": [{
        "fixture": {"mediaType": "movie", "category": "movie", "title": "Synthetic"},
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
        },
        "maxHypotheses": 3,
        "maxMutationsPerProvider": 2,
        "maxRepeatedSignature": 2,
        "maxGeneratedBytesPerProvider": 180000,
        "maxElapsedMsPerProvider": 45000,
    },
    "skillMaturity": {},
}

def memory(parent_sha: str = "", authority: str = "") -> dict:
    row = {
        "providerId": "parent-scoped-demo",
        "failureClass": "chain_terminal_gap",
        "profile": "adaptive_runtime_recovery",
        "experimentVariant": 0,
        "experimentGeneration": 1,
        "failures": 1,
        "consecutiveFailures": 1,
        "successes": 0,
        "executionObserved": True,
        "causalExerciseObserved": True,
    }
    if parent_sha:
        row["parentArtifactSha256"] = parent_sha
    if authority:
        row["parentAuthority"] = authority
    return row

def run(rows: list[dict]) -> dict:
    payload = {
        "mode": "repair",
        "policy": policy,
        "learnedSkills": {},
        "negativeMemory": rows,
        "items": [{
            "key": "published:parent-scoped-demo",
            "candidate": candidate,
            "result": result,
            "state": {},
        }],
    }
    child = subprocess.run(
        ["node", str(PLANNER)],
        cwd=ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    parsed = json.loads(child.stdout)
    plan = next(iter((parsed.get("plans") or {}).values()))
    assert plan["parentArtifactSha256"] == PARENT, plan
    assert plan["parentAuthority"] == "published-exact-current-bytes", plan
    return plan

# Legacy parentless memory remains historical but cannot veto an explicitly
# identified exact production parent.
legacy = run([memory()])
assert legacy["negativeMemoryMatches"] == 0, legacy
assert legacy["experimentVariant"] == 0, legacy

wrong = run([memory(OTHER, "published-exact-current-bytes")])
assert wrong["negativeMemoryMatches"] == 0, wrong
assert wrong["experimentVariant"] == 0, wrong

same = run([memory(PARENT, "published-exact-current-bytes")])
assert same["negativeMemoryMatches"] == 1, same
assert same["experimentVariant"] == 1, same

# Cross-day serialization must retain the same parent identity rather than
# collapsing it back into a provider/profile-only row.
learning_lab = (ROOT / "engine_v2/scripts/learning-lab.mjs").read_text(encoding="utf-8")
assert "parentArtifactSha256" in learning_lab
assert "parentAuthority" in learning_lab
assert "row.parentArtifactSha256 || ''" in learning_lab
assert "row.parentAuthority || ''" in learning_lab

# The canonical Python Learning ledger key must also distinguish parent bytes.
spec = importlib.util.spec_from_file_location(
    "learning_queue_parent_scope", ROOT / "scripts/run_brain_learning_queue.py"
)
assert spec and spec.loader
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)
base = {
    "providerId": "parent-scoped-demo",
    "providerVersion": "*",
    "failureClass": "chain_terminal_gap",
    "signature": "sig",
    "profile": "adaptive_runtime_recovery",
    "experimentVariant": 0,
    "experimentGeneration": 1,
}
a = {**base, "parentArtifactSha256": PARENT, "parentAuthority": "published-exact-current-bytes"}
b = {**base, "parentArtifactSha256": OTHER, "parentAuthority": "published-exact-current-bytes"}
assert queue._phase_experiment_key(a) != queue._phase_experiment_key(b)

runtime_spec = importlib.util.spec_from_file_location(
    "brain_runtime_parent_scope", ROOT / "scripts/brain_repair_runtime.py"
)
assert runtime_spec and runtime_spec.loader
runtime = importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime)
snapshot = runtime._plan_snapshot({
    "providerId": "parent-scoped-demo",
    "parentArtifactSha256": PARENT,
    "parentAuthority": "published-exact-current-bytes",
    "failureClass": "chain_terminal_gap",
    "signature": "sig",
})
assert snapshot["parentArtifactSha256"] == PARENT
assert snapshot["parentAuthority"] == "published-exact-current-bytes"

runtime_source = (ROOT / "scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
sanitized_plans = runtime_source[runtime_source.index("sanitized_plans = {"):]
assert '"parentArtifactSha256": row.get("parentArtifactSha256")' in sanitized_plans
assert '"parentAuthority": row.get("parentAuthority")' in sanitized_plans

print(
    "FIELD_BRAIN_PARENT_SCOPED_NEGATIVE_MEMORY "
    "legacy_exact_parent_veto=false wrong_parent_veto=false same_parent_veto=true "
    "cross_day_parent_identity=true"
)
