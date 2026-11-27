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
    "methods": ["POST", "DELETE"],
    "stages": ["episode", "media", "credential_theft"],
    "responseKinds": ["json", "private_blob"],
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

print("Brain sanitized network execution memory contract passed")
