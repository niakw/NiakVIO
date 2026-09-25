#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_learning_dispatch_gate.py"
spec = importlib.util.spec_from_file_location("dispatch_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def brain(signature="sig-a", profile="chain_terminal_extractor_v1", harness=None):
    return {
        "deferredLearningProviders": ["demo", "harness"],
        "harnessDifferentialProviders": list(harness or []),
        "waves": [{
            "batches": [{
                "brain": {
                    "plans": {
                        "demo-key": {
                            "providerId": "demo",
                            "failureClass": "chain_terminal_gap",
                            "signature": signature,
                            "repairScope": "provider",
                            "repairType": "targeted_runtime",
                            "learningDisposition": "invent-new-strategy",
                            "allowedProfiles": [profile],
                            "experimentVariant": 4,
                            "experimentGeneration": 2,
                            "llmAdvisorStrategy": "",
                            "llmAdvisorProfile": "",
                            "llmAdvisorExperimentFingerprint": "",
                        },
                        "harness-key": {
                            "providerId": "harness",
                            "failureClass": "route_proven_gap",
                            "signature": "harness-sig",
                            "repairScope": "harness-compatibility",
                            "repairType": "harness_differential",
                            "learningDisposition": "harness-fix-required-before-provider-learning",
                            "allowedProfiles": [],
                        },
                    }
                }
            }]
        }],
    }


first = module.select(brain(harness=["harness"]), {"providers": {}}, ["demo", "harness"])
assert first["eligibleProviders"] == ["demo"], first
assert first["harnessDifferentialExcludedProviders"] == ["harness"], first
fp = first["eligible"][0]["fingerprint"]
assert len(fp) == 64

ledger = module.mark_dispatched(
    {"schemaVersion": 1, "providers": {}},
    first,
    repair_run_id="repair-1",
    learning_run_id="learn-1",
)
assert ledger["providers"]["demo"]["lastDispatchedFingerprint"] == fp
assert ledger["providers"]["demo"]["dispatchCount"] == 1

repeat = module.select(brain(harness=["harness"]), ledger, ["demo", "harness"])
assert repeat["eligibleProviders"] == [], repeat
assert repeat["suppressedRepeatProviders"] == ["demo"], repeat

changed = module.select(brain(signature="sig-b", harness=["harness"]), ledger, ["demo"])
assert changed["eligibleProviders"] == ["demo"], changed
assert changed["eligible"][0]["fingerprint"] != fp

changed_method = module.select(
    brain(profile="player_media_extractor_v1", harness=["harness"]),
    ledger,
    ["demo"],
)
assert changed_method["eligibleProviders"] == ["demo"], changed_method
assert changed_method["eligible"][0]["fingerprint"] != fp

missing = {
    "deferredLearningProviders": ["unknown"],
    "waves": [{"batches": [{"brain": {"plans": {
        "x": {
            "providerId": "unknown",
            "failureClass": "unknown_failure",
            "signature": "unknown-sig",
            "allowedProfiles": [],
        }
    }}}]}],
}
closed = module.select(missing, {"providers": {}}, ["unknown"])
assert closed["eligibleProviders"] == [], closed
assert closed["suppressedMissingFingerprintProviders"] == ["unknown"], closed

print("Provider Learning causal dispatch gate tests passed")
