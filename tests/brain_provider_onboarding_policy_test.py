#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
policy = json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))
onboarding = policy.get("providerOnboarding") or {}
assert onboarding.get("minimumAutoCertificationRatio") == 0.75
assert onboarding.get("massDisableFractionCeiling") == 0.25
assert onboarding.get("lowYieldInterpretation") == "architecture_defect_not_provider_population_failure"
assert onboarding.get("clusterFirstRepair") is True
assert onboarding.get("repairOrder") == ["core_global", "capability_family", "provider_local_learning"]
assert onboarding.get("nodePositiveCanCertify") is True
assert onboarding.get("nodeNegativeCanDisable") is False
assert onboarding.get("nativeFallbackRequiredWhenNodeNegative") is True
assert onboarding.get("exactBundlePositiveWitnessRequiredForActivation") is True
print("brain provider onboarding yield policy tests passed")
