#!/usr/bin/env python3
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

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

# Execute the real run_single integration path with a synthetic probe result.
# This catches stale/undefined fan-out locals that helper-only tests cannot see.
original_run = mod.subprocess.run
try:
    mod.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
        stdout='{"playable_stream_count":1,"raw_stream_count":1,"content_verified_count":1,"identity_verified_count":1,"identity_contradiction_count":0,"runtime_error":null,"duration_ms":1,"streams":[],"debug":{"fetches":[]}}\n',
        stderr="",
        returncode=0,
    )
    run_single_result = mod.run_single({
        "provider_id": "demo",
        "provider_name": "Demo",
        "semantic_type": "movie",
        "filename": "providers/demo.js",
        "fixture": {"title": "Fixture", "mediaType": "movie", "tmdbId": "1"},
    })
finally:
    mod.subprocess.run = original_run
assert run_single_result["streams_returned"] == 1, run_single_result
assert run_single_result["variant_fanout_state"] == "not-observed", run_single_result

probe_path = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
syntax = subprocess.run(["node", "--check", str(probe_path)], cwd=ROOT, text=True, capture_output=True, check=False)
assert syntax.returncode == 0, syntax.stdout + syntax.stderr
probe = probe_path.read_text(encoding="utf-8")
assert "extractResponseVariantHints" in probe
assert "declared_player_candidate_count" in probe
assert "declared_player_hosts" in probe
assert "declared_quality_heights" in probe

print("provider quick-yield variant fan-out contract passed")
