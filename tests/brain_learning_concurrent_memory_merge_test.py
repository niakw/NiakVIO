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
    parent_sha: str = "",
    parent_authority: str = "",
):
    return {
        "providerId": provider,
        "providerVersion": "*",
        "parentArtifactSha256": parent_sha,
        "parentAuthority": parent_authority,
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

# A later diagnostics-only replay may add candidate-minus-parent delta while
# keeping the absolute summary unchanged. The delta must survive concurrent
# publication without incrementing counters.
delta_only = {
    "schemaVersion": 1,
    "providerRequestDelta": 24,
    "successfulProviderRequestDelta": 6,
    "networkFailureDelta": 1,
    "statusBucketDelta": {"2xx": 6, "3xx": 0, "4xx": 17, "5xx": 0, "network": 1},
    "newMethods": ["POST"],
    "newStages": ["episode"],
    "newResponseKinds": ["html"],
    "parentDeepestStage": "content_lookup",
    "candidateDeepestStage": "episode",
    "stageRankDelta": 1,
    "stageAdvanced": True,
    "proofAuthority": False,
    "publicationAuthority": False,
    "rawAddressRetained": False,
    "headersRetained": False,
    "bodyRetained": False,
}
base4_row = row("telemetry", attempts=7, failures=3)
base4_row["networkExecutionSummary"] = telemetry
base4 = {"experimentMemory": {"schemaVersion": 1, "entries": [base4_row]}}
previous4_row = row("telemetry", attempts=9, failures=5)
previous4_row["networkExecutionSummary"] = telemetry
previous4 = {
    "generatedAt": "2026-11-19T00:04:00+00:00",
    "experimentMemory": {"schemaVersion": 1, "entries": [previous4_row]},
}
current4_row = row("telemetry", attempts=7, failures=3)
current4_row["networkExecutionSummary"] = telemetry
current4_row["networkExecutionDelta"] = delta_only
current4 = {
    "generatedAt": "2026-11-19T00:03:30+00:00",
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {"schemaVersion": 1, "entries": [current4_row]},
}
merged4 = mod.merge_latest(base4, previous4, current4, max_entries=100)
got4 = merged4["experimentMemory"]["entries"][0]
assert got4["attempts"] == 9, got4
assert got4["failures"] == 5, got4
assert got4["networkExecutionSummary"] == telemetry, got4
assert got4["networkExecutionDelta"] == delta_only, got4
assert merged4["concurrentMemoryMerge"]["deltaRows"] == 0
assert merged4["concurrentMemoryMerge"]["telemetryDeltaRows"] == 1

# Same provider/profile/signature on different parent bytes are distinct
# experiments and must never coalesce during concurrent family publication.
parent_a = "a" * 64
parent_b = "b" * 64
parent_base = {
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [
            row(
                "same-provider",
                attempts=1,
                failures=1,
                parent_sha=parent_a,
                parent_authority="published-exact-current-bytes",
            )
        ],
    }
}
parent_previous = {
    "generatedAt": "2026-11-19T00:05:00+00:00",
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [
            row(
                "same-provider",
                attempts=1,
                failures=1,
                parent_sha=parent_a,
                parent_authority="published-exact-current-bytes",
            )
        ],
    },
}
parent_current = {
    "generatedAt": "2026-11-19T00:05:01+00:00",
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [
            row(
                "same-provider",
                attempts=1,
                failures=1,
                parent_sha=parent_a,
                parent_authority="published-exact-current-bytes",
            ),
            row(
                "same-provider",
                attempts=1,
                failures=1,
                parent_sha=parent_b,
                parent_authority="published-exact-current-bytes",
            ),
        ],
    },
}
parent_merged = mod.merge_latest(
    parent_base, parent_previous, parent_current, max_entries=100
)
parent_rows = [
    item
    for item in parent_merged["experimentMemory"]["entries"]
    if item["providerId"] == "same-provider"
]
assert len(parent_rows) == 2, parent_rows
assert {row["parentArtifactSha256"] for row in parent_rows} == {parent_a, parent_b}
assert parent_merged["concurrentMemoryMerge"]["deltaRows"] == 1

