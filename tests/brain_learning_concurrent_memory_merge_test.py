#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge_brain_learning_latest_memory.py"
spec = importlib.util.spec_from_file_location(
    "brain_learning_latest_merge",
    SCRIPT,
)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def row(
    provider: str,
    *,
    attempts: int,
    failures: int,
    outcome: str = "rejected",
):
    return {
        "providerId": provider,
        "providerVersion": "*",
        "failureClass": "media_extraction_gap",
        "signature": "sig-" + provider,
        "profile": "player_media_extractor_v1",
        "positiveProgramFingerprint": "",
        "strategyImplementationFingerprint": "",
        "experimentVariant": 1,
        "experimentGeneration": 1,
        "capabilityStrategy": "mixed_embed_resolver",
        "observedPipelineStage": "terminal-media",
        "attempts": attempts,
        "successes": 0,
        "failures": failures,
        "consecutiveFailures": failures,
        "progresses": 0,
        "lastOutcome": outcome,
        "lastReason": "no_validated_improvement",
        "lastSeenAt": "2026-11-19T00:00:00+00:00",
        "memoryRole": "fair-share-exact-experiment-ledger",
        "executionObserved": True,
        "generationAttemptObserved": False,
    }


base = {
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [row("base", attempts=3, failures=3)],
    }
}

# Another family published while this cohort was running.
previous = {
    "generatedAt": "2026-11-19T00:02:00+00:00",
    "marker": "newer-published-state",
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [
            row("base", attempts=3, failures=3),
            row("parallel-a", attempts=1, failures=1),
        ],
    }
}

# This cohort started from base. The unchanged base row must not be counted
# again; only parallel-b is new.
current = {
    "generatedAt": "2026-11-19T00:01:00+00:00",
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [
            row("base", attempts=3, failures=3),
            row("parallel-b", attempts=1, failures=1),
        ],
    },
}
merged = mod.merge_latest(base, previous, current, max_entries=100)
by_provider = {
    item["providerId"]: item
    for item in merged["experimentMemory"]["entries"]
}
assert set(by_provider) == {"base", "parallel-a", "parallel-b"}, by_provider
assert by_provider["base"]["attempts"] == 3, by_provider["base"]
assert by_provider["base"]["failures"] == 3, by_provider["base"]
assert merged["concurrentMemoryMerge"]["deltaRows"] == 1
assert merged["publicationAllowed"] is False
assert merged["productionWritesAllowed"] is False
assert merged["marker"] == "newer-published-state", merged
assert merged["concurrentMemoryMerge"]["metadataSource"] == "previous", merged

# Same exact experiment advances independently after the shared base. Apply
# only this cohort's +1 delta on top of a concurrently published +2 delta.
previous2 = {
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [row("base", attempts=5, failures=5)],
    }
}
current2 = {
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [row("base", attempts=4, failures=4)],
    }
}
merged2 = mod.merge_latest(base, previous2, current2, max_entries=100)
got = merged2["experimentMemory"]["entries"][0]
assert got["attempts"] == 6, got
assert got["failures"] == 6, got
assert merged2["concurrentMemoryMerge"]["deltaRows"] == 1

# A telemetry-only delta must survive a concurrent publish without becoming
# another experiment attempt.
telemetry = {
    "schemaVersion": 1,
    "providerRequestCount": 57,
    "successfulProviderRequestCount": 12,
    "networkFailureCount": 3,
    "statusBuckets": {"2xx": 12, "3xx": 0, "4xx": 42, "5xx": 0, "network": 3},
    "methods": ["GET", "POST"],
    "stages": ["episode"],
    "deepestStage": "episode",
    "responseKinds": ["html", "json"],
    "proofAuthority": False,
    "publicationAuthority": False,
    "rawAddressRetained": False,
    "headersRetained": False,
    "bodyRetained": False,
}
base3_row = row("telemetry", attempts=7, failures=3)
base3 = {
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [base3_row],
    }
}
previous3_row = row("telemetry", attempts=9, failures=5)
previous3 = {
    "generatedAt": "2026-11-19T00:03:00+00:00",
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [previous3_row],
    },
}
current3_row = row("telemetry", attempts=7, failures=3)
current3_row["networkExecutionSummary"] = telemetry
current3 = {
    "generatedAt": "2026-11-19T00:02:30+00:00",
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [current3_row],
    },
}
merged3 = mod.merge_latest(base3, previous3, current3, max_entries=100)
got3 = merged3["experimentMemory"]["entries"][0]
assert got3["attempts"] == 9, got3
assert got3["failures"] == 5, got3
assert got3["networkExecutionSummary"] == telemetry, got3
assert merged3["concurrentMemoryMerge"]["deltaRows"] == 0
assert merged3["concurrentMemoryMerge"]["telemetryDeltaRows"] == 1

# No delta means identity merge: historical counters cannot amplify.
same = mod.merge_latest(base, previous, base, max_entries=100)
same_by_provider = {
    item["providerId"]: item
    for item in same["experimentMemory"]["entries"]
}
assert same_by_provider["base"]["attempts"] == 3, same_by_provider["base"]
assert same["concurrentMemoryMerge"]["deltaRows"] == 0

print(
    "Brain Learning concurrent three-way experiment-memory merge "
    "contract passed"
)
