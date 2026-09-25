#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "brain_repair_runtime.py"
spec = importlib.util.spec_from_file_location("brain_runtime_visibility", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

positive = {
    "id": "media_extraction_gap:adaptive_runtime_recovery",
    "validated": True,
    "maturity": "experimental",
    "confidence": 1.0,
    "providers": ["demo"],
    "successCount": 1,
    "failureCount": 0,
    "sameProviderPositiveProgram": True,
    "positiveProgramFingerprintsByProvider": {"demo": "a" * 64},
}
generic_experimental = {
    "id": "route:experimental",
    "validated": True,
    "maturity": "experimental",
    "confidence": 1.0,
    "providers": ["peer-a", "peer-b"],
    "successCount": 2,
    "failureCount": 0,
}
trusted = {
    "id": "route:trusted",
    "validated": True,
    "maturity": "trusted",
    "confidence": 1.0,
    "providers": ["peer-a", "peer-b"],
    "successCount": 4,
    "failureCount": 0,
}

old_learned = mod.learned_skills
old_policy = mod.policy
try:
    mod.learned_skills = lambda: {
        positive["id"]: positive,
        generic_experimental["id"]: generic_experimental,
        trusted["id"]: trusted,
    }
    mod.policy = lambda: {
        "production": {
            "learnedSkillInputAllowed": False,
            "learnedSkillTransferPolicy": {
                "maturity": "trusted",
                "minimumConfidence": 0.8,
                "minimumDistinctProviders": 2,
            },
        },
        "skillMaturity": {
            "minimumConfidence": 0.8,
            "trustedProviders": 2,
        },
    }
    closed = mod.planner_learned_skills("deep")
    assert set(closed) == {positive["id"]}, closed

    mod.policy = lambda: {
        "production": {
            "learnedSkillInputAllowed": True,
            "learnedSkillTransferPolicy": {
                "maturity": "trusted",
                "minimumConfidence": 0.8,
                "minimumDistinctProviders": 2,
            },
        },
        "skillMaturity": {
            "minimumConfidence": 0.8,
            "trustedProviders": 2,
        },
    }
    opened = mod.planner_learned_skills("deep")
    assert positive["id"] in opened, opened
    assert trusted["id"] in opened, opened
    assert generic_experimental["id"] not in opened, opened

    learning = mod.planner_learned_skills("learning")
    assert set(learning) == {positive["id"], generic_experimental["id"], trusted["id"]}, learning
finally:
    mod.learned_skills = old_learned
    mod.policy = old_policy

print("Brain Repair strict positive-program visibility contract passed")