# No delta means identity merge: historical counters cannot amplify.
same = mod.merge_latest(base, previous, base, max_entries=100)
same_by_provider = {
    item["providerId"]: item
    for item in same["experimentMemory"]["entries"]
}
assert same_by_provider["base"]["attempts"] == 3, same_by_provider["base"]
assert same["concurrentMemoryMerge"]["deltaRows"] == 0


# Queue metadata is provider-local under parallel family publication. A provider
# re-observed without a hidden failure must clear only its own stale hidden flag
# while preserving siblings already published by another family.
queue_base = {
    "learningQueue": {
        "hiddenFailureProviders": ["meowtv", "other"],
        "pendingProviders": ["meowtv", "other"],
        "retryProviders": ["meowtv", "other"],
        "completedInCycle": ["old"],
        "processedThisRun": ["old"],
        "providerState": {
            "meowtv": {"attemptCount": 1, "lastStatus": "unresolved"},
            "other": {"attemptCount": 3, "lastStatus": "unresolved"},
        },
    },
    "experimentMemory": {"entries": []},
}
queue_previous = {
    "generatedAt": "2026-11-19T00:10:00+00:00",
    "learningQueue": {
        "hiddenFailureProviders": ["meowtv", "other", "parallel-a"],
        "pendingProviders": ["meowtv", "other", "parallel-a"],
        "retryProviders": ["meowtv", "other", "parallel-a"],
        "completedInCycle": ["old", "parallel-a"],
        "processedThisRun": ["parallel-a"],
        "providerState": {
            "meowtv": {"attemptCount": 1, "lastStatus": "unresolved"},
            "other": {"attemptCount": 3, "lastStatus": "unresolved"},
            "parallel-a": {"attemptCount": 2, "lastStatus": "blocked"},
        },
    },
    "experimentMemory": {"entries": []},
}
queue_current = {
    "generatedAt": "2026-11-19T00:09:00+00:00",
    "learningQueue": {
        "hiddenFailureProviders": [],
        "pendingProviders": ["meowtv"],
        "retryProviders": ["meowtv"],
        "completedInCycle": ["old", "meowtv"],
        "processedThisRun": ["meowtv"],
        "providerState": {
            "meowtv": {
                "attemptCount": 2,
                "lastStatus": "not_executed_no_mutation",
            },
        },
        "timeBudgetExhausted": False,
        "remainingProviderCount": 1,
        "retryProviderCount": 1,
        "budgetMinutes": 90,
    },
    "experimentMemory": {"entries": []},
}
queue_merged = mod.merge_latest(
    queue_base, queue_previous, queue_current, max_entries=100
)
queue = queue_merged["learningQueue"]
assert "meowtv" not in queue["hiddenFailureProviders"], queue
assert set(queue["hiddenFailureProviders"]) == {"other", "parallel-a"}, queue
assert set(queue["pendingProviders"]) == {"meowtv", "other", "parallel-a"}, queue
assert set(queue["retryProviders"]) == {"meowtv", "other", "parallel-a"}, queue
assert set(queue["completedInCycle"]) == {"old", "parallel-a", "meowtv"}, queue
assert queue["providerState"]["meowtv"]["lastStatus"] == "not_executed_no_mutation", queue
assert queue["providerState"]["parallel-a"]["lastStatus"] == "blocked", queue
assert queue_merged["concurrentMemoryMerge"]["queueProcessedProviders"] == ["meowtv"]
assert queue_merged["concurrentMemoryMerge"]["queueHiddenClearedProviders"] == ["meowtv"]
assert queue_merged["concurrentMemoryMerge"]["queueHiddenAddedProviders"] == []

# A current hidden failure for a processed sibling is authoritative for that
# provider only and must coexist with concurrent clean sibling state.
queue_current_hidden = {
    **queue_current,
    "learningQueue": {
        **queue_current["learningQueue"],
        "hiddenFailureProviders": ["meowtv"],
    },
}
queue_rehidden = mod.merge_latest(
    queue_base, queue_previous, queue_current_hidden, max_entries=100
)
assert set(queue_rehidden["learningQueue"]["hiddenFailureProviders"]) == {
    "meowtv", "other", "parallel-a"
}
assert queue_rehidden["concurrentMemoryMerge"]["queueHiddenAddedProviders"] == []

print(
    "Brain Learning concurrent three-way experiment-memory merge "
    "contract passed"
)
