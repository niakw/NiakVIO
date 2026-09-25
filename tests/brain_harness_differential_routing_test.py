#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
adaptive = (ROOT / "scripts" / "run_adaptive_deep_repair.py").read_text(encoding="utf-8")
runtime = (ROOT / "scripts" / "brain_repair_runtime.py").read_text(encoding="utf-8")
portfolio = (ROOT / "scripts" / "run_provider_brain_repair.py").read_text(encoding="utf-8")

for token in (
    "audit_harness_differential",
    "same-byte-nuvio-worker-request-differential",
    'plan["repairScope"] = "harness-compatibility"',
    'plan["allowedProfiles"] = []',
    "if provider in _HARNESS_DIFFERENTIAL_PROVIDERS:",
):
    assert token in adaptive, token

assert "harness_differential_plan(plan)" in runtime
assert '"harnessDifferentialProviders": sorted(harness_differential_providers)' in runtime
assert "not in harness_differential_providers" in runtime

for token in (
    "all_harness_differential",
    '"harnessDifferentialProviders": sorted(all_harness_differential)',
    '"harnessDifferentialExcludedFromLearningDebt": True',
    "deferred.difference_update(harness_differential)",
):
    assert token in portfolio, token

print("Brain harness differential routing contract passed")
