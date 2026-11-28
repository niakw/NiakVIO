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
assert row["executionObserved"] is True, row

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
assert unavailable[0]["executionObserved"] is False, unavailable

# Planner action labels may change when a selected causal profile cannot
# materialize. The exact selected g/v/profile is still durable negative
# experiment evidence and must advance the next phase.
deferred_plan = {
    **g4_plan,
    "action": "collect-more-evidence",
}
deferred_unavailable = queue.phase_experiment_entries(
    "synthetic-ledger",
    deferred_plan,
    {"attemptedProfiles": [], "report": {"rounds": []}},
    {"status": "unresolved"},
)
assert len(deferred_unavailable) == 1, deferred_unavailable
assert deferred_unavailable[0]["experimentGeneration"] == 4, deferred_unavailable
assert deferred_unavailable[0]["profile"] == "chain_terminal_extractor_v1_g4", deferred_unavailable
assert deferred_unavailable[0]["lastOutcome"] == "profile_unavailable", deferred_unavailable

# Fingerprinted meta-gap experiments are executable hypotheses, not aliases for
# the generic profile/generation. Persist the exact fingerprint so the JS
# planner's failedFingerprint() and three-fingerprint causal budget can work.
meta_plan = {
    **plan,
    "failureClass": "unknown_failure",
    "signature": "sig-meta-gap",
    "profile": "adaptive_runtime_recovery",
    "allowedProfiles": ["adaptive_runtime_recovery"],
    "llmAdvisorExperimentFingerprint": "a" * 64,
    "llmAdvisorGuidanceKind": "meta-gap-synthesis",
    "llmAdvisorMetaGapGeneration": 0,
}
meta_repair = {
    "attemptedProfiles": ["adaptive_runtime_recovery"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "adaptive_runtime_recovery",
                "status": "generated",
                "brain_plan": meta_plan,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "profile": "adaptive_runtime_recovery",
                "reason": "safety_gate:no_playable_proof",
                "brain_plan": meta_plan,
            }],
        }]
    },
}
meta_rows = queue.phase_experiment_entries(
    "synthetic-ledger", meta_plan, meta_repair, {"status": "no_streams"},
)
assert len(meta_rows) == 1, meta_rows
assert meta_rows[0]["llmAdvisorExperimentFingerprint"] == "a" * 64, meta_rows
assert meta_rows[0]["llmAdvisorGuidanceKind"] == "meta-gap-synthesis", meta_rows
assert meta_rows[0]["llmAdvisorMetaGapGeneration"] == 0, meta_rows

meta_plan_2 = {
    **meta_plan,
    "llmAdvisorExperimentFingerprint": "b" * 64,
    "llmAdvisorMetaGapGeneration": 1,
}
meta_repair_2 = {
    "attemptedProfiles": ["adaptive_runtime_recovery"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "adaptive_runtime_recovery",
                "status": "generated",
                "brain_plan": meta_plan_2,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "profile": "adaptive_runtime_recovery",
                "reason": "safety_gate:no_playable_proof",
                "brain_plan": meta_plan_2,
            }],
        }]
    },
}
meta_rows_2 = queue.phase_experiment_entries(
    "synthetic-ledger", meta_plan_2, meta_repair_2, {"status": "no_streams"},
)
meta_state = {
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {"schemaVersion": 1, "entries": []},
}
meta_state = queue.merge_phase_learning_state(meta_state, meta_rows)
meta_state = queue.merge_phase_learning_state(meta_state, meta_rows_2)
stored_meta = meta_state["experimentMemory"]["entries"]
assert len(stored_meta) == 2, stored_meta
assert {row["llmAdvisorExperimentFingerprint"] for row in stored_meta} == {"a" * 64, "b" * 64}, stored_meta
assert {row["llmAdvisorMetaGapGeneration"] for row in stored_meta} == {0, 1}, stored_meta
meta_state = queue.merge_phase_learning_state(meta_state, meta_rows)
stored_meta = meta_state["experimentMemory"]["entries"]
assert len(stored_meta) == 2, stored_meta
by_fp = {row["llmAdvisorExperimentFingerprint"]: row for row in stored_meta}
assert by_fp["a" * 64]["attempts"] == 2, by_fp
assert by_fp["b" * 64]["attempts"] == 1, by_fp

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

