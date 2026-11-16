#!/usr/bin/env python3
"""Stale route history must not block or mutate newly active catalogue providers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_provider_route_recovery_report as apply_report  # noqa: E402
import merge_provider_repair_report_v6 as merge_report  # noqa: E402


baseline = {
    "schemaVersion": 5,
    "providers": [{
        "providerId": "historical-provider",
        "status": "proven",
        "routes": ["/historical"],
        "routeData": [{"route": "/historical"}],
    }],
}
rows, missing = merge_report.baseline_rows_for_catalogue(
    baseline,
    ["historical-provider", "newly-active-provider"],
)
assert missing == ["newly-active-provider"], missing
assert set(rows) == {"historical-provider", "newly-active-provider"}, rows

placeholder = rows["newly-active-provider"]
assert placeholder["mergePolicy"] == merge_report.CATALOGUE_PRESENCE_ONLY_POLICY
assert placeholder["preserveExistingRuntimePlan"] is True
assert placeholder["proofAuthority"] is False
assert placeholder["executionAuthority"] is False
assert placeholder["routes"] == []
assert placeholder["routeData"] == []
assert placeholder["executionRoutes"] == []
assert apply_report.is_catalogue_presence_only(placeholder)

report = {"providers": [rows["historical-provider"], placeholder]}
applicable = apply_report.provider_rows_for_apply(report)
assert [row["providerId"] for row in applicable] == ["historical-provider"], applicable

# A fresh targeted row replaces the placeholder and becomes applicable. This
# verifies that the preservation state is temporary evidence debt, not a skip.
fresh = {
    "providerId": "newly-active-provider",
    "status": "proven",
    "routes": ["/fresh"],
    "routeData": [{"route": "/fresh"}],
}
assert not apply_report.is_catalogue_presence_only(fresh)
assert [row["providerId"] for row in apply_report.provider_rows_for_apply({"providers": [fresh]})] == [
    "newly-active-provider"
]

# Presence-only rows must fail the marker if any executable authority sneaks in.
tainted = dict(placeholder)
tainted["routes"] = ["/invented"]
assert not apply_report.is_catalogue_presence_only(tainted)

print(
    "provider repair catalogue-presence merge passed: "
    "stale baseline gaps preserve current DATA with zero invented route authority"
)
