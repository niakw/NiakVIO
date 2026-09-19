#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_provider_census_status import render

report = {
    "provider_count": 3,
    "rows": [
        {"provider_id": "full", "semantic_type": "movie", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams"},
        {"provider_id": "full", "semantic_type": "tv", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams"},
        {"provider_id": "partial", "semantic_type": "movie", "status": "playable_verified", "verified": 1, "contradictions": 0, "debug_stage": "provider_returned_streams"},
        {"provider_id": "partial", "semantic_type": "tv", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_http_error"},
        {"provider_id": "zero", "semantic_type": "anime", "status": "no_streams", "verified": 0, "contradictions": 0, "debug_stage": "provider_network_zero_result"},
    ],
}

md = render(report, run_id="123", sha="abcdef0123456789")
assert "**1 FULL / 1 PARTIAL / 1 ZERO**" in md
assert "| `full` | **FULL** | movie, tv | movie, tv | movie=OK; tv=OK |" in md
assert "| `partial` | **PARTIAL** | movie, tv | movie |" in md
assert "tv=no_streams/provider_network_http_error" in md
assert "| `zero` | **ZERO** | anime | — | anime=no_streams/provider_network_zero_result |" in md
assert "run `123`" in md
assert "SHA `abcdef012345`" in md
assert md.count("| `full` |") == 1
assert md.count("| `partial` |") == 1
assert md.count("| `zero` |") == 1

print("provider census status markdown contract passed")
