#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "brain_repair_runtime.py"
spec = importlib.util.spec_from_file_location("brain_repair_runtime_variant_prior", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    status = root / "status.json"
    sharded = root / "sharded.json"
    status.write_text(json.dumps({
        "providers": [
            {"provider": "demo", "status": "FULL OK", "currentVerifiedLanes": ["movie"]},
            {"provider": "clean", "status": "FULL OK", "currentVerifiedLanes": ["movie"]},
        ]
    }), encoding="utf-8")
    sharded.write_text(json.dumps({
        "runId": "12345",
        "rows": [
            {
                "provider_id": "demo",
                "semantic_type": "movie",
                "announced_player_candidates": 2,
                "announced_variant_candidates": 19,
                "explored_player_requests": 8,
                "streams_returned": 2,
                "variant_fanout_state": "returned-subset",
                "announced_quality_heights": [480, 720, 1080, 2160],
            },
            {
                "provider_id": "clean",
                "semantic_type": "movie",
                "announced_player_candidates": 2,
                "announced_variant_candidates": 2,
                "explored_player_requests": 2,
                "streams_returned": 2,
                "variant_fanout_state": "fanout-observed",
            },
        ],
    }), encoding="utf-8")
    old_status, old_sharded = mod.CENSUS_STATUS_PATH, mod.CENSUS_SHARDED_PATH
    try:
        mod.CENSUS_STATUS_PATH = status
        mod.CENSUS_SHARDED_PATH = sharded
        demo = mod._census_prior("demo")
        debt = demo["dynamicVariantCoverage"]
        assert debt["failureClass"] == "variant_coverage_gap", debt
        assert debt["repairTargetAuthority"] is True
        assert debt["proofAuthority"] is False
        assert debt["sourceRunId"] == "12345"
        assert debt["maxAnnouncedVariantCandidates"] == 19
        assert debt["maxReturnedStreams"] == 2
        assert debt["lanes"][0]["announcedQualityHeights"] == [480, 720, 1080, 2160]
        clean = mod._census_prior("clean")
        assert "dynamicVariantCoverage" not in clean, clean
    finally:
        mod.CENSUS_STATUS_PATH, mod.CENSUS_SHARDED_PATH = old_status, old_sharded

print("Brain dynamic variant census prior contract passed")
