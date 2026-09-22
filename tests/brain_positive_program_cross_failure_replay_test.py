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

def plan_for(provider: str) -> dict:
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
        "negativeMemory": [],
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
