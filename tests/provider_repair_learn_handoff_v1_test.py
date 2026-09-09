#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_repair_learn_handoff_v1.py"
spec = importlib.util.spec_from_file_location("handoff", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = {
    "schemaVersion": 1,
    "providers": {
        "old-red": {
            "owner": "LEARN",
            "status": "pending",
            "reason": "target-not-verified",
            "repairObservations": 2,
        },
        "resolved-now": {
            "owner": "LEARN",
            "status": "pending",
            "reason": "target-not-verified",
            "repairObservations": 1,
        },
    },
}
summary = {
    "targetedProviders": ["NEW_RED", "resolved-now"],
    "verifiedProviders": ["resolved-now"],
    "lostUpstreamPositivePairs": [["NEW_RED", "movie"], ["NEW_RED", "tv"]],
    "maxAttemptsPerTask": 3,
}
merged = module.merge_summary(base, summary, run_id="12345")
assert set(merged["providers"]) == {"new-red", "old-red"}, merged
row = merged["providers"]["new-red"]
assert row["owner"] == "LEARN"
assert row["reason"] == "lost-upstream-positive"
assert row["mediaTypes"] == ["movie", "tv"]
assert row["lastRepairRunId"] == "12345"
assert row["repairObservations"] == 1
assert row["publicationAllowed"] is False
serialized = json.dumps(merged).casefold()
for forbidden in ("http://", "https://", "authorization", "cookie", "requestbody"):
    assert forbidden not in serialized

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "handoff.json"
    module.write(path, merged)
    loaded = module.load(path)
    assert loaded["providerCount"] == 2

print("provider repair -> LEARN handoff tests passed")
