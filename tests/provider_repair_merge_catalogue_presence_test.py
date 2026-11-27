#!/usr/bin/env python3
"""Stale route history must not block or mutate newly active catalogue providers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_provider_route_recovery_report as apply_report  # noqa: E402
import merge_provider_repair_report_v6 as merge_report  # noqa: E402


# Default repository authority must be the Global+France active projection union,
# not root manifest.json. Inject the projection resolver so this remains an
# isolated unit test without depending on the live catalogue.
projection_ids = merge_report.publication_active_ids(
    merge_report.DEFAULT_MANIFEST,
    {"scrapers": [{"id": "global-only", "enabled": True, "filename": "providers/global.js"}]},
    projection_ids_fn=lambda: ["global-only", "france-only"],
)
assert projection_ids == ["global-only", "france-only"], projection_ids

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

seen: dict[str, object] = {}
def fake_apply(payload):
    seen.update(payload)
    return {"patchedProviders": 1, "provenRoutes": 1, "apiRecipes": 0}

summary = apply_report.apply_recovery_preserving_presence(report, apply_fn=fake_apply)
assert [row["providerId"] for row in seen["providers"]] == ["historical-provider"], seen
assert summary["patchedProviders"] == 1
assert summary["applicableProviders"] == 1
assert summary["preservedUntouchedProviders"] == 1
assert len(report["providers"]) == 2, "filtering must not rewrite the full-scope report"

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

tainted_report = {"providers": [tainted]}
tainted_seen: dict[str, object] = {}
tainted_summary = apply_report.apply_recovery_preserving_presence(
    tainted_report,
    apply_fn=lambda payload: (
        tainted_seen.update(payload)
        or {"patchedProviders": 1, "provenRoutes": 1, "apiRecipes": 0}
    ),
)
assert [row["providerId"] for row in tainted_seen["providers"]] == ["newly-active-provider"]
assert tainted_summary["preservedUntouchedProviders"] == 0

print(
    "provider repair catalogue-presence merge passed: "
    "stale baseline gaps preserve current DATA with zero invented route authority"
)
