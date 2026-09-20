#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_provider_repair_pipeline_v6 import unresolved_target_scope

active = ["green-a", "repair-b", "waf-c", "route-d", "partial-e"]
census = {
    "providers": [
        {"provider": "green-a", "status": "FULL OK"},
        {"provider": "repair-b", "status": "PROVIDER JS BROKEN"},
        {"provider": "waf-c", "status": "PROVIDER WAF/ANTIBOT"},
        {"provider": "route-d", "status": "ROUTE PROVEN"},
        {"provider": "partial-e", "status": "PARTIAL OK"},
    ],
    "brainQueue": ["repair-b", "waf-c", "route-d"],
    "repairQueue": ["repair-b", "route-d"],
    "environmentQueue": ["waf-c"],
}

targets, excluded = unresolved_target_scope(active, set(), set(), census=census)
assert targets == ["repair-b", "route-d"], (targets, excluded)
assert set(excluded) == {"green-a", "waf-c", "partial-e"}, (targets, excluded)

# Explicit requests do not override the census: a stable provider cannot be
# dragged back into Repair by stale operator/disposition state.
targets, excluded = unresolved_target_scope(active, set(), {"green-a", "repair-b"}, census=census)
assert targets == ["repair-b"], (targets, excluded)

# Skip still has final veto authority.
targets, excluded = unresolved_target_scope(active, {"repair-b"}, set(), census=census)
assert targets == ["route-d"], (targets, excluded)

# Legacy fallback remains deterministic for compatibility callers only.
disposition = {
    "providers": [
        {"provider": "green-a", "routeDataState": "on"},
        {"provider": "repair-b", "routeDataState": "repair"},
        {"provider": "partial-e", "routeDataState": "on"},
    ]
}
targets, _ = unresolved_target_scope(active, set(), set(), disposition)
assert "repair-b" in targets

print("provider repair census scope passed")
