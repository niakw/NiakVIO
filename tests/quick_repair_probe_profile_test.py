#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
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

# The Python -> Node planner boundary must survive both Python-only numeric JSON
# values and malformed Unicode copied from remote pages. The transport itself is
# ASCII-only escaped JSON and Node parses the exact bytes used in production.
strict_payload = brain._strict_json_dumps({
    "finite": 1.25,
    "nan": float("nan"),
    "positiveInfinity": float("inf"),
    "negativeInfinity": float("-inf"),
    "unicode": "é漢字",
    "loneHighSurrogate": "\ud800",
    "loneLowSurrogate": "\udfff",
    "nested": [float("nan"), {"latency": float("inf")}],
})
parsed_payload = json.loads(strict_payload)
assert parsed_payload["finite"] == 1.25
assert parsed_payload["nan"] is None
assert parsed_payload["positiveInfinity"] is None
assert parsed_payload["negativeInfinity"] is None
assert parsed_payload["unicode"] == "é漢字"
assert parsed_payload["loneHighSurrogate"] == "\ud800"
assert parsed_payload["loneLowSurrogate"] == "\udfff"
assert parsed_payload["nested"] == [None, {"latency": None}]
assert strict_payload.isascii()
node_parse = subprocess.run(
    ["node", "-e", "JSON.parse(require('fs').readFileSync(0, 'utf8'))"],
    input=strict_payload.encode("ascii"),
    capture_output=True,
    check=False,
)
assert node_parse.returncode == 0, node_parse.stderr.decode("utf-8", errors="replace")

# The planner receives only fields needed for causal classification, not whole
# live candidates/results. This bounds input size and keeps raw page/network data
# out of the control-plane transport.
minimal_candidate = brain._planner_candidate({
    "canonical_id": "demo",
    "upstream_id": "demo-upstream",
    "metadata": {"supportedTypes": ["movie", "tv"], "rawHomepage": "DROP"},
    "source": "DROP",
})
assert minimal_candidate == {
    "canonical_id": "demo",
    "upstream_id": "demo-upstream",
    "metadata": {"supportedTypes": ["movie", "tv"]},
}
minimal_result = brain._planner_result({
    "status": "blocked",
    "raw_html": "DROP",
    "evidence": {"streams_playable": 0, "private": "DROP"},
    "tests": [{
        "failure_class": "provider_http_blocked",
        "status": "blocked",
        "error_details": {"code": "HTTP_403", "message": "x" * 2000, "secret": "DROP"},
        "network_observations": [{"status": 403, "infrastructure": False, "url": "DROP"}],
        "fixture": {"category": "movie", "title": "DROP"},
        "streams_playable": 0,
    }],
})
assert "raw_html" not in minimal_result
assert "private" not in minimal_result["evidence"]
assert "secret" not in minimal_result["tests"][0]["error_details"]
assert "url" not in minimal_result["tests"][0]["network_observations"][0]
assert len(minimal_result["tests"][0]["error_details"]["message"]) == 600

brain_source = (ROOT / "scripts" / "brain_repair_runtime.py").read_text(encoding="utf-8")
assert "ensure_ascii=True" in brain_source
assert "allow_nan=False" in brain_source
assert 'encode("ascii")' in brain_source
assert '"candidate": _planner_candidate(candidate)' in brain_source
assert '"result": _planner_result(result)' in brain_source

print("quick repair probe profile test passed")
