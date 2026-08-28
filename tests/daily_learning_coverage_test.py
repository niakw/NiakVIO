#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_daily_learning_coverage.py"

spec = importlib.util.spec_from_file_location("validate_daily_learning_coverage", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

manifest = {"scrapers": [{"id": "alpha"}, {"id": "beta"}]}
stage = {
    "candidates": [
        {"key": "upstream:alpha", "canonical_id": "alpha"},
        {"key": "upstream:beta", "canonical_id": "beta"},
        {"key": "upstream:disabled", "canonical_id": "disabled"},
    ]
}
health = {
    "results": [
        {"key": "upstream:alpha", "status": "healthy"},
        {"key": "upstream:beta", "status": "no_streams"},
        {"key": "upstream:disabled", "status": "provider_unreachable"},
    ]
}
summary = module.validate_coverage(manifest, stage, health)
assert summary["complete"] is True, summary
assert summary["publishedProviderCount"] == 2, summary
assert summary["observedPublishedProviderCount"] == 2, summary
assert summary["coverageRatio"] == 1.0, summary
assert summary["extraObservedProviders"] == ["disabled"], summary

missing = module.validate_coverage(
    manifest,
    stage,
    {"results": [{"key": "upstream:alpha", "status": "healthy"}]},
)
assert missing["complete"] is False, missing
assert missing["missingPublishedProviders"] == ["beta"], missing

print("daily Learning coverage tests passed")
