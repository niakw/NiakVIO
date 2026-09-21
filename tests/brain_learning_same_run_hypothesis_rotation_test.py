#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_brain_learning_queue.py"

spec = importlib.util.spec_from_file_location("brain_learning_queue_rotation", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def report(variant: int, generation: int = 1) -> dict:
    return {
        "brain": {
            "plans": {
                "aio:demo": {
                    "providerId": "demo",
                    "failureClass": "search_gap",
                    "signature": "search-gap:route-proven",
                    "experimentVariant": variant,
                    "experimentGeneration": generation,
                    "allowedProfiles": ["adaptive_runtime_recovery"],
                }
            }
        }
    }


v0 = module.repair_method_fingerprints(report(0), ["adaptive_runtime_recovery"])
v1 = module.repair_method_fingerprints(report(1), ["adaptive_runtime_recovery"])
g2 = module.repair_method_fingerprints(report(0, 2), ["adaptive_runtime_recovery"])
assert v0 and v1 and g2
assert v0 != v1, (v0, v1)
assert v0 != g2, (v0, g2)
assert v0 == module.repair_method_fingerprints(report(0), ["adaptive_runtime_recovery"])
assert module.repair_method_fingerprints({}, ["adaptive_runtime_recovery"]) == [
    "profile:adaptive_runtime_recovery"
]

source = SCRIPT.read_text(encoding="utf-8")
assert 'method_set = tuple(repair["attemptedMethods"])' in source
assert '"attemptedMethods": repair["attemptedMethods"]' in source
assert 'if method_set in seen_method_sets or not method_set:' in source
assert 'if repair["accepted"] == 0:\n                    continue' in source
assert 'if repair["accepted"] == 0:\n                    break' not in source

print("Brain Learning same-run causal hypothesis rotation contract passed")
