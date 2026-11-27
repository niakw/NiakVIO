#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/run_brain_learning_queue.py"
source = path.read_text(encoding="utf-8")

assert "route_refresh_with_budget_scope(" in source
assert "route_search(provider_id, run_dir, work_deadline)" not in source
assert "refresh_stage_routes(stage, work_deadline, provider_id)" not in source
assert source.count("route_refresh_with_budget_scope(") >= 3  # definition + two call sites

spec = importlib.util.spec_from_file_location("brain_learning_fair_share_route_deadline", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def route_timeout(_provider, _run_dir, _deadline):
    raise mod.BudgetExhausted("provider route slice")

def route_ok(_provider, _run_dir, _deadline):
    return {"resolverStatus": 0, "routeEvidenceCount": 1}

def refresh_timeout(_stage, _deadline, _provider):
    raise mod.BudgetExhausted("provider refresh slice")

local_route, local_refresh = mod.route_refresh_with_budget_scope(
    "provider-a", Path("."), Path("."), 100.0, 1000.0, True,
    route_search_fn=route_timeout,
    refresh_fn=lambda *_args: {"ok": True},
)
assert local_route is None
assert local_refresh["ok"] is False and local_refresh["sliceExhausted"] is True
assert local_refresh["proofAuthority"] is False

preserved_route, refresh_result = mod.route_refresh_with_budget_scope(
    "provider-a", Path("."), Path("."), 100.0, 1000.0, True,
    route_search_fn=route_ok,
    refresh_fn=refresh_timeout,
)
assert preserved_route["routeEvidenceCount"] == 1
assert refresh_result["sliceExhausted"] is True

for fair_handoff, provider_deadline, work_deadline in (
    (False, 100.0, 1000.0),
    (True, 1000.0, 1000.0),
):
    try:
        mod.route_refresh_with_budget_scope(
            "provider-a", Path("."), Path("."), provider_deadline, work_deadline, fair_handoff,
            route_search_fn=route_timeout,
            refresh_fn=lambda *_args: {"ok": True},
        )
    except mod.BudgetExhausted:
        pass
    else:
        raise AssertionError("true global/non-fair BudgetExhausted was incorrectly localized")

print("Brain Learning fair-share route deadline contract passed local_slice_isolated=true global_budget_preserved=true")
