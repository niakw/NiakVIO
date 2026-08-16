#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

identity_path = ROOT / "scripts" / "repair_identity_gate.py"
identity_spec = importlib.util.spec_from_file_location("repair_identity_gate_test_module", identity_path)
identity = importlib.util.module_from_spec(identity_spec)
assert identity_spec and identity_spec.loader
identity_spec.loader.exec_module(identity)

quick_path = ROOT / "scripts" / "run_adaptive_quick_repair.py"
quick_spec = importlib.util.spec_from_file_location("run_adaptive_quick_repair_test_module", quick_path)
quick = importlib.util.module_from_spec(quick_spec)
assert quick_spec and quick_spec.loader
quick_spec.loader.exec_module(quick)


def result(*, status="healthy", movie=0, tv=0, anime=0, verified=0, unknown=0, contradictions=0, duration=0, score=80):
    tests = []
    for category, playable in (("movie", movie), ("tv", tv), ("anime", anime)):
        if playable <= 0:
            continue
        tests.append({
            "fixture": {"label": category, "category": category},
            "streams_playable": playable,
            "identity_verified_streams": min(verified, playable),
            "identity_unverified_streams": min(unknown, playable),
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": duration,
        })
    return {
        "status": status,
        "score": score,
        "tests": tests,
        "evidence": {
            "streams_playable": max(movie, tv, anime),
            "streams_returned": max(movie, tv, anime),
            "identity_verified_streams": verified,
            "identity_unverified_streams": unknown,
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": duration,
            "fixture_status_counts": {},
        },
    }


# Unknown identity is provisional-safe, but still not good enough for deep
# durable learning.
unknown_playable = result(movie=1, verified=0, unknown=1)
assert identity.automatic_repair_safety_gate(unknown_playable)[0] is True
assert identity.automatic_repair_identity_gate(unknown_playable)[0] is False

# Positive wrong-content evidence remains an immediate rejection.
wrong = result(movie=1, verified=0, unknown=0, contradictions=1)
assert identity.automatic_repair_safety_gate(wrong)[0] is False

# A quick repair may restore a previously dead category without being forced to
# solve every supported catalogue category in the same bounded pass.
parent = result(movie=1, tv=0, verified=1, unknown=0, score=70)
repaired = result(movie=1, tv=1, verified=0, unknown=1, score=80)
accepted, reason = quick._quick_compare_results(parent, repaired)
assert accepted is True, reason
assert reason == "provisional_quick_runtime_improvement"

# But it must never trade away a category that was already working.
regressed = result(movie=0, tv=2, verified=0, unknown=1, score=90)
accepted, reason = quick._quick_compare_results(parent, regressed)
assert accepted is False
assert reason == "quick_category_regression:movie"

# Dead -> playable is the core repair-first case.
dead = result(status="no_streams", score=10)
restored = result(movie=1, verified=0, unknown=1, score=75)
accepted, reason = quick._quick_compare_results(dead, restored)
assert accepted is True, reason

print("quick repair acceptance policy test passed")
