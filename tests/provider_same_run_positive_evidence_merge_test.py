#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "same_run_merge",
    ROOT / "scripts" / "merge_provider_same_run_positive_evidence.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

base = {
    "rows": [
        {
            "provider_id": "alpha",
            "semantic_type": "movie",
            "status": "no_streams",
            "debug_stage": "provider_network_zero_result",
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
            "samples": [{"fixture_title": "Old", "fixture": {"tmdbId": "1", "mediaType": "movie"}}],
        },
        {
            "provider_id": "beta",
            "semantic_type": "movie",
            "status": "playable_verified",
            "debug_stage": "provider_returned_streams",
            "raw": 3,
            "playable": 2,
            "verified": 2,
            "contradictions": 0,
        },
        {
            "provider_id": "gamma",
            "semantic_type": "tv",
            "status": "wrong_content",
            "debug_stage": "provider_returned_streams",
            "raw": 1,
            "playable": 1,
            "verified": 0,
            "contradictions": 1,
        },
    ]
}
supplement = {
    "rows": [
        {
            "provider_id": "alpha",
            "semantic_type": "movie",
            "status": "playable_verified",
            "debug_stage": "provider_returned_streams",
            "raw": 2,
            "playable": 2,
            "verified": 2,
            "contradictions": 0,
            "samples": [{"fixture_title": "Proof", "fixture": {"tmdbId": "2", "mediaType": "movie"}}],
        },
        {
            "provider_id": "beta",
            "semantic_type": "movie",
            "status": "no_streams",
            "debug_stage": "provider_network_zero_result",
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
        },
        {
            "provider_id": "gamma",
            "semantic_type": "tv",
            "status": "wrong_content",
            "debug_stage": "provider_returned_streams",
            "raw": 4,
            "playable": 4,
            "verified": 4,
            "contradictions": 1,
        },
        {
            "provider_id": "delta",
            "semantic_type": "anime",
            "status": "candidate_ok",
            "debug_stage": "provider_returned_streams",
            "raw": 1,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
        },
    ]
}

merged, applied = mod.merge(base, supplement)
by_key = {(r["provider_id"], r["semantic_type"]): r for r in merged["rows"]}

assert by_key[("alpha", "movie")]["verified"] == 2
assert {s["fixture_title"] for s in by_key[("alpha", "movie")]["samples"]} == {"Old", "Proof"}
assert by_key[("beta", "movie")]["verified"] == 2
assert by_key[("gamma", "tv")]["contradictions"] == 1
assert by_key[("gamma", "tv")]["verified"] == 0
assert by_key[("delta", "anime")]["raw"] == 1

assert merged["verified_providers"] == ["alpha", "beta"]
assert merged["playable_providers"] == ["alpha", "beta", "gamma"]
assert merged["raw_providers"] == ["alpha", "beta", "delta", "gamma"]
assert merged["accepted_playable_providers"] == ["alpha", "beta"]
assert merged["wrong_content_providers"] == ["gamma"]
assert {row["provider"] for row in applied} == {"alpha", "delta"}

print("same-run positive evidence monotonic merge test passed")
