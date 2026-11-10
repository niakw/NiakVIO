#!/usr/bin/env python3
"""Post-exhaustion Brain cannot choose HTML parser patch without exact source signature."""
from __future__ import annotations
import json
import subprocess
import tempfile
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
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
        "profile": "proven_route_terminal_traversal_v1" if i == 4 else "adaptive_runtime_recovery",
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

def observed_historical_html_signal():
    # The retained real renderer is a diagnostic oracle, not a fixture that
    # grants repair authority. This must agree with canonical source inspection.
    spec = importlib.util.spec_from_file_location(
        "post_exhaustion_source_oracle", ROOT / "scripts/provider_patches/4khdhub_runtime_v1.py")
    assert spec and spec.loader
    provider_renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider_renderer)
    import brain_repair_runtime as brain
    with tempfile.TemporaryDirectory(prefix="post-exhaustion-real-html-") as temp:
        stage = Path(temp)
        source = stage / "providers" / "historical-renderer.js"
        source.parent.mkdir(parents=True)
        source.write_text(provider_renderer.WRAPPER.replace(
            "CONFIG_PLACEHOLDER",
            json.dumps({"base":"https://provider.example","maxStreams":8,"ua":"test"})),
            encoding="utf-8")
        signal = brain._current_source_structural_repair_evidence(
            stage, {"local_path": "providers/historical-renderer.js"},
            {"status": "no_streams"})
    assert signal["profile"] == "html_class_token_exact_v1", signal
    assert len(signal["sourceSha256"]) == 64
    assert signal["diagnosticOnly"] is True and signal["proofAuthority"] is False
    return signal


absent = plan()
assert absent["baseExperimentExhausted"] is True, absent
assert absent["postExhaustionStrategyProfile"] == "route_transition_graph_v2", absent
assert "html_class_token_exact_v1" not in absent["allowedProfiles"], absent
assert "html_class_token_exact_v1" not in absent["postExhaustionCandidateProfiles"], absent

source_signal = observed_historical_html_signal()
present = plan(source_signal)
assert "html_class_token_exact_v1" in present["postExhaustionCandidateProfiles"], present
assert present["postExhaustionStrategyProfile"] == "html_class_token_exact_v1", present
assert present["allowedProfiles"] and present["allowedProfiles"][0] == "html_class_token_exact_v1", present

spoof = plan({**source_signal, "source": "historical-fixture"})
assert spoof["postExhaustionStrategyProfile"] == "route_transition_graph_v2", spoof

print("BRAIN_POST_EXHAUSTION_HTML_SIGNATURE_OK current_source_required=true "
      "historical_fixtures_not_authority=true no_repair_claim=true")
