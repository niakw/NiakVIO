#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_brain_llm_force_candidates.py"
spec = importlib.util.spec_from_file_location("force_eval", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def result(*, status="no_streams", playable=0, returned=0, score=0, contradictions=0):
    return {
        "status": status,
        "score": score,
        "evidence": {
            "streams_playable": playable,
            "streams_returned": returned,
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": 0,
            "required_fixture_categories": [],
            "healthy_fixture_categories": [],
        },
        "tests": [],
    }


baseline = result(status="no_streams", playable=0, returned=0, score=20)
candidate = result(status="healthy", playable=1, returned=1, score=90)
accepted, reason = mod.evaluate_pair(baseline, candidate)
assert accepted is True, reason
assert reason == "strict_playable_stream_improvement", reason

no_gain = result(status="reachable", playable=0, returned=1, score=80)
accepted, reason = mod.evaluate_pair(baseline, no_gain)
assert accepted is False
assert reason == "insufficient_playable_stream_proof", reason

contradictory = result(
    status="healthy",
    playable=1,
    returned=1,
    score=95,
    contradictions=1,
)
accepted, reason = mod.evaluate_pair(baseline, contradictory)
assert accepted is False
assert "identity" in reason.casefold() or "contradiction" in reason.casefold(), reason

failure = mod.candidate_execution_error(
    __import__("subprocess").CalledProcessError(
        1,
        ["python", "scripts/apply_brain_llm_force_mutations.py"],
    )
)
assert failure == "command_failed:apply_brain_llm_force_mutations.py:rc=1", failure
source = SCRIPT.read_text(encoding="utf-8")
assert "force_candidate_execution_error" in source
assert "One malformed/stale Force hypothesis must never cancel" in source
assert "except (subprocess.SubprocessError, ValueError, OSError) as exc:" in source
assert 'dir=ROOT / "local-output"' in source

summary = mod.invocation_summary({
    "tests": [{
        "fixture": {"label": "Fixture"},
        "invocation_diagnostics": [{
            "name": "object",
            "inferred_mode": "object",
            "result": "empty",
            "stream_count": 0,
            "provider_observations": 0,
        }],
    }],
})
assert summary == [{
    "fixture": "Fixture",
    "name": "object",
    "inferredMode": "object",
    "result": "empty",
    "streamCount": 0,
    "providerObservations": 0,
    "errorCode": "",
}], summary

print("Brain LLM isolated Force candidate evaluator tests passed")
