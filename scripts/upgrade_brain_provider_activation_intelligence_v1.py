#!/usr/bin/env python3
"""Upgrade Brain policy with provider-specific playable activation intelligence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "engine_v2/config/brain-policy.json"


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    data["schemaVersion"] = max(int(data.get("schemaVersion") or 0), 8)
    data["controlPlaneVersion"] = max(int(data.get("controlPlaneVersion") or 0), 6)
    data["activationIntelligence"] = {
        "activeRequiresPlayableCertification": True,
        "catalogReachabilityIsNotActivationProof": True,
        "certificateScope": "exact_bundle_plus_every_declared_semantic_lane",
        "positiveFixtureMemory": True,
        "positiveFixtureSelection": [
            "previous_provider_lane_witness",
            "provider_targeted_corpus",
            "deterministic_rotating_recent_corpus"
        ],
        "catalogueMissPolicy": "rotate_same_lane_before_failure_classification",
        "technicalFailurePolicy": "stop_catalogue_rotation_and_diagnose_causal_stage",
        "uncertifiedAction": "disable_and_queue_learning",
        "reenableRequiresFreshExactBundleCertificate": True,
        "nativeAcceptance": "FULL_required_for_every_active_provider_on_every_required_lab",
        "scaleTarget": "hundreds_of_providers_without_global_fixture_assumption"
    }
    learning = data.setdefault("learningLab", {})
    learning["learnProviderPositiveFixtures"] = True
    learning["revalidateExactBundleWitnesses"] = True
    learning["uncertifiedProvidersFirst"] = True
    learning["catalogueDiscoveryBeforeRepair"] = True
    learning["activationAuthority"] = "exact_bundle_playable_lane_certificate"
    allowed = learning.setdefault("selfArchitectureAllowedTargets", [])
    for path in (
        "scripts/certify_provider_playable_lanes.py",
        "scripts/learn_provider_positive_fixtures.py",
        "scripts/enforce_provider_activation_contract.py",
        "scripts/gate_native_declared_provider_matrix.py",
        "scripts/native_catalog_miss_rotation.py",
        "scripts/run_native_adaptive_catalog_fallbacks.sh",
        "automation/provider-positive-fixtures.json",
    ):
        if path not in allowed:
            allowed.append(path)
    daily = data.setdefault("executionLanes", {}).setdefault("dailyLearning", {})
    daily["positiveFixtureMemory"] = "learn_and_revalidate_provider_lane_witnesses"
    daily["activationRepairPriority"] = "uncertified_active_or_disabled_repair_candidates_first"
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("BRAIN_PROVIDER_ACTIVATION_INTELLIGENCE_V1 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
