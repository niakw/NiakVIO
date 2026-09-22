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

info = {
    "uhdmovies": {"status": "healthy"},
    "wookafr": {"status": "no_streams"},
    "other": {"status": "runtime_error"},
}
staged = {key: {"canonical_id": key} for key in info}
census = {"repairQueue": ["wookafr", "other"]}
current, deferred, authority = mod.current_repair_priority(
    ["uhdmovies", "other"],
    census,
    info,
    staged,
)
assert current == ["wookafr", "other"], current
assert deferred == ["other"], deferred
assert authority == "provider-census-status.json"

fallback_current, fallback_deferred, fallback_authority = mod.current_repair_priority(
    ["uhdmovies", "wookafr"],
    {},
    info,
    staged,
)
assert fallback_current == ["wookafr"], fallback_current
assert fallback_deferred == ["wookafr"], fallback_deferred
assert fallback_authority == "learning-current-observation-fallback"

ordered = mod.authoritative_learning_order(
    ["1shows", "animepahe", "wookafr", "other"],
    ["other"],
    ["wookafr", "other"],
    ["other"],
    ["1shows", "animepahe"],
    {
        "1shows": {"status": "provider_unreachable"},
        "animepahe": {"status": "provider_unreachable"},
        "wookafr": {"status": "no_streams"},
        "other": {"status": "runtime_error"},
    },
    {
        "1shows": {"canonical_id": "1shows"},
        "animepahe": {"canonical_id": "animepahe"},
        "wookafr": {"canonical_id": "wookafr"},
        "other": {"canonical_id": "other"},
    },
)
assert ordered == ["other", "wookafr", "1shows", "animepahe"], ordered

source = (ROOT / "scripts" / "run_brain_learning_queue.py").read_text(encoding="utf-8")
assert "authoritative_learning_order(" in source
assert "current census is the first Learning authority" in source
assert "fastRepairHandoffProviders" in source
assert "provider-repair-learn-handoff-v1.json" in source
assert "fastRepairHandoffMaxAttemptsPerProviderThisPhase" in source
assert "FIELD_BRAIN_HANDOFF_FAIR_SHARE" in source
assert "FIELD_BRAIN_HANDOFF_SLICE_EXHAUSTED" in source
assert "provider_deadline" in source
assert "min(" in source and "120" in source
assert "if fair_handoff and attempts_this_phase >= 1" in source

print("Brain Learning exhausted-Repair priority contract passed")
