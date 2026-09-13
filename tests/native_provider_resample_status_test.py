#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "gate_native_declared_provider_matrix.py"
spec = importlib.util.spec_from_file_location("native_matrix_gate", MODULE)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

assert gate.provider_status({"movie": "positive", "tv": "positive"}) == "FULL"
assert gate.provider_status({"movie": "positive", "tv": "technical_error"}) == "PARTIAL"
assert gate.provider_status({"movie": "positive", "tv": "catalog_miss"}) == "RESAMPLE"
assert gate.provider_status({"movie": "catalog_miss", "tv": "catalog_miss"}) == "RESAMPLE"
assert gate.provider_status({"movie": "technical_error", "tv": "catalog_miss"}) == "ZERO"
assert gate.provider_status({"movie": "technical_error", "tv": "technical_error"}) == "ZERO"

# A later positive sample proves the lane and wins over an earlier clean miss or
# transient technical error for capability classification.
assert gate.merge_outcome("catalog_miss", "positive") == "positive"
assert gate.merge_outcome("technical_error", "positive") == "positive"

payload = {
    "fixture": "rotated-title",
    "provider": "example",
    "mediaType": "movie",
    "enabled": True,
    "count": 0,
    "durationMs": 123,
    "state": "completed",
}
parsed = gate.parse_ios_result("FIELD_NATIVE_IOS_RESULT " + json.dumps(payload))
assert parsed == ("example", "movie", "catalog_miss"), parsed
payload["state"] = "timeout"
parsed = gate.parse_ios_result("FIELD_NATIVE_IOS_RESULT " + json.dumps(payload))
assert parsed == ("example", "movie", "technical_error"), parsed

print("native provider FULL/PARTIAL/RESAMPLE/ZERO status tests passed")
