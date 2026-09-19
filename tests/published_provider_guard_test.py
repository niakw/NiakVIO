#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_published_provider_guard.py"
spec = importlib.util.spec_from_file_location("published_guard", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

rows = [
    {
        "provider_id": "KEHFLIX",
        "semantic_type": "movie",
        "status": "playable_verified",
        "debug_stage": "provider_returned_streams",
        "raw": 3,
        "playable": 3,
        "verified": 3,
        "contradictions": 0,
        "duration_ms": 1200,
        "debug_fetches": [{"url": "https://secret.example/signed?token=never-persist"}],
    },
    {
        "provider_id": "streamzo",
        "semantic_type": "tv",
        "status": "wrong_content",
        "debug_stage": "provider_returned_wrong_content",
        "raw": 1,
        "playable": 1,
        "verified": 1,
        "contradictions": 1,
        "duration_ms": 800,
        "debug_fetches": [{"headers": {"Authorization": "Bearer secret"}}],
    },
]
summary = module.build_summary(["kehflix", "streamzo"], rows)
assert summary["providers"]["kehflix"]["status"] == "verified", summary
assert summary["providers"]["streamzo"]["status"] == "regression", summary
assert summary["allRequestedLanesVerified"] is False
serialized = json.dumps(summary).casefold()
for forbidden in ("https://", "secret", "authorization", "bearer", "token="):
    assert forbidden not in serialized, serialized

print("published provider live guard sanitizer tests passed")
