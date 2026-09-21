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
        "old-red": {"owner": "LEARN", "status": "pending", "reason": "target-not-verified", "repairObservations": 2},
        "resolved-now": {"owner": "LEARN", "status": "pending", "reason": "target-not-verified", "repairObservations": 1},
    },
}
summary = {
    "targetedProviders": ["NEW_RED", "resolved-now", "PARTIAL_GREEN"],
    "verifiedProviders": ["resolved-now", "PARTIAL_GREEN"],
    "lostUpstreamPositivePairs": [["NEW_RED", "movie"], ["NEW_RED", "tv"], ["PARTIAL_GREEN", "tv"]],
    "maxAttemptsPerTask": 3,
}
merged = module.merge_summary(base, summary, run_id="12345")
assert set(merged["providers"]) == {"new-red", "old-red", "partial-green"}, merged
row = merged["providers"]["new-red"]
assert row["reason"] == "lost-upstream-positive" and row["mediaTypes"] == ["movie", "tv"]
partial = merged["providers"]["partial-green"]
assert partial["reason"] == "lost-upstream-positive" and partial["mediaTypes"] == ["tv"]
assert merged["providers"].get("resolved-now") is None
assert row["lastRepairRunId"] == "12345" and row["publicationAllowed"] is False
serialized = json.dumps(merged).casefold()
for forbidden in ("http://", "https://", "authorization", "cookie", "requestbody"):
    assert forbidden not in serialized
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "handoff.json"
    module.write(path, merged)
    assert module.load(path)["providerCount"] == 3


fast_summary = {
    "selectedProviders": ["EXHAUSTED", "remaining-one", "fixed-now"],
    "validatedProviders": ["fixed-now"],
    "brainDeferredLearningProviders": ["EXHAUSTED"],
    "brainRemainingProviders": ["remaining-one"],
    "learnHandoffProviders": ["EXHAUSTED", "remaining-one"],
}
fast = module.merge_summary({"schemaVersion":1,"providers":{}}, fast_summary, run_id="777")
assert set(fast["providers"]) == {"exhausted", "remaining-one"}, fast
assert fast["providers"]["exhausted"]["reason"] == "brain-strategy-exhausted", fast
assert fast["providers"]["remaining-one"]["reason"] == "brain-unresolved", fast
assert "fixed-now" not in fast["providers"], fast

print("provider repair -> LEARN lane-aware handoff tests passed")
