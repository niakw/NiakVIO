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

# These are raw probe observations, never terminal repair decisions. Every one
# must enter the adaptive recovery path when a bounded provider origin is known.
for status in (
    "no_streams",
    "degraded",
    "blocked",
    "provider_unreachable",
    "unavailable",
):
    result = {
        "status": status,
        "tests": [],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    assert runtime_repair._adaptive_failure(result) is True, status
    profiles = runtime_repair.matching_profiles(candidate, result, source)
    assert "adaptive_runtime_recovery" in profiles, (status, profiles)

# A positive playable result is the only observation in this family that must
# bypass repair. Strong safety exclusions remain separate and are not converted
# into availability repair attempts.
healthy = {
    "status": "healthy",
    "tests": [],
    "evidence": {"streams_returned": 1, "streams_playable": 1},
}
assert runtime_repair._adaptive_failure(healthy) is False
assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(candidate, healthy, source)

# Concrete failure classes must also trigger repair even when the coarse status
# is not one of the legacy availability labels.
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
