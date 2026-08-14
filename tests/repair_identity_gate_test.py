#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from repair_identity_gate import automatic_repair_identity_gate


def sample(
    *,
    playable: int = 1,
    verified: int = 1,
    unknown: int = 0,
    contradictions: int = 0,
    duration_mismatches: int = 0,
    include_playable_fixture: bool = True,
) -> dict:
    tests = []
    if include_playable_fixture:
        tests.append(
            {
                "fixture": {"label": "Interstellar"},
                "streams_playable": playable,
                "identity_verified_streams": verified,
                "identity_unverified_streams": unknown,
                "identity_contradiction_count": contradictions,
                "duration_identity_mismatch_count": duration_mismatches,
            }
        )
    return {
        "status": "healthy",
        "evidence": {
            "streams_playable": playable,
            "identity_verified_streams": verified,
            "identity_unverified_streams": unknown,
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": duration_mismatches,
        },
        "tests": tests,
    }


ok, reason = automatic_repair_identity_gate(sample())
assert ok and reason == "positive_content_identity_proof", (ok, reason)

ok, reason = automatic_repair_identity_gate(sample(duration_mismatches=1))
assert not ok and "duration_identity_mismatch" in reason, (ok, reason)

ok, reason = automatic_repair_identity_gate(sample(contradictions=1))
assert not ok and "content_identity_contradiction" in reason, (ok, reason)

ok, reason = automatic_repair_identity_gate(sample(verified=0, unknown=1))
assert not ok and "no_positive_content_identity_proof" in reason, (ok, reason)

ok, reason = automatic_repair_identity_gate(sample(playable=2, verified=1, unknown=1))
assert not ok, (ok, reason)

ok, reason = automatic_repair_identity_gate(sample(include_playable_fixture=False))
assert not ok and reason == "identity_gate:no_fixture_level_playable_identity_proof", (ok, reason)

runner = (ROOT / "scripts" / "run_adaptive_deep_repair.py").read_text(encoding="utf-8")
assert "automatic_repair_identity_gate" in runner
assert 'sys.argv.extend(["--max-rounds", "0"])' not in runner
assert "runtime_repair.compare_results = _identity_safe_compare_results" in runner

print("automatic repair identity promotion gate tests passed")
