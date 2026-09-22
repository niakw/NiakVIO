#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_brain_learning_queue.py"
spec = importlib.util.spec_from_file_location("brain_learning_wave_merge", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def row(provider: str, profile: str, outcome: str) -> dict:
    return {
        "providerId": provider,
        "providerVersion": "*",
        "failureClass": "synthetic-gap",
        "signature": f"sig-{provider}",
        "profile": profile,
        "experimentVariant": 4,
        "experimentGeneration": 5,
        "attempts": 1,
        "successes": 0,
        "failures": 1,
        "consecutiveFailures": 1,
        "progresses": 0,
        "lastOutcome": outcome,
        "lastReason": "synthetic",
        "lastSeenAt": "2026-09-22T13:00:00+00:00",
        "memoryRole": "fair-share-exact-experiment-ledger",
        "executionObserved": True,
    }

a = row("family-a-provider", "runtime_response_salvage_v1", "rejected")
b = row("family-b-provider", "document_request_contract_mining_v1", "not_generated")
base = {
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {"schemaVersion": 1, "entries": []},
}

ab = mod.merge_wave_experiment_entries(base, [[a], [b]])
ba = mod.merge_wave_experiment_entries(base, [[b], [a]])

assert ab == ba, (ab, ba)
entries = ab["experimentMemory"]["entries"]
assert [x["providerId"] for x in entries] == ["family-a-provider", "family-b-provider"], entries
assert all(x["executionObserved"] is True for x in entries)

# A second wave must accumulate evidence through the same canonical merge,
# rather than replacing the first wave's provider-local memory.
a2 = dict(a)
a2["attempts"] = 2
a2["lastOutcome"] = "exploration_progress_nonpublishable"
next_state = mod.merge_wave_experiment_entries(ab, [[a2]])
by_provider = {x["providerId"]: x for x in next_state["experimentMemory"]["entries"]}
assert by_provider["family-a-provider"]["attempts"] == 3, by_provider
assert by_provider["family-b-provider"]["attempts"] == 1, by_provider

source = SCRIPT.read_text(encoding="utf-8")
for needle in (
    "causal_family_waves",
    "merge_wave_experiment_entries",
    "fastRepairHandoffParallelExecutionEnabled",
):
    assert needle in source, needle

# Regression for Repair->Learning Fast-Handoff initialization. The real handoff
# previously crashed before provider 1 because causal_waves read fair_handoff
# before the local had been assigned. Keep the runtime dependency order locked.
fair_assignment = source.index("fair_handoff = bool(handoff_priority) and not bool(args.provider)")
wave_assignment = source.index("causal_waves = causal_family_waves(order, batch_plan, max_parallel=4) if fair_handoff else []")
assert fair_assignment < wave_assignment, (fair_assignment, wave_assignment)

print("Brain Learning causal-wave memory merge tests passed")
