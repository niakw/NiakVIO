#!/usr/bin/env python3
"""Bounded Brain negative-memory retains underrepresented repair signatures."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "scripts/brain_negative_memory_retention.py"
spec = importlib.util.spec_from_file_location("brain_negative_memory_retention", source)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(provider, signature, failures):
    return {
        "providerId": provider,
        "signature": signature,
        "profile": "runtime_response_salvage_v1",
        "failures": failures,
        "consecutiveFailures": failures,
        "experimentVariant": 4,
        "experimentGeneration": 2,
        "lastOutcome": "rejected",
    }


dominated = [row("4khdhub", f"legacy-{idx:04d}", 1000 - idx) for idx in range(1000)]
new = [
    row("animekai", "first-current-executed-timeout", 1),
    row("animesama-co", "first-new-candidate-network", 1),
    row("uhdmovies", "first-regressed-terminal-gap", 1),
]
retained = mod.select_bounded_negative_memory(dominated + new, limit=1000)
assert len(retained) == 1000
assert {r["providerId"] for r in retained} == {
    "4khdhub", "animekai", "animesama-co", "uhdmovies"
}, "newly executed providers must never disappear behind hot negative signatures"
assert len(mod.select_bounded_negative_memory(dominated + new, limit=14)) == 14
assert mod.select_bounded_negative_memory(dominated + new, limit=1000) == retained, "deterministic output"
assert len(mod.select_bounded_negative_memory(new, limit=3)) == 3
assert all(r["lastOutcome"] == "rejected" for r in retained)
print("Brain bounded negative memory retention tests passed")
