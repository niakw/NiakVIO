#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "run_adaptive_quick_repair.py"
spec = importlib.util.spec_from_file_location("run_adaptive_quick_repair", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    registry_path = Path(tmp) / "candidates.json"
    registry_path.write_text(json.dumps({
        "candidates": [
            {"key": "aio:full", "canonical_id": "full", "metadata": {"supportedTypes": ["movie", "tv"]}},
            {"key": "published:full", "canonical_id": "full", "metadata": {"supportedTypes": ["movie", "tv"]}},
            {"key": "aio:partial", "canonical_id": "partial", "metadata": {"supportedTypes": ["movie", "tv"]}},
            {"key": "published:partial", "canonical_id": "partial", "metadata": {"supportedTypes": ["movie", "tv"]}},
        ]
    }), encoding="utf-8")
    report = {
        "results": [
            {
                "key": "aio:full", "status": "healthy", "score": 93,
                "evidence": {"streams_playable": 2, "payload_verified_streams": 2, "healthy_fixture_categories": ["movie", "tv"], "identity_contradiction_count": 0, "duration_identity_mismatch_count": 0},
            },
            {"key": "published:full", "status": "no_streams", "score": 10, "evidence": {}},
            {
                "key": "aio:partial", "status": "healthy", "score": 80,
                "evidence": {"streams_playable": 1, "payload_verified_streams": 1, "healthy_fixture_categories": ["tv"], "identity_contradiction_count": 0, "duration_identity_mismatch_count": 0},
            },
            {"key": "published:partial", "status": "no_streams", "score": 10, "evidence": {}},
        ]
    }
    resolved = module._discover_sibling_resolutions(registry_path, report)
    assert resolved == {"full": "aio:full"}, resolved

module._sibling_resolutions.clear()
module._sibling_resolutions.update({"full": "aio:full"})
assert module._sibling_aware_matching_profiles(
    {"key": "published:full", "canonical_id": "full"},
    {"status": "no_streams"},
    "function getStreams(){}",
    {},
) == []

print("healthy sibling resolution test passed")
