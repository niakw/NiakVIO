#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_retest.py"
spec = importlib.util.spec_from_file_location("provider_retest", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

status = {
    "providers": [
        {"provider": "full", "status": "FULL OK"},
        {"provider": "partial", "status": "PARTIAL OK"},
        {"provider": "route", "status": "ROUTE PROVEN"},
        {"provider": "harness", "status": "HARNESS MISMATCH"},
        {"provider": "disabled", "status": "DISABLED"},
        {"provider": "rediscover", "status": "ROUTE PROVEN"},
    ],
    "repairQueue": ["route"],
}
authority = {
    "providers": [
        {"provider": "full", "action": "KEEP_DIRECT", "repairEligible": True, "authorityClass": "direct"},
        {"provider": "partial", "action": "KEEP_DIRECT", "repairEligible": True, "authorityClass": "direct"},
        {"provider": "route", "action": "KEEP_DIRECT", "repairEligible": True, "authorityClass": "direct"},
        {"provider": "harness", "action": "KEEP_DIRECT", "repairEligible": True, "authorityClass": "direct"},
        {"provider": "disabled", "action": "KEEP_DISABLED", "repairEligible": False, "authorityClass": "disabled"},
        {"provider": "rediscover", "action": "REDISCOVER_SEARCH", "repairEligible": False, "authorityClass": "unproven-direct-candidate"},
    ]
}

assert mod.select_providers(status, authority, scope="non-full", requested=set()) == [
    "harness", "partial", "route"
]
assert mod.select_providers(status, authority, scope="repair", requested=set()) == ["route"]
assert mod.select_providers(status, authority, scope="all", requested=set()) == [
    "full", "harness", "partial", "route"
]
assert mod.select_providers(
    status, authority, scope="non-full", requested={"disabled"}
) == ["disabled"]
assert mod.select_providers(
    status, authority, scope="non-full", requested={"rediscover"}
) == ["rediscover"]

source = SCRIPT.read_text(encoding="utf-8")
for forbidden in (
    "materialize_provider_v3_all.py",
    "materialize_provider_v3_one.py",
    "run_provider_brain_repair.py",
    "recover_provider_routes_from_upstreams.py",
    "apply_provider_route_recovery_report.py",
):
    assert forbidden not in source, forbidden
for required in (
    "audit_provider_quick_yield.py",
    "render_provider_census_status.py",
    "merge_waf_census_transport.py",
    "render_provider_census_status_from_state.py",
    "build_provider_repair_batch_plan.py",
):
    assert required in source, required

print("provider retest scope contract passed")