slice_exhausted = queue.phase_experiment_entries(
    "synthetic-ledger",
    plan,
    accepted_repair,
    {"status": "fair_share_slice_exhausted"},
)[0]
assert slice_exhausted["successes"] == 0, slice_exhausted
assert slice_exhausted["failures"] == 0, slice_exhausted
assert slice_exhausted["consecutiveFailures"] == 0, slice_exhausted
assert slice_exhausted["lastOutcome"] == "executed_inconclusive", slice_exhausted
assert slice_exhausted["lastReason"] == "strict_lab_not_completed_due_fair_share_budget", slice_exhausted
assert slice_exhausted["executionObserved"] is True, slice_exhausted

workflow = (ROOT / ".github" / "workflows" / "brain-learning-lab.yml").read_text(encoding="utf-8")
assert "--runtime-experiment-memory brain-sandbox/health-output/runtime-experiment-memory.json" in workflow
assert "brain-sandbox/health-output/runtime-experiment-memory.json" in workflow
assert "--runtime-experiment-memory automation/brain-repair-memory.json" not in workflow



# A child may already have replanned to the next post-g5 strategy after the
# experiment it actually executed failed. The ledger must attribute the failure
# to the event's plan snapshot and must not pre-fail the unexecuted replan.
executed_g5 = {
    **plan,
    "signature": "sig-g5",
    "experimentGeneration": 5,
    "allowedProfiles": ["chain_terminal_extractor_v1_g5"],
}
next_evolved = {
    **executed_g5,
    "repairType": "evolved_strategy",
    "strategyEscalated": True,
    "learningDisposition": "execute_bounded_evolved_strategy",
    "allowedProfiles": ["terminal_request_program_inference_v1"],
}
replanned_repair = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g5"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "chain_terminal_extractor_v1_g5",
                "status": "generated",
                "brain_plan": executed_g5,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "profile": "chain_terminal_extractor_v1_g5",
                "reason": "no_validated_improvement",
                "brain_plan": executed_g5,
            }],
        }]
    },
}
replanned_rows = queue.phase_experiment_entries(
    "synthetic-ledger",
    next_evolved,
    replanned_repair,
    {"status": "no_streams"},
)
assert len(replanned_rows) == 1, replanned_rows
assert replanned_rows[0]["profile"] == "chain_terminal_extractor_v1_g5", replanned_rows
assert replanned_rows[0]["experimentGeneration"] == 5, replanned_rows
assert replanned_rows[0]["signature"] == "sig-g5", replanned_rows
assert all(row["profile"] != "terminal_request_program_inference_v1" for row in replanned_rows)

# Exact outcomes become an in-memory, read-only Learning prior immediately so
# the next attempt can advance instead of replaying the same generation.
phase_state = {
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {"schemaVersion": 1, "entries": []},
}
phase_state = queue.merge_phase_learning_state(phase_state, replanned_rows)
stored = phase_state["experimentMemory"]["entries"]
assert len(stored) == 1 and stored[0]["failures"] == 1, stored
phase_state = queue.merge_phase_learning_state(phase_state, replanned_rows)
stored = phase_state["experimentMemory"]["entries"]
assert len(stored) == 1, stored
assert stored[0]["failures"] == 2 and stored[0]["consecutiveFailures"] == 2, stored
assert phase_state["publicationAllowed"] is False
assert phase_state["productionWritesAllowed"] is False

# Fair-share remains one attempt for ordinary work, but a finite evolved
# strategy family may consume the remainder of the same provider slice.
assert queue.should_continue_evolved_frontier(next_evolved, 1) is True
assert queue.should_continue_evolved_frontier(next_evolved, 2) is True
assert queue.should_continue_evolved_frontier(next_evolved, 3) is False

# The first attempt may still report the exact final g5 strategy it just ran.
# That boundary must receive one continuation so phase memory can expose and
# execute the newly unlocked evolved strategy in the next sandbox process.
final_g5 = {
    **executed_g5,
    "repairType": "provider_runtime",
    "experimentGenerationLimit": 5,
    "experimentExhausted": False,
}
assert queue.should_continue_evolved_frontier(final_g5, 1) is True
assert queue.should_continue_evolved_frontier(final_g5, 2) is True
assert queue.should_continue_evolved_frontier(final_g5, 3) is False
assert queue.should_continue_evolved_frontier(
    {**final_g5, "experimentGeneration": 4},
    1,
) is False
assert queue.should_continue_evolved_frontier(
    {**next_evolved, "repairType": "provider_runtime", "experimentGenerationLimit": 0},
    1,
) is False

