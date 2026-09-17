#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "build_provider_certification_learning_queue.py"
spec = importlib.util.spec_from_file_location("queue", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

payload = {
    "authority": "exact-bundle-playable-lane-certification-v1",
    "manifestVersion": "x",
    "activeProviderCount": 4,
    "certifiedActiveProviderCount": 1,
    "providers": [
        {"providerId": "a", "enabled": True, "certified": False, "missingTypes": ["movie"], "lanes": {"movie": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_zero_result"}]}}},
        {"providerId": "b", "enabled": True, "certified": False, "missingTypes": ["movie"], "lanes": {"movie": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_zero_result"}]}}},
        {"providerId": "c", "enabled": True, "certified": False, "missingTypes": ["tv"], "lanes": {"tv": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_exception"}]}}},
        {"providerId": "d", "enabled": True, "certified": True, "missingTypes": [], "lanes": {}},
    ],
}
out = mod.build(payload)
assert out["clusters"][0]["providerCount"] == 2
assert out["clusters"][0]["failureClass"] == "route_or_catalog_resolution"
assert out["clusters"][0]["providers"] == ["a", "b"]
assert any(row["failureClass"] == "runtime_compatibility" for row in out["clusters"])
print("provider certification cluster-learning tests passed")
