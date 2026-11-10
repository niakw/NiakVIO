#!/usr/bin/env python3
"""Post-exhaustion Brain cannot choose HTML parser patch without exact source signature."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "engine_v2/scripts/plan-repairs.mjs"
provider = "generic-html-post-exhaustion"

def plan(signal=None):
    candidate = {
        "canonical_id": provider,
        "metadata": {"supportedTypes": ["movie", "tv"]},
        "censusPrior": {
            "status": "ROUTE PROVEN",
            "dominantIssue": "provider_network_zero_result",
            "evidenceDepth": ["movie=route_proven"],
        },
    }
    if signal is not None:
        candidate["structuralRepairEvidence"] = signal
    result = {
        "status": "no_streams",
        "evidence": {"streams_playable": 0, "streams_returned": 0},
        "tests": [{
            "status": "no_streams", "failure_class": "content_lookup_completed_no_streams",
            "fixture": {"category": "movie", "mediaType": "movie"},
            "network_observations": [{"status": 200, "ok": True, "stage": "search"}],
            "streams_playable": 0, "stream_count": 0,
        }],
    }
    memory = [{
        "providerId": provider, "failureClass": "route_proven_gap",
        "profile": "adaptive_runtime_recovery",
        "experimentVariant": i, "experimentGeneration": 1,
        "consecutiveFailures": 1, "failures": 1, "successes": 0,
        "executionObserved": True, "lastOutcome": "rejected",
    } for i in range(5)]
    payload = {
        "mode": "repair", "explorationChain": True,
        "policy": {"production": {
            "maxHypotheses": 3, "maxMutationsPerProvider": 2,
            "maxRepeatedSignature": 2, "maxGeneratedBytesPerProvider": 180000,
            "maxElapsedMsPerProvider": 45000,
            "negativeExperimentMemory": {
                "rotateExperimentAfterFailures": 1,
                "maxVariantsPerSignature": 5, "finalVariantGeneration": 1,
            },
        }, "skillMaturity": {}},
        "learnedSkills": {}, "negativeMemory": memory, "llmGuidance": [],
        "items": [{"key": "published:" + provider,
                   "candidate": candidate, "result": result, "state": {}}],
    }
    proc = subprocess.run(["node", str(PLANNER)], input=json.dumps(payload),
                          text=True, capture_output=True, cwd=ROOT, timeout=25)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["plans"]["published:" + provider]

absent = plan()
assert absent["postExhaustionStrategyProfile"] != "html_class_token_exact_v1", absent
assert "html_class_token_exact_v1" not in absent["allowedProfiles"], absent
assert "html_class_token_exact_v1" not in absent["postExhaustionCandidateProfiles"], absent

present = plan({
    "profile": "html_class_token_exact_v1",
    "source": "current_candidate_bytes",
    "sourceSha256": "a" * 64,
    "diagnosticOnly": True,
    "proofAuthority": False,
})
assert "html_class_token_exact_v1" in present["postExhaustionCandidateProfiles"], present
assert present["postExhaustionStrategyProfile"] == "html_class_token_exact_v1", present
assert present["allowedProfiles"] and present["allowedProfiles"][0] == "html_class_token_exact_v1", present

spoof = plan({
    "profile": "html_class_token_exact_v1",
    "source": "historical-fixture", "sourceSha256": "a" * 64,
    "diagnosticOnly": True, "proofAuthority": False,
})
assert spoof["postExhaustionStrategyProfile"] != "html_class_token_exact_v1", spoof

print("BRAIN_POST_EXHAUSTION_HTML_SIGNATURE_OK current_source_required=true "
      "historical_fixtures_not_authority=true no_repair_claim=true")
