#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "engine_v2/scripts/plan-repairs.mjs"

policy = {
    "production": {
        "negativeExperimentMemory": {
            "rotateExperimentAfterFailures": 1,
            "maxVariantsPerSignature": 5,
            "finalVariantGeneration": 2,
            "maxLearningGenerationsPerSignature": 5,
        },
        "maxHypotheses": 3,
        "maxMutationsPerProvider": 2,
        "maxRepeatedSignature": 2,
        "maxGeneratedBytesPerProvider": 180000,
        "maxElapsedMsPerProvider": 45000,
    },
    "skillMaturity": {},
}

candidate = {
    "canonical_id": "mallumv-like",
    "censusPrior": {
        "status": "CHAIN REACHED",
        "dominantIssue": "provider_network_zero_result",
        "evidenceDepth": ["movie=chain_reached"],
    },
    "metadata": {"supportedTypes": ["movie"]},
}
result = {
    "status": "no_streams",
    "evidence": {"streams_playable": 0, "streams_returned": 0},
    "tests": [{
        "fixture": {"mediaType": "movie", "category": "movie", "title": "Synthetic"},
        "failure_class": "content_lookup_completed_no_streams",
        "status": "no_streams",
        "network_observations": [],
        "streams_playable": 0,
        "stream_count": 0,
    }],
}

positive = {
    "id": "media_extraction_gap:adaptive_runtime_recovery",
    # This is intentionally the historical failure label, not the current one.
    "failureClass": "media_extraction_gap",
    "profile": "adaptive_runtime_recovery",
    "validated": True,
    "maturity": "experimental",
    "confidence": 1.0,
    "providers": ["mallumv-like"],
    "signatures": ["historical-positive-signature"],
    "successCount": 1,
    "failureCount": 0,
    "actions": ["replay strict provider-local positive program"],
    "sameProviderPositiveProgram": True,
    "positiveProgramFingerprintsByProvider": {"mallumv-like": "a" * 64},
    "source": "brain-positive-program-memory",
}
generic = {
    "id": "chain-terminal-generic",
    "failureClass": "chain_terminal_gap",
    "profile": "adaptive_runtime_recovery",
    "validated": True,
    "maturity": "experimental",
    "confidence": 1.0,
    "providers": ["global"],
    "successCount": 50,
    "failureCount": 0,
    "actions": ["generic chain repair"],
}

def plan_for(provider: str, negative_memory: list[dict] | None = None) -> dict:
    item_candidate = copy.deepcopy(candidate)
    item_candidate["canonical_id"] = provider
    payload = {
        "mode": "learning",
        "policy": policy,
        "learnedSkills": {
            positive["id"]: positive,
            generic["id"]: generic,
        },
        "historicalSolutions": [],
        "negativeMemory": negative_memory or [],
        "items": [{
            "key": f"published:{provider}",
            "candidate": item_candidate,
            "result": result,
            "state": {},
        }],
    }
    completed = subprocess.run(
        ["node", str(PLANNER)],
        cwd=ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    parsed = json.loads(completed.stdout)
    return next(iter((parsed.get("plans") or {}).values()))

same = plan_for("mallumv-like")
assert same["failureClass"] == "chain_terminal_gap", same
assert same["action"] == "probe-targeted-repair", same
assert same["hypotheses"], same
assert same["hypotheses"][0]["id"] == positive["id"], same
assert same["hypotheses"][0]["profile"] == "adaptive_runtime_recovery", same
assert same["hypotheses"][0]["transferScore"] > same["hypotheses"][1]["transferScore"], same
assert same["allowedProfiles"][0] == "adaptive_runtime_recovery", same

# Once the ordinary experiment family is truly exhausted, the strict provider-
# local positive program gets one separately-addressed replay. Generic adaptive
# failures must not pre-exhaust this identity before it actually runs.
exhausted_memory = []
for variant in range(4):
    exhausted_memory.append({
        "providerId": "mallumv-like",
        "providerVersion": "*",
        "failureClass": same["failureClass"],
        "signature": same["signature"],
        "profile": "adaptive_runtime_recovery",
        "experimentVariant": variant,
        "experimentGeneration": 1,
        "failures": 1,
        "consecutiveFailures": 1,
        "successes": 0,
    })
for generation in range(2, 6):
    profile = "chain_terminal_extractor_v1" if generation == 2 else f"chain_terminal_extractor_v1_g{generation}"
    exhausted_memory.append({
        "providerId": "mallumv-like",
        "providerVersion": "*",
        "failureClass": same["failureClass"],
        "signature": same["signature"],
        "profile": profile,
        "experimentVariant": 4,
        "experimentGeneration": generation,
        "failures": 1,
        "consecutiveFailures": 1,
        "successes": 0,
    })
replay = plan_for("mallumv-like", exhausted_memory)
assert replay["action"] == "probe-targeted-repair", replay
assert replay["providerPositiveProgramReplay"] is True, replay
assert replay["postExhaustionStrategyProfile"] == "provider_positive_program_replay_v1", replay
assert replay["allowedProfiles"][0] == "provider_positive_program_replay_v1", replay
assert replay["positiveProgramFingerprint"] == "a" * 64, replay

# Legacy replay debt has no exact positive-program identity. Once current
# positive memory is fingerprinted, that old debt cannot condemn the new
# provider-local replay program.
legacy_failed_replay_memory = exhausted_memory + [{
    "providerId": "mallumv-like",
    "providerVersion": "*",
    "failureClass": same["failureClass"],
    "signature": same["signature"],
    "profile": "provider_positive_program_replay_v1",
    "experimentVariant": 4,
    "experimentGeneration": 5,
    "failures": 1,
    "consecutiveFailures": 1,
    "successes": 0,
}]
legacy_retry = plan_for("mallumv-like", legacy_failed_replay_memory)
assert legacy_retry["postExhaustionStrategyProfile"] == "provider_positive_program_replay_v1", legacy_retry
assert legacy_retry["positiveProgramFingerprint"] == "a" * 64, legacy_retry

# A failure against an older exact positive program also cannot suppress a
# newly learned program fingerprint.
old_program_failed_memory = exhausted_memory + [{
    **legacy_failed_replay_memory[-1],
    "positiveProgramFingerprint": "b" * 64,
}]
rotated = plan_for("mallumv-like", old_program_failed_memory)
assert rotated["postExhaustionStrategyProfile"] == "provider_positive_program_replay_v1", rotated
assert rotated["positiveProgramFingerprint"] == "a" * 64, rotated

# The exact same positive program remains bounded: once that fingerprint has
# failed, the planner must rotate away instead of looping forever.
current_program_failed_memory = exhausted_memory + [{
    **legacy_failed_replay_memory[-1],
    "positiveProgramFingerprint": "a" * 64,
}]
after_failed_replay = plan_for("mallumv-like", current_program_failed_memory)
assert after_failed_replay["postExhaustionStrategyProfile"] != "provider_positive_program_replay_v1", after_failed_replay

# Same historical program must not jump to another provider merely because its
# current failure class is similar. Provider-local positive memory is not a
# transferable skill.
other = plan_for("other-provider")
assert all(row["id"] != positive["id"] for row in other["hypotheses"]), other
assert other["hypotheses"][0]["id"] == generic["id"], other

planner_source = PLANNER.read_text(encoding="utf-8")
assert "sameProviderPositiveProgram" in planner_source
assert "sameProviderPositiveProgramBonus" in planner_source

print("Brain same-provider positive-program cross-failure replay contract passed")
