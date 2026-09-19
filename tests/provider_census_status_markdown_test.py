#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_provider_census_status import build_status_rows, render
from update_provider_census_proof_history import NETWORK_STAGES, TECHNICAL_STAGES

report = {
    "provider_count": 5,
    "rows": [
        {"provider_id": "full", "semantic_type": "movie", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams", "sample_count": 1},
        {"provider_id": "full", "semantic_type": "tv", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams", "sample_count": 1},
        {"provider_id": "partial", "semantic_type": "movie", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams", "sample_count": 1},
        {"provider_id": "partial", "semantic_type": "tv", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_http_error", "sample_count": 1},
        {"provider_id": "no-proof", "semantic_type": "anime", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_zero_result", "sample_count": 4, "samples": []},
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

rows = {row["provider"]: row for row in build_status_rows(report, history, baseline)}
assert rows["full"]["status"] == "FULL OK"
assert rows["partial"]["status"] == "PARTIAL OK"
assert rows["no-proof"]["status"] == "NO PROOF"
assert rows["network-blocked"]["status"] == "PROVIDER NETWORK BLOCKED"
assert rows["broken"]["status"] == "PROVIDER JS BROKEN"
assert "provider_network_http_error" in NETWORK_STAGES
assert "provider_network_exception" in NETWORK_STAGES
assert "timeout" in NETWORK_STAGES
assert not (NETWORK_STAGES & TECHNICAL_STAGES)
assert rows["carried-green"]["status"] == "FULL OK"
assert rows["carried-green"]["testedThisRun"] is False

md = render(report, run_id="123", sha="abcdef0123456789", history=history, baseline=baseline)
assert "🟢 **FULL OK**" in md
assert "🟡 **PARTIAL OK**" in md
assert "🔵 **NO PROOF**" in md
assert "🟤 **PROVIDER NETWORK BLOCKED**" in md
assert "🟠 **PROVIDER JS BROKEN**" in md
assert "**no-proof**" in md
assert "provider_network_zero_result" in md
assert "catalogue miss / missing current proof" in md
assert "carried" in md
assert "run 123" in md
assert "SHA abcdef012345" in md

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

print("provider census status/state-machine markdown contract passed")