source = SCRIPT.read_text(encoding="utf-8")
assert "phase_learning_state_path" in source
assert "merge_phase_learning_state(" in source
assert "fastRepairHandoffMaxEvolvedAttemptsPerProviderThisPhase" in source
assert "incomplete_entries = phase_experiment_entries(" in source
assert "strict_lab_not_completed_due_fair_share_budget" in source

# A sandbox profile can be selected and fail before child bytes exist. Its
# generation attempt is useful rotation evidence, but NOT executed-negative
# authority. Replaying a different executor must not inherit a false failure.
not_generated_repair = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g3"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "status": "not_generated",
                "reason": "structural_profile_made_no_change",
                "brain_plan": plan,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [],
        }]
    },
}
generation_rows = queue.phase_experiment_entries(
    "synthetic-ledger", plan, not_generated_repair, {"status": "no_streams"},
)
assert len(generation_rows) == 1, generation_rows
assert generation_rows[0]["lastOutcome"] == "not_generated", generation_rows
assert generation_rows[0]["executionObserved"] is False, generation_rows
assert generation_rows[0]["generationAttemptObserved"] is True, generation_rows

# Real failed execution still outranks a later no-child attempt for the same
# profile fingerprint. Reversed order must yield identical safe semantics.
for first, second in ((generation_rows, rows), (rows, generation_rows)):
    test_state = {
        "publicationAllowed": False,
        "productionWritesAllowed": False,
        "experimentMemory": {"schemaVersion": 1, "entries": []},
    }
    test_state = queue.merge_phase_learning_state(test_state, first)
    test_state = queue.merge_phase_learning_state(test_state, second)
    observed = test_state["experimentMemory"]["entries"]
    assert len(observed) == 1, observed
    assert observed[0]["executionObserved"] is True, observed
    assert observed[0]["lastOutcome"] == "rejected", observed
    assert observed[0]["generationAttemptObserved"] is True, observed
    assert test_state["publicationAllowed"] is False
    assert test_state["productionWritesAllowed"] is False

# Legacy no-child memory incorrectly marked executionObserved=true. It cannot
# turn repeated generation-only failures into fake terminal replay evidence.
legacy_state = {
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {
        "schemaVersion": 1,
        "entries": [{**generation_rows[0], "executionObserved": True}],
    },
}
merged = queue.merge_phase_learning_state(legacy_state, generation_rows)
assert merged["experimentMemory"]["entries"][0]["executionObserved"] is False, merged
assert merged["experimentMemory"]["entries"][0]["lastOutcome"] == "not_generated", merged


# A healthy exact published parent must never become negative provider memory
# merely because the internal repair child observes a contradictory zero-stream
# baseline before mutation.
published_row = {
    "id": "healthy-parent",
    "status": "healthy",
    "evidence": {
        "streams_playable": 2,
        "provider_server_accessible": True,
        "provider_server_successful_response": True,
    },
    "tests": [
        {"streams_returned": 2, "streams_playable": 2},
    ],
}
published_info = queue.diagnostic(published_row)
assert published_info["published_streams_playable"] == 2, published_info
assert published_info["published_streams_returned"] == 2, published_info

contradictory_repair = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g3"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "status": "generated",
                "baseline_status": "no_streams",
                "baseline_streams_returned": 0,
                "baseline_streams_playable": 0,
                "brain_plan": plan,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "reason": "safety_gate:no_playable_proof",
                "brain_plan": plan,
            }],
        }]
    },
}
contradiction = queue.repair_parent_baseline_contradiction(
    published_info,
    contradictory_repair,
)
assert contradiction is not None, contradiction
assert contradiction["publishedStreamsPlayable"] == 2, contradiction
assert contradiction["baselineStreamsPlayable"] == 0, contradiction
assert contradiction["proofAuthority"] is False, contradiction

contradiction_rows = queue.phase_experiment_entries(
    "healthy-parent",
    plan,
    contradictory_repair,
    {"status": "no_streams"},
    contradiction,
)
assert len(contradiction_rows) == 1, contradiction_rows
contradiction_row = contradiction_rows[0]
assert contradiction_row["executionObserved"] is True, contradiction_row
assert contradiction_row["lastOutcome"] == "executed_inconclusive", contradiction_row
assert contradiction_row["lastReason"] == "harness_parent_contradiction", contradiction_row
assert contradiction_row["failures"] == 0, contradiction_row
assert contradiction_row["consecutiveFailures"] == 0, contradiction_row
assert contradiction_row["causalExerciseObserved"] is False, contradiction_row
assert contradiction_row["harnessParentContradiction"] is True, contradiction_row
assert contradiction_row["harnessParentContradictionEvidence"]["publishedStreamsPlayable"] == 2

