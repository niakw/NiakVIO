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


def result(
    *,
    status="no_streams",
    playable=0,
    returned=0,
    score=0,
    contradictions=0,
    quality_heights=None,
    effective_height=0,
    audio_languages=None,
    reachable_hosts=None,
    announced_player_candidates=0,
    explored_player_requests=0,
    announced_quality_heights=None,
    fanout_state="",
):
    verified = playable if contradictions <= 0 else 0
    tests = []
    if playable > 0:
        tests.append({
            "fixture": {"label": "Synthetic fixture", "tmdbId": "1"},
            "streams_playable": playable,
            "identity_verified_streams": verified,
            "identity_unverified_streams": playable - verified,
            "identity_contradiction_count": contradictions,
            "duration_identity_mismatch_count": 0,
            "returned_quality_heights": list(quality_heights or []),
            "effective_max_height": int(effective_height or 0) or None,
            "verified_max_height": int(effective_height or 0) or None,
            "audio_languages": list(audio_languages or []),
            "reachable_hosts": list(reachable_hosts or []),
            "announced_player_candidates": int(announced_player_candidates or 0),
            "explored_player_requests": int(explored_player_requests or 0),
            "announced_quality_heights": list(announced_quality_heights or []),
            "variant_fanout_state": fanout_state,
        })
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
            "required_fixture_categories": [],
            "healthy_fixture_categories": [],
        },
        "tests": tests,
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

coverage_baseline = result(
    status="healthy",
    playable=1,
    returned=4,
    score=90,
    quality_heights=[480],
    effective_height=480,
    reachable_hosts=["stream.example"],
)
coverage_candidate = result(
    status="healthy",
    playable=1,
    returned=8,
    score=90,
    quality_heights=[480, 720, 1080, 2160],
    effective_height=2160,
    reachable_hosts=["stream.example"],
)
accepted, reason = mod.evaluate_pair(
    coverage_baseline,
    coverage_candidate,
    "bounded-variant-enumeration-before-cap",
)
assert accepted is True, reason
assert reason.startswith("variant_coverage_improvement:"), reason
assert "playable-height" in reason, reason

count_only_candidate = result(
    status="healthy",
    playable=2,
    returned=8,
    score=95,
    quality_heights=[480],
    effective_height=480,
    reachable_hosts=["stream.example"],
)
accepted, reason = mod.evaluate_pair(
    coverage_baseline,
    count_only_candidate,
    "bounded-variant-enumeration-before-cap",
)
assert accepted is False
assert reason == "variant_coverage_no_verified_dimension_gain", reason

fanout_baseline = result(
    status="healthy",
    playable=1,
    returned=1,
    quality_heights=[480],
    effective_height=480,
    reachable_hosts=["stream.example"],
    announced_player_candidates=9,
    explored_player_requests=1,
    announced_quality_heights=[480,720,1080],
    fanout_state="announced-not-explored",
)
fanout_summary = mod.variant_coverage_summary(fanout_baseline)
assert fanout_summary["announcedPlayerCandidates"] == 9, fanout_summary
assert fanout_summary["exploredPlayerRequests"] == 1, fanout_summary
assert fanout_summary["announcedQualityHeights"] == [480,720,1080], fanout_summary
assert fanout_summary["fanoutStates"] == ["announced-not-explored"], fanout_summary

health_source = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")
assert "returned_quality_heights: returnedQualityHeights" in health_source

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
assert 'local_output_root = ROOT / "local-output"' in source
assert "local_output_root.mkdir(parents=True, exist_ok=True)" in source
assert "tempfile.mkdtemp(prefix=\"force-candidates-\", dir=local_output_root)" in source
assert "multiple concrete Force candidates require isolated hypothesis scheduling" not in source
assert "skipped_after_provider_winner" in source
assert "FIELD_BRAIN_LLM_FORCE_PORTFOLIO_WINNER" in source
assert "candidateOrdinal" in source
assert "eligible.sort(" in source
assert "skipped_after_provider_winner" in source

network = mod.network_summary({
    "tests": [{
        "fixture": {"label": "Fixture"},
        "network_observations": [
            {"stage": "provider_fetch", "host": "example.test", "method": "GET", "path_pattern": "/search", "status": 200, "ok": True},
            {"stage": "provider_fetch", "host": "example.test", "method": "GET", "path_pattern": "/search", "status": 200, "ok": True},
            {"stage": "detail_fetch", "host": "example.test", "method": "GET", "path_pattern": "/movie/1", "status": 200, "ok": True},
        ],
    }],
})
assert network == [
    {"fixture": "Fixture", "stage": "provider_fetch", "host": "example.test", "method": "GET", "path": "/search", "status": 200, "ok": True, "errorCode": ""},
    {"fixture": "Fixture", "stage": "detail_fetch", "host": "example.test", "method": "GET", "path": "/movie/1", "status": 200, "ok": True, "errorCode": ""},
], network

summary = mod.result_summary({
    "status": "no_streams",
    "score": 100,
    "evidence": {
        "provider_server_hosts": ["example.test"],
        "provider_server_http_statuses": [200],
    },
    "tests": [{
        "fixture": {"label": "Fixture"},
        "network_observations": [
            {"stage": "provider_fetch", "host": "example.test", "method": "GET", "path_pattern": "/search", "status": 200, "ok": True},
        ],
    }],
})
assert summary["providerHosts"] == ["example.test"], summary
assert summary["providerHttpStatuses"] == [200], summary
assert summary["networkTrace"][0]["path"] == "/search", summary

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
