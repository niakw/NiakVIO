#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_local_force_guidance.py"
spec = importlib.util.spec_from_file_location("local_force_eval", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def result(*, status="no_streams", playable=0, returned=0, score=10, contradictions=0):
    verified = playable if contradictions == 0 else 0
    return {
        "status": status,
        "score": score,
        "evidence": {
            "streams_playable": playable,
            "streams_returned": returned,
            "identity_verified_streams": verified,
            "identity_unverified_streams": playable - verified,
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": 0,
        },
        "tests": (
            [{
                "fixture": {"label": "Synthetic", "tmdbId": "1"},
                "streams_playable": playable,
                "identity_verified_streams": verified,
                "identity_unverified_streams": playable - verified,
                "identity_contradiction_count": contradictions,
                "duration_identity_mismatch_count": 0,
            }]
            if playable else []
        ),
    }

baseline = result()
healthy = result(status="healthy", playable=1, returned=1, score=90)
accepted, reason = mod.evaluate_pair(baseline, healthy, 1)
assert accepted is True, reason

accepted, reason = mod.evaluate_pair(healthy, healthy, 1)
assert accepted is False
assert reason == "baseline_already_healthy"

accepted, reason = mod.evaluate_pair(baseline, healthy, 0)
assert accepted is False
assert reason == "deep_report_did_not_accept_repair"

contradictory = result(status="healthy", playable=1, returned=1, score=90, contradictions=1)
accepted, reason = mod.evaluate_pair(baseline, contradictory, 1)
assert accepted is False

source = SCRIPT.read_text(encoding="utf-8")
assert "localForcePromotion" in source
assert "run_adaptive_deep_repair.py" in source
assert "baseline_already_healthy" in source
assert "causalEvidenceOnly" in source
assert "providerPublicationAuthority" in source

print("Local FORCE guidance causal evaluator tests passed")
