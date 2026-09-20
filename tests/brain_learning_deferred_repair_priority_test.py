#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "run_brain_learning_queue.py"
spec = importlib.util.spec_from_file_location("run_brain_learning_queue_priority_test", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

policy = {
    "production": {
        "negativeExperimentMemory": {
            "rotateExperimentAfterFailures": 1,
            "maxVariantsPerSignature": 4,
        }
    }
}

def row(provider: str, variant: int, *, signature: str = "sig", successes: int = 0, consecutive: int = 1):
    return {
        "providerId": provider,
        "failureClass": "chain_terminal_gap",
        "signature": signature,
        "profile": "adaptive_runtime_recovery",
        "experimentVariant": variant,
        "failures": 1,
        "consecutiveFailures": consecutive,
        "successes": successes,
    }

memory = {
    "entries": [
        *[row("exhausted-a", variant) for variant in range(4)],
        *[row("partial-b", variant) for variant in range(3)],
        *[row("resolved-c", variant, successes=1) for variant in range(4)],
        row("split-d", 0, signature="one"),
        row("split-d", 1, signature="one"),
        row("split-d", 2, signature="two"),
        row("split-d", 3, signature="two"),
    ]
}
assert mod.exhausted_repair_providers(memory, policy) == ["exhausted-a"]

policy2 = {
    "production": {
        "negativeExperimentMemory": {
            "rotateExperimentAfterFailures": 2,
            "maxVariantsPerSignature": 2,
        }
    }
}
memory2 = {"entries": [
    row("needs-two", 0, consecutive=2),
    row("needs-two", 1, consecutive=2),
    row("not-yet", 0, consecutive=1),
    row("not-yet", 1, consecutive=2),
]}
assert mod.exhausted_repair_providers(memory2, policy2) == ["needs-two"]

print("Brain Learning exhausted-Repair priority contract passed")
