#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_provider_repair_pipeline_v6 import dynamic_variant_gap_providers, static_variant_gap_providers, unresolved_target_scope

active = ["green-a", "repair-b", "waf-c", "route-d", "partial-e"]
census = {
    "providers": [
        {"provider": "green-a", "status": "FULL OK"},
        {"provider": "repair-b", "status": "PROVIDER JS BROKEN"},
        {"provider": "waf-c", "status": "HARNESS/ENV BLOCKED"},
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

# Dynamic sharded variant debt is an additional current symptom authority.
# A stable provider may re-enter Repair only when bounded current execution
# proves announced/explored/returned completeness loss.
dynamic = dynamic_variant_gap_providers({
    "rows": [
        {
            "provider_id": "green-a",
            "semantic_type": "movie",
            "announced_variant_candidates": 19,
            "streams_returned": 2,
            "variant_fanout_state": "returned-subset",
        },
        {
            "provider_id": "partial-e",
            "semantic_type": "movie",
            "announced_variant_candidates": 2,
            "streams_returned": 2,
            "variant_fanout_state": "fanout-observed",
        },
    ]
})
assert dynamic == {"green-a"}, dynamic

static = static_variant_gap_providers({
    "schemaVersion": 1,
    "role": "static-runtime-variant-coverage-debt",
    "proofAuthority": False,
    "highRiskProviders": ["partial-e", "green-a"],
})
assert static == {"partial-e", "green-a"}, static
assert static_variant_gap_providers({
    "role": "static-runtime-variant-coverage-debt",
    "proofAuthority": True,
    "highRiskProviders": ["green-a"],
}) == set()

targets, excluded = unresolved_target_scope(
    active,
    set(),
    {"green-a", "repair-b"},
    census=census,
    additional_symptoms=dynamic,
)
assert targets == ["green-a", "repair-b"], (targets, excluded)

targets, excluded = unresolved_target_scope(
    active,
    set(),
    set(),
    census=census,
    additional_symptoms=dynamic,
)
assert targets == ["green-a", "repair-b", "route-d"], (targets, excluded)

targets, excluded = unresolved_target_scope(
    active,
    set(),
    {"partial-e"},
    census=census,
    additional_symptoms=dynamic | static,
)
assert targets == ["partial-e"], (targets, excluded)

# Historical provider-wide skip is only an optimization. A current repairQueue
# entry reopens the provider and must outrank stale/exact-byte skip memory.
targets, excluded = unresolved_target_scope(active, {"repair-b"}, set(), census=census)
assert targets == ["repair-b", "route-d"], (targets, excluded)

# Independent authority blockers remain a hard Repair prerequisite.
targets, excluded = unresolved_target_scope(
    active,
    {"repair-b"},
    set(),
    census=census,
    authority_blocked={"repair-b"},
)
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
