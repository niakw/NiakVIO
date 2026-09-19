#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

import runtime_repair  # noqa: E402

candidate = {
    "key": "test:repairable-status",
    "canonical_id": "repairable-status",
    "upstream_id": "repairable-status",
    "source": "test",
    "local_path": "providers/repairable-status.js",
    "metadata": {
        "id": "repairable-status",
        "name": "Repairable Status",
        "baseUrl": "https://repairable-status.example",
        "supportedTypes": ["movie", "tv", "anime"],
    },
    "local_patches": [],
}
source = "module.exports={getStreams:async()=>[]};\n"

# Runtime labels are observations, never terminal repair decisions. Every
# non-healthy/non-playable observation must enter adaptive recovery when a
# bounded provider origin is available. This intentionally includes unknown
# future labels so a new diagnostic vocabulary cannot silently disable Repair.
for status in (
    "no_streams",
    "degraded",
    "blocked",
    "provider_unreachable",
    "unavailable",
    "runtime_error",
    "reachable",
    "future_runtime_gap",
):
    result = {
        "status": status,
        "tests": [],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    assert runtime_repair._adaptive_failure(result) is True, status
    profiles = runtime_repair.matching_profiles(candidate, result, source)
    assert "adaptive_runtime_recovery" in profiles, (status, profiles)

# Even a nominal `healthy` label is repairable if no playable media backs it.
healthy_without_playable = {
    "status": "healthy",
    "tests": [],
    "evidence": {"streams_returned": 0, "streams_playable": 0},
}
assert runtime_repair._adaptive_failure(healthy_without_playable) is True
assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(candidate, healthy_without_playable, source)

# Only positive playable health bypasses runtime repair.
healthy = {
    "status": "healthy",
    "tests": [],
    "evidence": {"streams_returned": 1, "streams_playable": 1},
}
assert runtime_repair._adaptive_failure(healthy) is False
assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(candidate, healthy, source)

# `excluded` is not a runtime failure. It represents an explicit policy/safety
# decision (for example forbidden P2P/provenance) and must not be auto-repaired
# into an active provider by the unattended availability engine.
excluded = {
    "status": "excluded",
    "tests": [],
    "evidence": {"streams_returned": 0, "streams_playable": 0},
}
assert runtime_repair._adaptive_failure(excluded) is False
assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(candidate, excluded, source)

# Concrete failure classes still trigger repair independently of the coarse
# status label.
for failure_class in (
    "content_lookup_completed_no_streams",
    "stream_not_playback_verified",
    "stream_http_blocked",
    "provider_http_blocked",
    "provider_http_error",
):
    result = {
        "status": "reachable",
        "tests": [{"failure_class": failure_class}],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    assert runtime_repair._adaptive_failure(result) is True, failure_class
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(candidate, result, source)

print("repairable observation status tests passed")
