#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

import runtime_repair  # noqa: E402

with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    provider = stage / "providers" / "demo.js"
    provider.parent.mkdir(parents=True)
    provider.write_text(
        "module.exports={getStreams:async function(){return []}};\n",
        encoding="utf-8",
    )
    candidate = {
        "key": "test:demo",
        "canonical_id": "demo",
        "upstream_id": "demo",
        "source": "test",
        "local_path": "providers/demo.js",
        "metadata": {
            "id": "demo",
            "name": "Demo",
            "baseUrl": "https://demo.example",
            "supportedTypes": ["movie"],
        },
        "local_patches": [],
    }
    failing = {
        "status": "no_streams",
        "tests": [{"failure_class": "content_lookup_completed_no_streams"}],
        "evidence": {"streams_returned": 0, "streams_playable": 0},
    }
    healthy = {
        "status": "healthy",
        "tests": [],
        "evidence": {"streams_returned": 1, "streams_playable": 1},
    }
    source = provider.read_text(encoding="utf-8")
    assert "adaptive_runtime_recovery" in runtime_repair.matching_profiles(
        candidate, failing, source
    )
    assert "adaptive_runtime_recovery" not in runtime_repair.matching_profiles(
        candidate, healthy, source
    )

    repaired, error = runtime_repair.create_repair_candidate(
        stage, candidate, "adaptive_runtime_recovery", 1
    )
    assert error is None, error
    assert repaired is not None
    target = stage / repaired["local_path"]
    assert target.is_file()
    assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V1" in target.read_text(encoding="utf-8")
    assert repaired["runtime_repair"]["profile"] == ""
    assert repaired["runtime_repair"]["strategy"] == "adaptive_runtime_recovery"

print("adaptive runtime repair tests passed")
