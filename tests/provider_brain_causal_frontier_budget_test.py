#!/usr/bin/env python3
"""A changed negative-memory file is not itself causal repair progress."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "family_frontier_guard", ROOT / "scripts/run_provider_brain_repair.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
guard = module.repeated_wave_no_frontier

base = {
    "remaining_count": 5,
    "accepted_count": 0,
    "exploration_progress_count": 0,
    "advisor_rotation_pending": False,
    "observation_complete": True,
}
assert not guard(wave=1, **base), "first negative wave may motivate a new hypothesis"
assert guard(wave=2, **base), "second no-gain wave must stop profile replay"
assert guard(wave=3, **base)
for variation in (
    {"remaining_count": 0},
    {"accepted_count": 1},
    {"exploration_progress_count": 1},
    {"advisor_rotation_pending": True},
    {"observation_complete": False},
):
    current = {**base, **variation}
    assert not guard(wave=2, **current), current

# The ordinary planner may still rotate a genuinely new executed hypothesis.
assert module.experiment_rotation_decision(
    accepted_count=0, remaining_count=5, wave=2,
    max_waves=6, memory_advanced=True,
) == "rotate"
print("Brain causal frontier no-gain rotation guard passed")
