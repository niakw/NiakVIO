#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_provider_census_status import build_status_rows, render
from update_provider_census_proof_history import NETWORK_STAGES, TECHNICAL_STAGES

report = {
    "provider_count": 9,
    "rows": [
        {"provider_id": "full", "semantic_type": "movie", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams", "sample_count": 1},
        {"provider_id": "full", "semantic_type": "tv", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams", "sample_count": 1},
        {"provider_id": "partial", "semantic_type": "movie", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams", "sample_count": 1},
        {"provider_id": "partial", "semantic_type": "tv", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_http_error", "sample_count": 1},
        {"provider_id": "no-proof", "semantic_type": "anime", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_zero_result", "debug_progress_stage": "lookup_only", "sample_count": 4, "samples": []},
        {"provider_id": "chain", "semantic_type": "movie", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_zero_result", "debug_progress_stage": "chain_reached", "sample_count": 1, "samples": []},
        {"provider_id": "candidate", "semantic_type": "anime", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_zero_result", "debug_progress_stage": "lookup_only", "sample_count": 1, "samples": []},
        {"provider_id": "route", "semantic_type": "movie", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_zero_result", "debug_progress_stage": "lookup_only", "sample_count": 1, "samples": []},
        {"provider_id": "waf", "semantic_type": "movie", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_waf_challenge", "debug_progress_stage": "lookup_only", "sample_count": 1},
        {"provider_id": "network-blocked", "semantic_type": "movie", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_http_error", "sample_count": 2},
        {"provider_id": "broken", "semantic_type": "movie", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "gate_runtime_plan_missing", "sample_count": 1},
    ],
}
history = {
    "providers": {
        "no-proof": {"lanes": {"anime": {"proofs": [], "misses": [{"fixture": {"slug": "a"}}]}}},
        "network-blocked": {"lanes": {"movie": {"proofs": [], "misses": [], "consecutiveTechnicalRuns": 9, "consecutiveNetworkRuns": 3}}},
        "broken": {"lanes": {"movie": {"proofs": [], "misses": [], "consecutiveTechnicalRuns": 1}}},
    }
}
candidate_evidence = {"ciEvidence": {"run87_reconstruction": {"runId": "34309729426", "scope": "reconstruction-candidate", "verifiedProviders": ["candidate"]}}}

provider_overrides = {
    "provider_patches": {
        "route": {
            "live_route_gate": {
                "completion_state": "declared-types-qualified",
                "required_types": ["movie"],
                "validated_types": ["movie"],
                "missing_types": [],
                "live_validated_route_count": 3,
                "provider_request_count": 9,
            }
        }
    }
}

baseline = {
    "providers": [
        {
            "provider": "carried-green",
            "status": "FULL OK",
            "color": "🟢",
            "declaredLanes": ["anime"],
            "currentVerifiedLanes": ["anime"],
            "historicalProof": ["anime: Known"],
            "latestLaneVerdicts": ["anime=OK"],
            "dominantIssue": "none",
            "searchProgress": ["anime: retained"],
            "action": "protect + replay retained proof",
            "brainCheckRequired": False,
            "testedThisRun": True,
        }
    ]
}

rows = {row["provider"]: row for row in build_status_rows(report, history, baseline, candidate_evidence, provider_overrides)}
assert rows["full"]["status"] == "FULL OK"
assert rows["partial"]["status"] == "PARTIAL OK"
assert rows["no-proof"]["status"] == "NO PROOF"
assert rows["chain"]["status"] == "CHAIN REACHED"
assert rows["candidate"]["status"] == "CANDIDATE OK"
assert rows["candidate"]["candidateProof"] == ["run 34309729426"]
assert rows["route"]["status"] == "ROUTE PROVEN"
assert rows["route"]["routeProof"] == ["3 live routes / movie"]
assert rows["waf"]["status"] == "PROVIDER WAF/ANTIBOT"
assert rows["network-blocked"]["status"] == "PROVIDER NETWORK BLOCKED"
assert rows["broken"]["status"] == "PROVIDER JS BROKEN"
assert rows["full"]["brainCheckRequired"] is False
assert rows["partial"]["brainCheckRequired"] is False
assert rows["waf"]["brainCheckRequired"] is True
assert rows["waf"]["repairEligible"] is False
assert rows["broken"]["repairEligible"] is True
assert rows["route"]["repairEligible"] is True
assert "provider_waf_challenge" in NETWORK_STAGES
assert "provider_network_http_error" in NETWORK_STAGES
assert "provider_network_exception" in NETWORK_STAGES
assert "timeout" in NETWORK_STAGES
assert not (NETWORK_STAGES & TECHNICAL_STAGES)
assert rows["carried-green"]["status"] == "FULL OK"
assert rows["carried-green"]["testedThisRun"] is False

md = render(report, run_id="123", sha="abcdef0123456789", history=history, baseline=baseline, candidate_evidence=candidate_evidence, provider_overrides=provider_overrides)
assert "🟢 **FULL OK**" in md
assert "🟡 **PARTIAL OK**" in md
assert "🟦 **CANDIDATE OK**" in md
assert "🟪 **ROUTE PROVEN**" in md
assert "3 live routes / movie" in md
assert "🔵 **NO PROOF**" in md
assert "🟣 **CHAIN REACHED**" in md
assert "🟫 **PROVIDER WAF/ANTIBOT**" in md
assert "🟤 **PROVIDER NETWORK BLOCKED**" in md
assert "🟠 **PROVIDER JS BROKEN**" in md
assert "**no-proof**" in md
assert "provider_network_zero_result" in md
assert "Corpus progress" in md
assert "Evidence depth" in md
assert "Candidate proof" in md
assert "Route proof" in md
assert "CANDIDATE OK preserves verified playback from a reconstruction candidate" in md
assert "PARTIAL OK still requires at least one current verified playable lane" in md
assert "carried" in md
assert "run 123" in md
assert "SHA abcdef012345" in md
assert "Symptomatic providers: **7**" in md
assert "automated repair queue: **6**" in md
assert "environment-only/WAF: **1**" in md

# A previously proven fixture that is explicitly replayed and now returns a
# clean zero is a provider regression, not NO PROOF.
regression_report = {
    "provider_count": 1,
    "rows": [{
        "provider_id": "reg",
        "semantic_type": "movie",
        "status": "no_streams",
        "verified": 0,
        "contradictions": 0,
        "debug_stage": "provider_network_zero_result",
        "sample_count": 1,
        "samples": [{
            "fixture": {"slug": "known", "tmdbId": "1", "mediaType": "movie"},
            "status": "no_streams",
            "debug_stage": "provider_network_zero_result",
        }],
    }],
}
regression_history = {
    "providers": {
        "reg": {"lanes": {"movie": {"proofs": [{
            "fixture": {"slug": "known", "tmdbId": "1", "mediaType": "movie"}
        }]}}}
    }
}
row = build_status_rows(regression_report, regression_history)[0]
assert row["status"] == "REGRESSION PROVIDER", row


# Real DATA regression guard: these providers previously appeared as NO PROOF
# even though their provider-local live route gates already covered every
# declared semantic lane. Preserve that distinction across renderer refactors.
actual_overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
route_proven_real_provider_ids = {
    "4khdhub": {"movie", "tv"},
    "animetsu": {"anime"},
    "showbox": {"movie", "tv"},
}
for pid, expected_lanes in route_proven_real_provider_ids.items():
    patch = actual_overrides["provider_patches"][pid]
    gate = patch["live_route_gate"]
    assert gate["completion_state"] == "declared-types-qualified", (pid, gate)
    assert set(gate["required_types"]) == expected_lanes, (pid, gate)
    assert set(gate["validated_types"]) == expected_lanes, (pid, gate)
    assert gate.get("missing_types") == [], (pid, gate)
    assert int(gate.get("live_validated_route_count") or 0) > 0, (pid, gate)

print("provider census status/state-machine markdown contract passed")