contradiction_state = {
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {"schemaVersion": 1, "entries": []},
}
contradiction_state = queue.merge_phase_learning_state(
    contradiction_state, contradiction_rows
)
contradiction_state = queue.merge_phase_learning_state(
    contradiction_state, contradiction_rows
)
stored_contradiction = contradiction_state["experimentMemory"]["entries"][0]
assert stored_contradiction["attempts"] == 2, stored_contradiction
assert stored_contradiction["failures"] == 0, stored_contradiction
assert stored_contradiction["consecutiveFailures"] == 0, stored_contradiction
assert stored_contradiction["harnessParentContradiction"] is True, stored_contradiction
assert stored_contradiction["lastOutcome"] == "executed_inconclusive", stored_contradiction

# A false-zero child parent may make a candidate look like a strict playable
# improvement. That is still inconclusive: it only recovered the already
# playable published level and must not become positive repair memory.
contradictory_accepted = {
    "attemptedProfiles": ["chain_terminal_extractor_v1_g3"],
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "status": "generated",
                "baseline_status": "no_streams",
                "baseline_streams_returned": 0,
                "baseline_streams_playable": 0,
                "brain_plan": plan,
            }],
            "accepted": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "reason": "strict_playable_stream_improvement",
                "brain_plan": plan,
            }],
            "exploration_progress": [],
            "rejected": [],
        }]
    },
}
false_positive_rows = queue.phase_experiment_entries(
    "healthy-parent",
    plan,
    contradictory_accepted,
    {"status": "playable"},
    contradiction,
)
assert len(false_positive_rows) == 1, false_positive_rows
false_positive = false_positive_rows[0]
assert false_positive["successes"] == 0, false_positive
assert false_positive["failures"] == 0, false_positive
assert false_positive["lastOutcome"] == "executed_inconclusive", false_positive
assert false_positive["lastReason"] == "harness_parent_contradiction", false_positive
assert false_positive["harnessParentContradiction"] is True, false_positive

# No contradiction when the internal baseline preserves the published playable
# parent; this protects genuine negative experiments from being hidden.
matching_parent = {
    **contradictory_repair,
    "report": {
        "rounds": [{
            "attempts": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "status": "generated",
                "baseline_status": "healthy",
                "baseline_streams_returned": 2,
                "baseline_streams_playable": 2,
                "brain_plan": plan,
            }],
            "accepted": [],
            "exploration_progress": [],
            "rejected": [{
                "profile": "chain_terminal_extractor_v1_g3",
                "reason": "safety_gate:no_playable_proof",
                "brain_plan": plan,
            }],
        }]
    },
}
assert queue.repair_parent_baseline_contradiction(
    published_info, matching_parent
) is None


# Client replay is reserved for executable, validated mutations. Generation-only
# debt must advance Brain memory without spending a TV/Desktop/Mobile Lab.
assert queue.repair_executable_mutation_observed({
    "validationStatus": "validated",
    "report": {"rounds": [{
        "attempts": [{"profile": "x", "status": "generated"}],
        "accepted": [], "rejected": [], "exploration_progress": [],
    }]},
}) is True
assert queue.repair_executable_mutation_observed({
    "validationStatus": "validated",
    "report": {"rounds": [{
        "attempts": [{"profile": "x", "status": "not_generated"}],
        "accepted": [], "rejected": [], "exploration_progress": [],
    }]},
}) is False
assert queue.repair_executable_mutation_observed({
    "validationStatus": "rejected_incomplete_child",
    "report": {"rounds": [{
        "attempts": [{"profile": "x", "status": "generated"}],
        "accepted": [], "rejected": [], "exploration_progress": [],
    }]},
}) is False
assert queue.repair_executable_mutation_observed({
    "validationStatus": "validated",
    "report": {"rounds": [{
        "attempts": [],
        "accepted": [],
        "rejected": [{"profile": "x", "reason": "no_validated_improvement"}],
        "exploration_progress": [],
    }]},
}) is True

source = SCRIPT.read_text(encoding="utf-8")
assert "FIELD_BRAIN_LAB_SKIPPED" in source
assert '"status": "not_executed_no_mutation"' in source
assert 'repair_executable_mutation_observed(repair)' in source
assert 'state["lastFixture"] = ""' in source
assert 'state["lastClients"] = {}' in source
assert 'not in {"playable", "not_executed_no_mutation"}' in source

print("Brain fair-share exact experiment ledger contract passed")
