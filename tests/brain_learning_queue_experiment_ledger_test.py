#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_brain_learning_queue.py"
spec = importlib.util.spec_from_file_location("brain_learning_queue_ledger", SCRIPT)
assert spec and spec.loader
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)

plan = {
    "providerId": "synthetic-ledger",
    "failureClass": "chain_terminal_gap",
    "signature": "sig-g3",
    "experimentVariant": 4,
    "experimentGeneration": 3,
    "capabilityStrategy": "html_scraper",
    "observedPipelineStage": "player",
    "action": "probe-targeted-repair",
    "allowedProfiles": ["chain_terminal_extractor_v1_g3"],
}
repair = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g3"],
    "report": {
        "rounds": [{
            "attempts": [{
                "parent_key": "published:synthetic-ledger",
                "profile": "chain_terminal_extractor_v1_g3",
                "status": "generated",
                "brain_plan": plan,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "parent_key": "published:synthetic-ledger",
                "profile": "chain_terminal_extractor_v1_g3",
                "reason": "required_category_playable_proof:anime",
                "brain_plan": plan,
            }],
        }]
    },
}
rows = queue.phase_experiment_entries(
    "synthetic-ledger",
    plan,
    repair,
    {"status": "no_streams"},
)
assert len(rows) == 1, rows
row = rows[0]
assert row["experimentVariant"] == 4, row
assert row["experimentGeneration"] == 3, row
assert row["profile"] == "chain_terminal_extractor_v1_g3", row
assert row["lastOutcome"] == "rejected", row
assert row["failures"] == 1 and row["consecutiveFailures"] == 1, row
assert row["memoryRole"] == "fair-share-exact-experiment-ledger", row

# A planned profile that cannot even materialize must retain the exact causal
# generation identity instead of falling back to g1/v0.
g4_plan = {
    **plan,
    "experimentGeneration": 4,
    "allowedProfiles": ["chain_terminal_extractor_v1_g4"],
}
unavailable = queue.phase_experiment_entries(
    "synthetic-ledger",
    g4_plan,
    {"attemptedProfiles": [], "report": {"rounds": []}},
    {"status": "no_streams"},
)
assert len(unavailable) == 1, unavailable
assert unavailable[0]["experimentVariant"] == 4, unavailable
assert unavailable[0]["experimentGeneration"] == 4, unavailable
assert unavailable[0]["profile"] == "chain_terminal_extractor_v1_g4", unavailable
assert unavailable[0]["lastOutcome"] == "profile_unavailable", unavailable

# Non-publishable progress is still durable experiment evidence and raw endpoint
# or credential-shaped text must never enter cross-phase memory.
progress_repair = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g3"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "status": "generated",
            }],
            "accepted": [],
            "exploration_progress": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "reason": "sandbox_diagnostic_progress:provider-requests https://secret.example authorization=abc",
            }],
            "rejected": [],
        }]
    },
}
progress = queue.phase_experiment_entries(
    "synthetic-ledger",
    plan,
    progress_repair,
    {"status": "no_streams"},
)[0]
assert progress["lastOutcome"] == "exploration_progress_nonpublishable", progress
assert progress["progresses"] == 1, progress
assert "secret.example" not in progress["lastReason"], progress
assert "abc" not in progress["lastReason"], progress
assert "<url>" in progress["lastReason"], progress
assert "<redacted>" in progress["lastReason"], progress

# A child acceptance is positive memory only when the independent final Lab also
# reaches strict playable proof.
accepted_repair = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g3"],
    "report": {
        "rounds": [{
            "attempts": [{"profile": "chain_terminal_extractor_v1_g3", "status": "generated"}],
            "accepted": [{"profile": "chain_terminal_extractor_v1_g3", "reason": "strict_playable_stream_improvement"}],
            "exploration_progress": [],
            "rejected": [],
        }]
    },
}
not_playable = queue.phase_experiment_entries(
    "synthetic-ledger", plan, accepted_repair, {"status": "no_streams"}
)[0]
assert not_playable["successes"] == 0, not_playable
assert not_playable["lastOutcome"] == "rejected", not_playable

playable = queue.phase_experiment_entries(
    "synthetic-ledger", plan, accepted_repair, {"status": "playable"}
)[0]
assert playable["successes"] == 1, playable
assert playable["failures"] == 0 and playable["consecutiveFailures"] == 0, playable
assert playable["lastOutcome"] == "accepted", playable

workflow = (ROOT / ".github" / "workflows" / "brain-learning-lab.yml").read_text(encoding="utf-8")
assert "--runtime-experiment-memory brain-sandbox/health-output/runtime-experiment-memory.json" in workflow
assert "brain-sandbox/health-output/runtime-experiment-memory.json" in workflow
assert "--runtime-experiment-memory automation/brain-repair-memory.json" not in workflow

print("Brain fair-share exact experiment ledger contract passed")
