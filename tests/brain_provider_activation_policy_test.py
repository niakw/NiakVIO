#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
policy = json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))
activation = policy.get("activationIntelligence") or {}
assert activation.get("activeRequiresPlayableCertification") is True
assert activation.get("catalogReachabilityIsNotActivationProof") is True
assert activation.get("positiveFixtureMemory") is True
assert activation.get("uncertifiedAction") == "disable_and_queue_learning"
assert activation.get("reenableRequiresFreshExactBundleCertificate") is True
assert activation.get("nativeAcceptance") == "FULL_required_for_every_active_provider_on_every_required_lab"
learning = policy.get("learningLab") or {}
assert learning.get("learnProviderPositiveFixtures") is True
assert learning.get("revalidateExactBundleWitnesses") is True
assert learning.get("catalogueDiscoveryBeforeRepair") is True
allowed = set(learning.get("selfArchitectureAllowedTargets") or [])
for required in (
    "scripts/certify_provider_playable_lanes.py",
    "scripts/learn_provider_positive_fixtures.py",
    "scripts/enforce_provider_activation_contract.py",
    "scripts/gate_native_declared_provider_matrix.py",
):
    assert required in allowed, required
print("Brain provider activation intelligence policy tests passed")
