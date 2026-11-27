#!/usr/bin/env python3
"""Executable bytes do not become negative memory until their Bloc is exercised."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import brain_repair_runtime as brain
import run_brain_learning_queue as queue

ZERO_NETWORK = {
    "schemaVersion": 1,
    "providerRequestCount": 0,
    "successfulProviderRequestCount": 0,
    "networkFailureCount": 0,
    "statusBuckets": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "network": 0},
    "methods": [],
    "stages": [],
    "deepestStage": "none",
    "responseKinds": [],
    "proofAuthority": False,
    "publicationAuthority": False,
    "rawAddressRetained": False,
    "headersRetained": False,
    "bodyRetained": False,
}
ZERO_DELTA = {
    "schemaVersion": 1,
    "providerRequestDelta": 0,
    "successfulProviderRequestDelta": 0,
    "networkFailureDelta": 0,
    "statusBucketDelta": {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "network": 0},
    "newMethods": [],
    "newStages": [],
    "newResponseKinds": [],
    "parentDeepestStage": "none",
    "candidateDeepestStage": "none",
    "stageRankDelta": 0,
    "stageAdvanced": False,
    "proofAuthority": False,
    "publicationAuthority": False,
    "rawAddressRetained": False,
    "headersRetained": False,
    "bodyRetained": False,
}
REAL_NETWORK = {
    **ZERO_NETWORK,
    "providerRequestCount": 57,
    "successfulProviderRequestCount": 12,
    "networkFailureCount": 3,
    "statusBuckets": {"2xx": 12, "3xx": 0, "4xx": 42, "5xx": 0, "network": 3},
    "methods": ["GET", "POST"],
    "stages": ["content_lookup", "episode"],
    "deepestStage": "episode",
    "responseKinds": ["html"],
}

session = "provider_session_bootstrap_replay_v1"
v2 = "document_request_contract_mining_v2"
assert brain.strategy_causal_exercise_observed(session, ZERO_NETWORK) is False
assert brain.strategy_causal_exercise_observed(v2, REAL_NETWORK) is True
assert brain.strategy_causal_exercise_observed(session, {}) is None

plan = {
    "failureClass": "media_extraction_gap",
    "signature": "player-bootstrap",
    "allowedProfiles": [session],
    "experimentVariant": 4,
    "experimentGeneration": 5,
    "strategyImplementationFingerprint": "b" * 64,
}
repair = {
    "attemptedProfiles": [session],
    "report": {"rounds": [{
        "attempts": [{"profile": session, "status": "generated", "brain_plan": plan}],
        "accepted": [],
        "exploration_progress": [],
        "rejected": [{
            "profile": session,
            "brain_plan": plan,
            "reason": "safety_gate:no_playable_proof",
            "network_execution": ZERO_NETWORK,
            "network_execution_delta": ZERO_DELTA,
        }],
    }]},
}
rows = queue.phase_experiment_entries(
    "family-representative", plan, repair, {"status": "unresolved"}
)
assert len(rows) == 1, rows
row = rows[0]
assert row["executionObserved"] is True, row
assert row["causalExerciseObserved"] is False, row
assert row["lastOutcome"] == "executed_inconclusive", row
assert row["failures"] == 0, row
assert row["consecutiveFailures"] == 0, row

print(
    "FIELD_BRAIN_CAUSAL_EXERCISE "
    "bytes_executed=true capability_exercised=false negative_memory=false"
)
