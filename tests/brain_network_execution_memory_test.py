#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import deep_repair_loop as deep
import run_brain_learning_queue as queue

raw_result = {
    "tests": [{
        "network_observations": [
            {
                "url": "https://secret.example/player?token=do-not-keep",
                "host": "secret.example",
                "request_headers": {"authorization": "Bearer secret"},
                "response_body": "private",
                "stage": "episode",
                "method": "POST",
                "status": 200,
                "infrastructure": False,
                "response_structure": {"kind": "json", "keys": ["secret"]},
            },
            {
                "url": "https://secret.example/media",
                "stage": "media",
                "method": "GET",
                "status": 403,
                "infrastructure": False,
                "response_structure": {"kind": "html"},
            },
            {
                "url": "https://api.themoviedb.org/3/tv/1?api_key=secret",
                "stage": "search",
                "method": "GET",
                "status": 200,
                "infrastructure": True,
                "response_structure": {"kind": "json"},
            },
        ],
    }],
}
summary = deep.sanitized_network_execution_summary(raw_result)
assert summary["providerRequestCount"] == 2, summary
assert summary["successfulProviderRequestCount"] == 1, summary
assert summary["statusBuckets"] == {
    "2xx": 1, "3xx": 0, "4xx": 1, "5xx": 0, "network": 0,
}, summary
assert summary["methods"] == ["GET", "POST"], summary
assert summary["stages"] == ["episode", "media"], summary
assert summary["deepestStage"] == "media", summary
assert summary["responseKinds"] == ["html", "json"], summary
assert summary["proofAuthority"] is False
assert summary["publicationAuthority"] is False
for forbidden in ("secret.example", "do-not-keep", "authorization", "private", "api.themoviedb.org"):
    assert forbidden not in repr(summary), (forbidden, summary)

profile = "document_request_contract_mining_v2"
fingerprint = "a" * 64
plan = {
    "failureClass": "media_extraction_gap",
    "signature": "sig-player-bootstrap",
    "allowedProfiles": [profile],
    "experimentVariant": 4,
    "experimentGeneration": 5,
    "strategyImplementationFingerprint": fingerprint,
    "capabilityStrategy": "mixed_embed_resolver",
    "observedPipelineStage": "episode",
}
poisoned = {
    **summary,
    "url": "https://must-not-survive.example/signed",
    "headers": {"cookie": "secret"},
    "body": "secret body",
    "methods": [*summary["methods"], "DELETE"],
    "stages": [*summary["stages"], "credential_theft"],
    "responseKinds": [*summary["responseKinds"], "private_blob"],
}
repair = {
    "attemptedProfiles": [profile],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": profile,
                "status": "generated",
                "brain_plan": plan,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "profile": profile,
                "brain_plan": plan,
                "reason": "safety_gate:no_playable_proof",
                "network_execution": poisoned,
            }],
        }],
    },
}
entries = queue.phase_experiment_entries(
    "anime-sama",
    plan,
    repair,
    {"status": "unresolved"},
)
assert len(entries) == 1, entries
row = entries[0]
assert row["profile"] == profile
assert row["strategyImplementationFingerprint"] == fingerprint
assert row["executionObserved"] is True
assert row["lastOutcome"] == "rejected"
persisted = row["networkExecutionSummary"]
assert persisted == summary, (persisted, summary)
for forbidden in ("must-not-survive", "cookie", "secret body", "DELETE", "credential_theft", "private_blob"):
    assert forbidden not in repr(persisted), (forbidden, persisted)

state = queue.merge_phase_learning_state({}, entries)
saved = state["experimentMemory"]["entries"][0]
assert saved["strategyImplementationFingerprint"] == fingerprint
assert saved["networkExecutionSummary"] == summary
assert state["publicationAllowed"] is False
assert state["productionWritesAllowed"] is False

# One-shot diagnostic replay must enrich an old executed negative without
# pretending it is a new experiment or changing its historical counters.
historical_row = {
    **row,
    "attempts": 7,
    "failures": 3,
    "consecutiveFailures": 1,
    "lastSeenAt": "2026-11-27T20:00:00+00:00",
}
historical_row.pop("networkExecutionSummary", None)
historical = {
    "schemaVersion": 1,
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [historical_row],
    },
}
diagnostic_target = queue.missing_network_diagnostic_negative(
    historical,
    "anime-sama",
    profile,
)
assert diagnostic_target is not None
assert diagnostic_target["strategyImplementationFingerprint"] == fingerprint
masked = queue.diagnostic_replay_memory(historical, diagnostic_target)
assert masked["experimentMemory"]["entries"] == []
assert historical["experimentMemory"]["entries"], "source memory must remain immutable"

diagnostic_plan = {
    **plan,
    "strategyImplementationFingerprint": fingerprint,
}
backfill = queue.diagnostic_network_backfill_entry(
    diagnostic_target,
    diagnostic_plan,
    summary,
)
assert backfill is not None
assert backfill["attempts"] == 7
assert backfill["failures"] == 3
assert backfill["consecutiveFailures"] == 1
assert backfill["lastOutcome"] == "rejected"
assert backfill["lastSeenAt"] == "2026-11-27T20:00:00+00:00"
assert backfill["networkExecutionSummary"] == summary
assert queue.diagnostic_network_backfill_entry(
    diagnostic_target,
    {**diagnostic_plan, "strategyImplementationFingerprint": "b" * 64},
    summary,
) is None

enriched = queue.merge_phase_learning_state(historical, [backfill])
enriched_row = enriched["experimentMemory"]["entries"][0]
assert enriched_row["attempts"] == 7
assert enriched_row["failures"] == 3
assert enriched_row["consecutiveFailures"] == 1
assert enriched_row["lastOutcome"] == "rejected"
assert enriched_row["networkExecutionSummary"] == summary
assert queue.missing_network_diagnostic_negative(
    enriched,
    "anime-sama",
    profile,
) is None, "diagnostic replay must be one-shot once telemetry exists"

print("Brain sanitized network execution memory contract passed")
