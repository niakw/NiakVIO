#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("quick_yield", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

hierarchical = {
    "fetches": [
        {
            "url": "https://coflix.example/ajax/episode/player",
            "response_url": "https://coflix.example/ajax/episode/player",
            "declared_player_candidate_count": 2,
            "declared_url_player_candidate_count": 2,
            "declared_indexed_player_candidate_count": 0,
            "declared_player_hosts": ["one.test", "two.test"],
            "declared_quality_heights": [480],
        },
        {
            "url": "https://one.test/player/1",
            "response_url": "https://one.test/player/1",
            "declared_player_candidate_count": 10,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 10,
            "declared_player_hosts": [],
            "declared_quality_heights": [720, 1080],
        },
        {
            "url": "https://two.test/player/2",
            "response_url": "https://two.test/player/2",
            "declared_player_candidate_count": 9,
            "declared_url_player_candidate_count": 0,
            "declared_indexed_player_candidate_count": 9,
            "declared_player_hosts": [],
            "declared_quality_heights": [1080],
        },
    ]
}
summary = mod._variant_fanout_summary(hierarchical, 8)
assert summary["announced_player_candidates"] == 2, summary
assert summary["announced_variant_candidates"] == 19, summary
assert summary["explored_player_requests"] == 2, summary
assert summary["explored_player_hosts"] == ["one.test", "two.test"], summary
assert summary["announced_quality_heights"] == [480, 720, 1080], summary
assert summary["variant_fanout_state"] == "returned-subset", summary

index_only = {
    "fetches": [{
        "url": "https://coflix.example/title",
        "response_url": "https://coflix.example/title",
        "declared_player_candidate_count": 19,
        "declared_url_player_candidate_count": 0,
        "declared_indexed_player_candidate_count": 19,
        "declared_player_hosts": [],
        "declared_quality_heights": [480, 720, 1080],
    }]
}
summary = mod._variant_fanout_summary(index_only, 8)
assert summary["announced_variant_candidates"] == 19, summary
assert summary["explored_player_requests"] == 0, summary
assert summary["variant_fanout_state"] == "returned-subset", summary

probe = (ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs").read_text(encoding="utf-8")
assert "extractResponseVariantHints" in probe
assert "declared_player_candidate_count" in probe
assert "declared_player_hosts" in probe
assert "declared_quality_heights" in probe

print("provider quick-yield variant fan-out contract passed")
