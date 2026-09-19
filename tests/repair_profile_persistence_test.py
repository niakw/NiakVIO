#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from repair_profile_persistence import ensure_repair_profile  # noqa: E402

adaptive = {
    "runtime_repair": {
        "profile": "",
        "strategy": "adaptive_runtime_recovery",
    }
}
assert ensure_repair_profile(adaptive, "adaptive_runtime_recovery") is adaptive
assert adaptive["runtime_repair"]["profile"] == "adaptive_runtime_recovery"

explicit = {
    "runtime_repair": {
        "profile": "existing_profile",
        "strategy": "different_strategy",
    }
}
ensure_repair_profile(explicit, "requested_profile")
assert explicit["runtime_repair"]["profile"] == "existing_profile"

fallback = {"runtime_repair": {"profile": "", "strategy": ""}}
ensure_repair_profile(fallback, "requested_profile")
assert fallback["runtime_repair"]["profile"] == "requested_profile"

assert ensure_repair_profile(None, "x") is None
assert ensure_repair_profile({}, "x") == {}

print("repair profile persistence test passed")
