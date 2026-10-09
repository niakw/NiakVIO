#!/usr/bin/env python3
"""Fast Brain stale run import: strict negative-memory and authority boundary."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "fast_stale_bridge", ROOT / "scripts/merge_stale_fast_repair_memory.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def row(pid, outcome, failures=1, observed=True):
    return {
        "providerId": pid, "signature": "signed-current-failure",
        "profile": "route_transition_graph_v2",
        "experimentVariant": 4, "experimentGeneration": 2,
        "lastOutcome": outcome, "lastReason": "no-terminal",
        "executionObserved": observed, "failures": failures,
        "consecutiveFailures": failures, "successes": 0,
    }

baseline = {"schemaVersion": 1, "entries": [row("4khdhub", "rejected", 2)]}
incoming = {"schemaVersion": 1, "entries": [
    row("4khdhub", "rejected", 3),
    row("animevostfr", "rejected", 4),
    row("animekai", "accepted", 99),
    row("animesama-co", "rejected", 99, observed=False),
    row("unrelated", "rejected", 12),
]}
out, stats = module.merge_memory(
    baseline, incoming, {"4khdhub", "animevostfr", "animekai", "animesama-co"}
)
assert stats == {"inspected": 5, "accepted": 2, "inserted": 1}, stats
assert len(out["entries"]) == 2, out
old = next(item for item in out["entries"] if item["providerId"] == "4khdhub")
assert old["failures"] == 3 and old["lastOutcome"] == "rejected"
new = next(item for item in out["entries"] if item["providerId"] == "animevostfr")
assert new["failures"] == 4

# An accepted current-byte result must never regress to a stale negative.
positive = {"schemaVersion": 1, "entries": [row("4khdhub", "accepted", 1)]}
current, _ = module.merge_memory(positive, incoming, {"4khdhub"})
assert current["entries"][0]["lastOutcome"] == "accepted", current
assert current["entries"][0]["failures"] == 3
assert incoming["entries"][0]["failures"] == 3, "no mutation of source artifact"
for invalid in ({"schemaVersion": 3, "entries": []}, {"schemaVersion": 1, "entries": {}}):
    try:
        module.merge_memory(baseline, invalid, {"4khdhub"})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid stale artifact schema accepted")
print("Brain Fast stale evidence import contract passed")
