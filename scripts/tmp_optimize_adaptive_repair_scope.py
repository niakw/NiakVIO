#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
repair = ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py"
test = ROOT / "tests" / "adaptive_runtime_repair_test.py"

source = repair.read_text(encoding="utf-8")
old = '''def _adaptive_failure(result: dict[str, Any]) -> bool:
    status = str(result.get("status") or "runtime_error")
    failures = {str(test.get("failure_class") or "") for test in _base._tests(result)}
    return status in {"no_streams", "degraded", "blocked", "provider_unreachable", "unavailable"} or bool(failures & {
        "content_lookup_completed_no_streams", "stream_not_playback_verified",
        "stream_http_blocked", "provider_http_blocked", "provider_http_error",
        "worker_memory_exhausted",
    })
'''
new = '''def _adaptive_failure(result: dict[str, Any]) -> bool:
    status = str(result.get("status") or "runtime_error")
    playable = _base.playable_stream_count(result)
    # Runtime recovery is an expensive network fallback. A provider that is
    # already healthy *and* has current playable proof does not need to be
    # rewritten merely because a secondary fixture missed. Keep inconsistent
    # "healthy" rows with zero playable proof eligible so the guard fails safe.
    if status == "healthy" and playable > 0:
        return False
    failures = {str(test.get("failure_class") or "") for test in _base._tests(result)}
    return status in {"no_streams", "degraded", "blocked", "provider_unreachable", "unavailable"} or bool(failures & {
        "content_lookup_completed_no_streams", "stream_not_playback_verified",
        "stream_http_blocked", "provider_http_blocked", "provider_http_error",
        "worker_memory_exhausted",
    })
'''
if new not in source:
    if old not in source:
        raise SystemExit("adaptive failure anchor missing")
    source = source.replace(old, new, 1)
repair.write_text(source, encoding="utf-8")

source = test.read_text(encoding="utf-8")
anchor = '''    healthy = {
        "status": "healthy",
        "tests": [],
        "evidence": {"streams_returned": 1, "streams_playable": 1},
    }
'''
replacement = '''    healthy = {
        "status": "healthy",
        "tests": [],
        "evidence": {"streams_returned": 1, "streams_playable": 1},
    }
    healthy_with_secondary_gap = {
        "status": "healthy",
        "tests": [{"failure_class": "content_lookup_completed_no_streams", "streams_playable": 0}],
        "evidence": {"streams_returned": 1, "streams_playable": 1},
    }
    healthy_without_playable_proof = {
        "status": "healthy",
        "tests": [{"failure_class": "content_lookup_completed_no_streams", "streams_playable": 0}],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
'''
if replacement not in source:
    if anchor not in source:
        raise SystemExit("adaptive runtime test fixture anchor missing")
    source = source.replace(anchor, replacement, 1)

assertion_anchor = '''    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy, source
    )
'''
assertion_replacement = '''    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy, source
    )
    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy_with_secondary_gap, source
    )
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        candidate, healthy_without_playable_proof, source
    )
'''
if assertion_replacement not in source:
    if assertion_anchor not in source:
        raise SystemExit("adaptive runtime test assertion anchor missing")
    source = source.replace(assertion_anchor, assertion_replacement, 1)

test.write_text(source, encoding="utf-8")
print("adaptive repair scope optimization applied: proven healthy providers are not opportunistically rewritten")
