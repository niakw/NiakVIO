#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "local" / "run_force_experiment_farm.py"

spec = importlib.util.spec_from_file_location("local_force_experiment_farm", SCRIPT)
assert spec is not None and spec.loader is not None
farm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(farm)

row = {
    "provider": "demo",
    "status": "CHAIN REACHED",
    "dominantIssue": "terminal chain reached without playable media",
}
variants = farm.generated_experiments("demo", row, 24)
assert len(variants) == 24, len(variants)
fingerprints = [item["experimentFingerprint"] for item in variants]
keys = [(item["profile"], item["experimentFingerprint"]) for item in variants]
assert len(set(keys)) == len(keys)
assert all(len(value) == 64 for value in fingerprints)
assert all(item["providerId"] == "demo" for item in variants)
strategies = {item["strategy"] for item in variants}
profiles = {item["profile"] for item in variants}
assert strategies == set(farm.guidance_contract.STRATEGY_TO_PROFILE), strategies
assert profiles == set(farm.guidance_contract.STRATEGY_TO_PROFILE.values()), profiles
assert variants[0]["strategy"] == "terminal-media-extractor-with-playback-validation"
assert variants[0]["profile"] == "chain_terminal_extractor_v1"
assert len({farm.experiment_state_key(item) for item in variants}) == len(variants)


synthetic_report = {
    "accepted_repairs": 0,
    "rounds": [
        {
            "generated_candidates": 3,
            "accepted": [],
            "exploration_progress": [{"reason": "partial"}],
        },
        {
            "generated_candidates": 2,
            "accepted": [],
            "exploration_progress": [],
        },
    ],
    "final_counts": {"reachable": 1},
}
synthetic_summary = farm.report_summary(synthetic_report)
assert synthetic_summary["generatedCandidates"] == 5
assert synthetic_summary["explorationProgressCount"] == 1
assert synthetic_summary["acceptedRepairs"] == 0

# Deep can prove the current provider bytes healthy without accepting a mutation.
# The local farm must surface this as a revalidation target and stop wasting variants.
assert "deepBaselineHealthy" in SCRIPT.read_text(encoding="utf-8")
assert "deepBaselineHealthyProviders" in SCRIPT.read_text(encoding="utf-8")

payload = farm.guidance_payload("a" * 40, variants[0])
assert payload["sourceSha"] == "a" * 40
assert payload["publicationAuthority"] is False
assert payload["directMutationAuthority"] is False
assert payload["proofAuthority"] is False
assert payload["providerCount"] == 1

source = SCRIPT.read_text(encoding="utf-8")
for forbidden in (
    "git push",
    "gh workflow run",
    "brain-learning-lab.yml",
    "publicationAuthority\": True",
    "directMutationAuthority\": True",
):
    assert forbidden not in source, forbidden
assert 'env["NIAKVIO_SKIP_CLIENT_DRIFT_GUARD"] = "1"' in source
assert '"clientDriftGuardSkippedForLocalExperiments": True' in source

for required in (
    "--breadth-batch-size",
    "FIELD_LOCAL_FORCE_BREADTH_ROUND",
    "FIELD_LOCAL_FORCE_PROVIDER_BATCH_YIELD",
    "run_adaptive_quick_repair.py",
    "run_adaptive_deep_repair.py",
    "WINNING_GUIDANCE.json",
    "STATE.json",
    "git\", \"worktree\", \"add",
    "quick_then_deep=true",
    "quickPromising",
    "explorationProgressCount",
):
    assert required in source, required

print("local FORCE experiment farm contract passed")

# Adaptive early-stop requires two identical outcomes in every executable profile.
rows = {}
for profile in farm.guidance_contract.STRATEGY_TO_PROFILE.values():
    for idx in range(2):
        rows[f"{profile}-{idx}"] = {
            "profile": profile,
            "quickPromising": False,
            "quickAccepted": False,
            "quickHealth": {"status": "unavailable", "score": 15, "streamsReturned": 0, "streamsPlayable": 0},
            "quick": {"generatedCandidates": 1, "explorationProgressCount": 0},
            "deepAccepted": False,
            "deepBaselineHealthy": False,
        }
assert farm.redundant_strategy_exhaustion(rows) is True
rows[next(iter(rows))]["quickHealth"]["score"] = 16
assert farm.redundant_strategy_exhaustion(rows) is False

# Sanitized Brain-LLM guidance must remain prior-only and observable.
brain_payload = {
    "schemaVersion": 2,
    "sourceSha": "b" * 40,
    "brainLlmSha": "c" * 40,
    "publicationAuthority": False,
    "directMutationAuthority": False,
    "proofAuthority": False,
    "privateContentRetained": False,
    "rows": [dict(variants[0])],
}
brain_payload["rows"][0]["providerId"] = "demo"
brain_rows = farm.external_rows(brain_payload, "demo")
assert len(brain_rows) == 1
assert brain_rows[0]["localExperimentSource"] == "brain-llm-guidance"
assert brain_rows[0]["guidanceSourceSha"] == "b" * 40
source = SCRIPT.read_text(encoding="utf-8")
assert "BRAIN_LLM_GUIDANCE_URL" in source
assert "NiakVIO-Brain-LLM" in source

source = SCRIPT.read_text(encoding="utf-8")
assert "start_new_session=True" in source
assert "signal.signal(signal.SIGTERM, signal_cleanup)" in source
assert "os.killpg(proc.pid, signal.SIGTERM)" in source
