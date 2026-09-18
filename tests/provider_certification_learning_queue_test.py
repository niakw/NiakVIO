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
    "manifestProviderCount": 46,
    "selectedProviderCount": 5,
    "selectedActiveProviderCount": 4,
    "certifiedProviderCount": 1,
    "activeProviderCount": 4,
    "certifiedActiveProviderCount": 1,
    "fullManifestCensus": False,
    "providers": [
        {"providerId": "a", "enabled": True, "certified": False, "missingTypes": ["movie"], "lanes": {"movie": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_zero_result"}]}}},
        {"providerId": "b", "enabled": True, "certified": False, "missingTypes": ["movie"], "lanes": {"movie": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_zero_result"}]}}},
        {"providerId": "c", "enabled": True, "certified": False, "missingTypes": ["tv"], "lanes": {"tv": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_exception"}]}}},
        {"providerId": "d", "enabled": True, "certified": True, "missingTypes": [], "lanes": {}},
        {"providerId": "e", "enabled": False, "certified": False, "missingTypes": ["movie"], "lanes": {"movie": {"state": "uncertified", "attemptCount": 2, "attempts": [{"debugStage": "provider_network_exception"}]}}},
    ],
}
out = mod.build(payload)
assert out["clusters"][0]["providerCount"] == 2
assert out["clusters"][0]["failureClass"] == "route_or_catalog_resolution"
assert out["clusters"][0]["providers"] == ["a", "b"]
assert any(row["failureClass"] == "runtime_compatibility" for row in out["clusters"])
assert out["manifestProviderCount"] == 46
assert out["selectedProviderCount"] == 5
assert out["repairEligibleProviderCount"] == 3
assert out["disabledRetainedProviderCount"] == 1
assert [row["providerId"] for row in out["disabledProviders"]] == ["e"]
assert "e" not in {row["providerId"] for row in out["providers"]}
assert all("e" not in row["providers"] for row in out["clusters"])
assert out["fullManifestCensus"] is False
assert out["autoCertificationRatio"] is None
assert out["architectureState"] == "targeted-diagnostic-no-global-yield"

full = dict(payload)
full.update({
    "selectedProviderCount": 46,
    "certifiedProviderCount": 35,
    "fullManifestCensus": True,
})
full_out = mod.build(full)
assert full_out["fullManifestCensus"] is True
assert full_out["autoCertificationRatio"] == round(35 / 46, 4)
assert full_out["architectureState"] == "auto-yield-sufficient"

print("provider certification cluster-learning tests passed")
