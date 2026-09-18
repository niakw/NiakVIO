#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_provider_repair_pipeline_v6 import unresolved_target_scope

active = ["green-a", "repair-b", "unknown-c", "green-d"]
disposition = {
    "providers": [
        {"provider": "green-a", "routeDataState": "on"},
        {"provider": "repair-b", "routeDataState": "repair"},
        {"provider": "green-d", "routeDataState": "on"},
    ]
}

targets, excluded = unresolved_target_scope(active, set(), set(), disposition)
assert targets == ["repair-b", "unknown-c"], (targets, excluded)
assert excluded == ["green-a", "green-d"], (targets, excluded)

targets, excluded = unresolved_target_scope(active, {"repair-b"}, set(), disposition)
assert targets == ["unknown-c"], (targets, excluded)
assert excluded == ["green-a", "green-d"], (targets, excluded)

targets, excluded = unresolved_target_scope(active, set(), {"green-a"}, disposition)
assert targets == ["green-a"], (targets, excluded)
assert excluded == [], (targets, excluded)

print("provider repair unresolved scope passed")
