#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "validate_learning_health_baseline.py"
spec = importlib.util.spec_from_file_location("validate_learning_health_baseline", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

catalog = {
    "providers": [{"canonicalId": f"p{i}"} for i in range(10)]
}
stage = {
    "candidates": [
        {"key": f"aio:p{i}", "canonical_id": f"p{i}"}
        for i in range(10)
    ] + [
        {"key": "aio:future", "canonical_id": "future-provider"}
    ]
}

def runtime_row(i: int, message: str = "NIAKVIO_PROVIDER_MODEL is not defined"):
    return {
        "key": f"aio:p{i}",
        "status": "runtime_error",
        "tests": [{
            "error_details": {
                "name": "ReferenceError",
                "code": None,
                "message": message,
            }
        }],
    }

collapsed = {
    "results": [runtime_row(i) for i in range(9)] + [
        {"key": "aio:p9", "status": "no_streams", "tests": []},
        runtime_row(0, "future should not matter") | {"key": "aio:future"},
    ]
}
summary = mod.validate(catalog, stage, collapsed)
assert summary["observedCurrentProviderCount"] == 10, summary
assert summary["runtimeErrorProviderCount"] == 9, summary
assert summary["runtimeErrorRatio"] == 0.9, summary
assert summary["catastrophicCommonRuntimeCollapse"] is True, summary
assert summary["dominantRuntimeError"]["name"] == "ReferenceError", summary
assert "NIAKVIO_PROVIDER_MODEL" in summary["dominantRuntimeError"]["message"], summary
assert "future-provider" not in summary["runtimeErrorProviders"], summary

mixed = {
    "results": [
        runtime_row(0),
        runtime_row(1),
        {"key": "aio:p2", "status": "blocked", "tests": []},
        {"key": "aio:p3", "status": "provider_unreachable", "tests": []},
        {"key": "aio:p4", "status": "no_streams", "tests": []},
        {"key": "aio:p5", "status": "unavailable", "tests": []},
        {"key": "aio:p6", "status": "healthy", "tests": []},
        {"key": "aio:p7", "status": "no_streams", "tests": []},
        {"key": "aio:p8", "status": "blocked", "tests": []},
        {"key": "aio:p9", "status": "no_streams", "tests": []},
    ]
}
summary = mod.validate(catalog, stage, mixed)
assert summary["catastrophicCommonRuntimeCollapse"] is False, summary
assert summary["runtimeErrorProviderCount"] == 2, summary

# A tiny targeted Learning invocation must not be rejected by the portfolio
# collapse heuristic merely because its one provider failed at runtime.
tiny_catalog = {"providers": [{"canonicalId": "only"}]}
tiny_stage = {"candidates": [{"key": "aio:only", "canonical_id": "only"}]}
tiny_health = {"results": [{
    "key": "aio:only",
    "status": "runtime_error",
    "tests": [{"error_details": {"name": "ReferenceError", "message": "x is not defined"}}],
}]}
summary = mod.validate(tiny_catalog, tiny_stage, tiny_health)
assert summary["catastrophicCommonRuntimeCollapse"] is False, summary

print("Learning common-runtime-collapse baseline contract passed")
