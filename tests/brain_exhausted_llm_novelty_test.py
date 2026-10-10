#!/usr/bin/env python3
"""Real planner replay: exhausted Learning must accept only new LLM hypotheses."""
from __future__ import annotations
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fixture = runpy.run_path(str(ROOT / "tests/brain_final_experiment_generation_test.py"))
plan = fixture["plan"]
memory = fixture["evolved_memory"]
base = fixture["base_exhausted"]

# The imported test proves the entire installed causal family is exhausted.
assert fixture["learning_exhausted"]["experimentExhausted"] is True
advice = [{
    "providerId": "synthetic-generation",
    "failureClass": "chain_terminal_gap",
    "targetLayer": "provider",
    "strategy": "new-bounded-advisor-evidence",
    "profile": "chain_terminal_extractor_v1",
    "confidence": 0.96,
    "priorOnly": True,
    "experiment": {"routePolicy": "owned_only"},
    "experimentFingerprint": "a" * 64,
    "guidanceKind": "persistent-learning",
}]

# plan() in this existing fixture accepts no advisor input, so invoke the
# exact Node planner with identical inputs but injected guidance.
import json
import subprocess
candidate = fixture["candidate"]
result = fixture["result"]
policy = fixture["policy"]
planner = fixture["PLANNER"]

def with_advice(rows, guidance):
    payload = {
        "mode": "learning",
        "policy": policy,
        "learnedSkills": {},
        "llmGuidance": guidance,
        "negativeMemory": rows,
        "items": [{"key": "published:synthetic-generation",
                   "candidate": candidate, "result": result, "state": {}}],
    }
    process = subprocess.run(["node", str(planner)], cwd=ROOT,
                             input=json.dumps(payload), capture_output=True,
                             text=True, check=True, timeout=20)
    return json.loads(process.stdout)["plans"]["published:synthetic-generation"]

fresh = with_advice(memory, advice)
assert fresh["llmAdvisorApplied"] is True, fresh
assert fresh["llmAdvisorExplorationRescue"] is True, fresh
assert fresh["allowedProfiles"] == ["chain_terminal_extractor_v1"], fresh
assert fresh["action"] == "probe-targeted-repair", fresh

repeated = with_advice([*memory, {
    "providerId": "synthetic-generation",
    "failureClass": "chain_terminal_gap",
    "profile": "chain_terminal_extractor_v1",
    "llmAdvisorExperimentFingerprint": "a" * 64,
    "consecutiveFailures": 1, "failures": 1,
    "executionObserved": True,
}], advice)
assert repeated["llmAdvisorApplied"] is False, repeated
assert repeated["action"] == "collect-more-evidence", repeated

without_fingerprint = with_advice(memory, [{
    **advice[0], "experimentFingerprint": "",
}])
assert without_fingerprint["llmAdvisorApplied"] is False, without_fingerprint
assert without_fingerprint["action"] == "collect-more-evidence", without_fingerprint

still_evolving = with_advice(base, advice)
assert still_evolving["strategyEscalated"] is True, still_evolving
assert still_evolving["llmAdvisorApplied"] is False, still_evolving
assert still_evolving["allowedProfiles"] == ["terminal_transition_graph_v1"], still_evolving
print("Exhausted Learning LLM novelty/negative-memory replay passed")
