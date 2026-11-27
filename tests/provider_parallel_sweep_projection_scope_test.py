#!/usr/bin/env python3
"""Lock Repair sweep planning to the current active Global+France projection union."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_parallel_sweep_plan_v1 as planner  # noqa: E402
from current_provider_scope import active_provider_ids, projection_active_provider_ids  # noqa: E402

planned = planner.catalogue()
planned_set = set(planned)
projection = projection_active_provider_ids()
global_only = active_provider_ids()
france_only = projection - global_only

assert planned, "parallel sweep planner produced an empty executable scope"
assert len(planned) == len(planned_set), "parallel sweep planner duplicated provider identities"
assert planned_set == projection, (
    f"parallel sweep scope drift missing={sorted(projection-planned_set)} "
    f"extra={sorted(planned_set-projection)}"
)
assert france_only, "fixture requires at least one active France-only provider"
assert france_only <= planned_set, (
    "France-only active providers disappeared from Repair sweep planning: "
    + ",".join(sorted(france_only))
)

# Historical regression guards may outlive activation. They must not block the
# active-only parallel sweep, while explicit unknown operator requests remain
# fail-closed in the planner.
plan = planner.plan(24, 4)
trigger = planner.load(planner.TRIGGER) if planner.TRIGGER.exists() else {}
requested_guards = {
    planner.cid(value)
    for value in trigger.get("regressionGuardProviders") or []
    if planner.cid(value)
}
expected_stale = requested_guards - planned_set
assert set(plan["staleRegressionGuardProviders"]) == expected_stale, plan
assert not (set(plan["selectedProviders"]) & expected_stale), plan
assert "unknown explicit providers:" in (ROOT / "scripts/provider_parallel_sweep_plan_v1.py").read_text(encoding="utf-8")
assert "unknown explicit/guard providers:" not in (ROOT / "scripts/provider_parallel_sweep_plan_v1.py").read_text(encoding="utf-8")

workflow = (ROOT / ".github" / "workflows" / "provider-repair-parallel-sweep.yml").read_text(encoding="utf-8")
assert "projection_active_provider_rows" in workflow
assert "projection_active_provider_ids" in workflow
assert 'Path("manifest.json").read_text' not in workflow, "parallel Repair sweep must not regress to Global-only scope"
assert "parallel sweep projection drift" in workflow

print(
    "provider parallel sweep projection scope passed "
    f"providers={len(planned_set)} global={len(global_only)} france_only={len(france_only)}"
)
