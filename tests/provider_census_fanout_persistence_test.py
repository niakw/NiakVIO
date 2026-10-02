#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("quick_yield", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

debug = {
    "model": {"official_site": "https://provider.test"},
    "fetches": [
        {
            "url": "https://provider.test/ajax/player",
            "response_url": "https://provider.test/ajax/player",
            "status": 200,
            "declared_player_candidate_count": 2,
            "declared_url_player_candidate_count": 2,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["player-a.test", "player-b.test"],
            "declared_quality_heights": [480, 720, 1080],
        },
        {
            "url": "https://player-a.test/e/root",
            "response_url": "https://player-a.test/e/root",
            "status": 200,
            "declared_player_candidate_count": 10,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 10,
            "declared_player_hosts": [],
            "declared_quality_heights": [480, 720, 1080, 2160],
        },
        {
            "url": "https://player-b.test/e/root",
            "response_url": "https://player-b.test/e/root",
            "status": 200,
            "declared_player_candidate_count": 9,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 9,
            "declared_player_hosts": [],
            "declared_quality_heights": [480, 720, 1080, 2160],
        },
    ]
}
summary = mod._variant_fanout_summary(debug, 8)
assert summary["announced_player_candidates"] == 2, summary
assert summary["announced_player_hosts"] == ["player-a.test", "player-b.test"], summary
assert summary["announced_variant_candidates"] == 19, summary
assert summary["explored_player_requests"] == 2, summary
assert summary["explored_player_hosts"] == ["player-a.test", "player-b.test"], summary
assert summary["announced_quality_heights"] == [480, 720, 1080, 2160], summary
assert summary["streams_returned"] == 8, summary
assert summary["variant_fanout_state"] == "returned-subset", summary

complete = mod._variant_fanout_summary(debug, 19)
assert complete["variant_fanout_state"] == "fanout-observed", complete

probe = (ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs").read_text(encoding="utf-8")
for needle in (
    "extractResponseVariantHints",
    "declared_player_candidate_count",
    "declared_player_hosts",
    "declared_quality_heights",
):
    assert needle in probe, f"quick probe missing fanout persistence field: {needle}"

health = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")
assert "streams.length < announcedVariantCandidates" in health
assert "variantFanoutState = 'returned-subset'" in health

print("provider census fan-out persistence passed")
