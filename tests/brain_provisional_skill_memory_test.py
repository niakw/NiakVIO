#!/usr/bin/env python3
"""Real UHDMovies-like Quick 0->2 must not poison Brain success memory."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from repair_promotion_state import durable_accepted_event, provisional_accepted_event

quick = {
    "parent_key": "aio:uhdmovies", "profile": "route_transition_graph_v6",
    "reason": "provisional_quick_runtime_improvement",
    "streams_playable_after": 2, "durable_promotion_eligible": False,
    "identity_strict_reason": "identity_gate:no_positive_content_identity_proof",
    "brain_plan": {"providerId": "uhdmovies", "failureClass": "search_gap",
                   "signature": "original-uhdmovies-quick", "hypotheses": []},
}
strict = {
    "parent_key": "published:proven-provider", "profile": "adaptive_runtime_recovery",
    "reason": "strict_playable_stream_improvement", "streams_playable_after": 2,
    "durable_promotion_eligible": True,
    "identity_strict_reason": "positive_content_identity_proof",
    "brain_plan": {"providerId": "proven-provider", "failureClass": "search_gap",
                   "signature": "strict-identity-verified", "hypotheses": []},
}
assert provisional_accepted_event(quick) and not durable_accepted_event(quick)
assert durable_accepted_event(strict) and not provisional_accepted_event(strict)
assert not durable_accepted_event({**quick, "durable_promotion_eligible": True})
assert not durable_accepted_event({**strict, "identity_strict_reason": "unknown"})
assert durable_accepted_event({"reason": "strict_playable_stream_improvement"})

path = ROOT / "scripts" / "brain_repair_runtime.py"
spec = importlib.util.spec_from_file_location("brain_provisional_memory_test", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory(prefix="brain-provisional-skill-") as tmp:
    root = Path(tmp)
    out = root / "out"
    out.mkdir()
    overrides = root / "provider-overrides.json"
    memory = root / "brain-repair-memory.json"
    census = root / "census.json"
    policy = root / "policy.json"
    overrides.write_text(json.dumps({"runtime_repair":{"learned_skills":{}}}), encoding="utf-8")
    memory.write_text(json.dumps({"schemaVersion":1,"entries":[]}), encoding="utf-8")
    census.write_text(json.dumps({"providers":[]}), encoding="utf-8")
    policy.write_text(json.dumps({
        "identity":{"name":"NiakVIO Brain"},
        "production":{"learningOnValidatedRepair":True,
                      "negativeExperimentMemory":{"enabled":True,"maxEntries":100}},
        "skillMaturity":{"candidateSuccesses":2,"trustedSuccesses":4}
    }), encoding="utf-8")
    (out / "repair-report.json").write_text(json.dumps({
        "rounds":[{"round":1,"attempts":[],"accepted":[quick,strict],
                   "exploration_progress":[],"rejected":[]}]
    }), encoding="utf-8")
    mod.OVERRIDES_PATH = overrides
    mod.REPAIR_MEMORY_PATH = memory
    mod.CENSUS_STATUS_PATH = census
    mod.POLICY_PATH = policy
    mod.reset_runtime_state()
    mod.annotate_and_learn(out, "learning")
    cfg = json.loads(overrides.read_text(encoding="utf-8"))
    skills = cfg["runtime_repair"]["learned_skills"]
    assert all("route_transition_graph_v6" not in x for x in skills), skills
    assert "search_gap:adaptive_runtime_recovery" in skills, skills
    assert skills["search_gap:adaptive_runtime_recovery"]["successCount"] == 1, skills
    mem = json.loads(memory.read_text(encoding="utf-8"))["entries"]
    quick_memory = next(r for r in mem if r.get("providerId") == "uhdmovies")
    assert quick_memory["successes"] == 0, quick_memory
    assert quick_memory["failures"] == 0, quick_memory
    assert quick_memory["progresses"] >= 1, quick_memory
    assert quick_memory["lastOutcome"] == "provisional_quick_candidate_unverified", quick_memory
print("FIELD_BRAIN_PROVISIONAL_SKILL_NO_SUCCESS quick_retained=true "
      "false_positive_skills=0 strict_positive_skills=1")
