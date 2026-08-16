#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "run_adaptive_quick_repair.py"
spec = importlib.util.spec_from_file_location("run_adaptive_quick_repair", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

config = {
    "modes": {
        "quick": {
            "fixture_limit": 1,
            "max_streams_to_probe": 1,
            "probe_best_variant": False,
            "probe_first_segment": False,
            "probe_streams_adaptively": False,
            "verify_fixture_duration_identity": False,
        },
        "deep": {
            "fixture_limit": 1,
            "max_streams_to_probe": 10,
            "probe_best_variant": True,
            "probe_first_segment": True,
            "probe_streams_adaptively": True,
            "fallback_fixture_limit_per_category": 3,
            "minimum_fixture_duration_ratio": 0.55,
            "maximum_fixture_duration_ratio": 1.8,
        },
    }
}
original_deep = copy.deepcopy(config["modes"]["deep"])
module._strengthen_quick_probe(config)
quick = config["modes"]["quick"]

assert quick["fixture_limit"] == 3
assert quick["max_streams_to_probe"] == 2
assert quick["probe_best_variant"] is True
assert quick["probe_first_segment"] is True
assert quick["probe_streams_adaptively"] is True
assert quick["verify_fixture_duration_identity"] is True
assert quick["minimum_fixture_duration_ratio"] == 0.55
assert quick["maximum_fixture_duration_ratio"] == 1.8

assert config["modes"]["deep"] == original_deep
assert config["modes"]["deep"]["max_streams_to_probe"] == 10
assert config["modes"]["deep"]["fallback_fixture_limit_per_category"] == 3

source = path.read_text(encoding="utf-8")
assert 'mode="quick"' in source
assert 'modes["deep"] = copy.deepcopy(quick)' not in source

# Brain mutation/loop budgets are executable and shared by canonical family,
# not reset for every upstream sibling.
brain = module.brain
brain.reset_runtime_state()
brain.PLANS.update({
    "source:one": {"action": "probe-targeted-repair", "signature": "same-signature", "failureClass": "search_gap", "providerId": "budget-provider"},
    "source:two": {"action": "probe-targeted-repair", "signature": "same-signature", "failureClass": "search_gap", "providerId": "budget-provider"},
})
calls = []

def fake_create(stage, candidate, profile_name, round_number):
    calls.append((candidate["key"], profile_name, round_number))
    repaired = dict(candidate)
    repaired["bytes"] = int(candidate.get("bytes") or 0) + 50
    return repaired, None

bounded_create = brain.wrap_create_repair_candidate(fake_create)
candidate_one = {"key": "source:one", "canonical_id": "budget-provider", "bytes": 100}
candidate_two = {"key": "source:two", "canonical_id": "budget-provider", "bytes": 100}
first, first_error = bounded_create(ROOT, candidate_one, "adaptive_runtime_recovery", 1)
second, second_error = bounded_create(ROOT, candidate_two, "adaptive_runtime_recovery", 1)
third, third_error = bounded_create(ROOT, candidate_one, "adaptive_runtime_recovery", 2)
assert first is not None and first_error is None
assert second is not None and second_error is None
assert third is None
assert third_error == "brain_mutation_budget_exhausted"
assert len(calls) == 2
budget = brain.runtime_state_snapshot()["budget-provider"]
assert budget["mutationCount"] == 2
assert budget["generatedBytes"] == 100
assert budget["signatureCounts"]["same-signature"] == 2
brain.reset_runtime_state()

print("quick repair probe profile test passed")
