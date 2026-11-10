#!/usr/bin/env python3
"""The UHDMovies 0->2 Quick result is useful but not publishable evidence."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("deep_repair_loop", ROOT/"scripts/deep_repair_loop.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
def result(verified: int, unknown: int, contradictions: int = 0) -> dict:
    return {
        "status": "healthy",
        "evidence": {"streams_playable": 2,
            "identity_verified_streams": verified,
            "identity_unverified_streams": unknown,
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": 0},
        "tests": [{"fixture":{"label":"movie"}, "streams_playable":2,
            "identity_verified_streams":verified, "identity_unverified_streams":unknown,
            "identity_contradiction_count":contradictions,
            "duration_identity_mismatch_count":0}],
    }
assert module.durable_promotion_state(result(0,2), "provisional_quick_runtime_improvement") == (
    False, "quick_candidate_requires_strict_identity_replay")
assert module.durable_promotion_state(result(2,0), "provisional_quick_runtime_improvement")[0] is False
assert module.durable_promotion_state(result(0,2), "strict_playable_stream_improvement")[0] is False
assert module.durable_promotion_state(result(2,0), "strict_playable_stream_improvement") == (
    True, "positive_content_identity_proof")
assert module.durable_promotion_state(result(2,0,1), "strict_playable_stream_improvement")[0] is False
print("FIELD_BRAIN_QUICK_PROVISIONAL_NO_PUBLISH quick_2_streams_blocked=true "
      "positive_identity_required=true retained_experiment_not_production=true")
