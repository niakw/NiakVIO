#!/usr/bin/env python3
"""End-to-end planner regression: generation attempt is not an executed repair.

This is a control-plane negative-memory test. It does not grant playback
or provider-publication authority, and it never patches any provider.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PLANNER = ROOT / "engine_v2/scripts/plan-repairs.mjs"

spec = importlib.util.spec_from_file_location(
    "brain_generation_attempt_runtime", ROOT / "scripts/brain_repair_runtime.py"
)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

candidate = {
    "canonical_id": "synthetic-route-cards",
    "censusPrior": {
        "status": "ROUTE PROVEN",
        "dominantIssue": "provider_network_zero_result",
        "evidenceDepth": ["movie=lookup_only"],
        "routeProof": ["1 live route / movie"],
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
def verified_html_parser_signal() -> dict:
    # Real historical provider renderer used as a structural oracle; no
    # provider-specific workaround, no mutation and no success declaration.
    spec = importlib.util.spec_from_file_location(
        "historical_html_generation_oracle", ROOT / "scripts/provider_patches/4khdhub_runtime_v1.py")
    assert spec and spec.loader
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    with tempfile.TemporaryDirectory(prefix="brain-generation-source-") as folder:
        stage = Path(folder)
        source = stage / "providers" / "historical-html-renderer.js"
        source.parent.mkdir(parents=True)
        source.write_text(oracle.WRAPPER.replace(
            "CONFIG_PLACEHOLDER",
            json.dumps({"base":"https://provider.example","maxStreams":8,"ua":"test"})),
            encoding="utf-8")
        signal = runtime._current_source_structural_repair_evidence(
            stage, {"local_path": "providers/historical-html-renderer.js"}, result)
    assert signal["profile"] == "html_class_token_exact_v1" and signal["diagnosticOnly"]
    assert signal["proofAuthority"] is False and len(signal["sourceSha256"]) == 64
    return signal


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

def plan(memory: list[dict], force: str = "", source_evidence: dict | None = None) -> dict:
    current_candidate = {
        **candidate,
        **({"structuralRepairEvidence": source_evidence} if source_evidence else {}),
    }
    payload = {
        "mode": "learning",
        "policy": policy,
        "forcePreferredStrategy": force,
        "learnedSkills": {},
        "negativeMemory": memory,
        "items": [{
            "key": "published:synthetic-route-cards",
            "candidate": current_candidate,
            "result": result,
            "state": {},
        }],
    }
    completed = subprocess.run(
        ["node", str(PLANNER)], cwd=ROOT, input=json.dumps(payload),
        capture_output=True, text=True, timeout=25, check=True,
    )
    data = json.loads(completed.stdout)
    assert data.get("plannerErrors") == 0, data
    return data["plans"]["published:synthetic-route-cards"]

initial = plan([])
assert initial["failureClass"] == "route_proven_gap", initial
signature = initial["signature"]
assert signature

def row(variant: int, generation: int = 1) -> dict:
    last = variant == 4
    profile = (
        "proven_route_terminal_traversal_v1"
        if last and generation == 2
        else f"proven_route_terminal_traversal_v1_g{generation}"
        if last and generation > 2
        else "adaptive_runtime_recovery"
    )
    return {
        "providerId": candidate["canonical_id"],
        "failureClass": initial["failureClass"],
        "signature": signature,
        "profile": profile,
        "experimentVariant": variant,
        "experimentGeneration": generation,
        "failures": 1,
        "consecutiveFailures": 1,
        "successes": 0,
        "executionObserved": True,
        "lastOutcome": "rejected",
    }

exhausted = [*[row(i) for i in range(5)], *[row(4, g) for g in range(2, 6)]]
# A reported failure alone cannot authorize an HTML parser fix. It has to
# be grounded in the same staged source that the runtime actually executes.
negative_without_source = plan(exhausted)
assert negative_without_source["postExhaustionStrategyProfile"] == "route_transition_graph_v2", negative_without_source
assert "html_class_token_exact_v1" not in negative_without_source["postExhaustionCandidateProfiles"], negative_without_source
source_signal = verified_html_parser_signal()
first = plan(exhausted, source_evidence=source_signal)
assert first["baseExperimentExhausted"] is True, first
assert first["postExhaustionStrategyProfile"] == "html_class_token_exact_v1", first
assert first["action"] == "probe-targeted-repair", first
fp = first["strategyImplementationFingerprint"]
assert len(fp) == 64, first

# Old memory improperly treated a child that was never generated as executed.
# A missing/stale implementation fingerprint cannot consume a new executable
# generation slot, even when an older runner set executionObserved=true.
for previous_fp in ("", "a" * 64):
    legacy = {
        **row(4, 5),
        "profile": "html_class_token_exact_v1",
        "lastOutcome": "not_generated",
        "lastReason": "brain_repair_loop_detected",
        "executionObserved": True,
        "strategyImplementationFingerprint": previous_fp,
    }
    replay = plan([*exhausted, legacy], source_evidence=source_signal)
    assert replay["postExhaustionStrategyProfile"] == "html_class_token_exact_v1", replay

# Same profile implementation, repeatedly failing to generate a candidate:
# do not loop forever. Rotate to another installed, causally eligible profile.
no_child_same_impl = {
    **row(4, 5),
    "profile": "html_class_token_exact_v1",
    "lastOutcome": "not_generated",
    "lastReason": "structural_profile_made_no_change",
    "executionObserved": False,
    "generationAttemptObserved": True,
    "strategyImplementationFingerprint": fp,
}
rotated = plan([*exhausted, no_child_same_impl], source_evidence=source_signal)
assert rotated["postExhaustionStrategyProfile"] != "html_class_token_exact_v1", rotated
assert rotated["postExhaustionStrategyProfile"], rotated
assert rotated["action"] == "probe-targeted-repair", rotated

# A child that was actually executed and rejected stays negative. Rewriting
# fingerprints must not silently convert a failed playable/identity gate into
# publication authority, or trigger the identical v1 strategy again.
executed_rejection = {
    **no_child_same_impl,
    "executionObserved": True,
    "lastOutcome": "rejected",
    "lastReason": "required_category_playable_proof:movie",
    "strategyImplementationFingerprint": "a" * 64,
}
rejected = plan([*exhausted, executed_rejection], source_evidence=source_signal)
assert rejected["postExhaustionStrategyProfile"] != "html_class_token_exact_v1", rejected

# Legacy ingestion must normalize "not_generated" regardless of old flag.
with tempfile.TemporaryDirectory(prefix="niakvio-brain-generation-") as folder:
    source = Path(folder) / "repair-memory.json"
    source.write_text(json.dumps({
        "schemaVersion": 1,
        "entries": [no_child_same_impl, {**no_child_same_impl, "executionObserved": True}],
    }), encoding="utf-8")
    original = runtime.REPAIR_MEMORY_PATH
    runtime.REPAIR_MEMORY_PATH = source
    try:
        records = runtime.planner_negative_memory("learning")
    finally:
        runtime.REPAIR_MEMORY_PATH = original
    assert records and all(x["executionObserved"] is False for x in records), records
    assert all(x["lastOutcome"] == "not_generated" for x in records), records
    assert all(x["generationAttemptObserved"] is True for x in records), records

# Explicitly verify the memory writer's safety contract. A future refactor
# must not silently restore executionObserved=True for not_generated.
writer = (ROOT / "scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
start = writer.index('mem["lastOutcome"] = "not_generated"')
generation_block = writer[start:start + 550]
assert 'mem["generationAttemptObserved"] = True' in generation_block
assert 'mem["executionObserved"] = False' in generation_block

print(json.dumps({
    "memory": "generation-vs-execution-distinguished",
    "replay_after_stale_fingerprint": True,
    "same_implementation_generation_loop_blocked": True,
    "executed_rejection_still_blocked": True,
    "provider_publication_allowed": False,
}, sort_keys=True))
