#!/usr/bin/env python3
"""Targeted census rows must not supersede fleet-wide census authority."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import merge_targeted_provider_census_status as mod


def row(provider: str, status: str, tested: bool, marker: str) -> dict:
    return {
        "provider": provider,
        "status": status,
        "testedThisRun": tested,
        "marker": marker,
        "repairEligible": status not in {"FULL OK", "HARNESS/ENV BLOCKED"},
    }


base = {
    "schemaVersion": 3,
    "runId": "fleet-100",
    "triggerSha": "a" * 40,
    "providers": [
        row("alpha", "FULL OK", True, "fresh-alpha"),
        row("beta", "FULL OK", True, "fresh-beta"),
        row("target", "HARNESS/ENV BLOCKED", False, "old-target"),
    ],
    "counts": {"FULL OK": 2, "HARNESS/ENV BLOCKED": 1},
    "repairQueue": [],
    "environmentQueue": ["target"],
    "lastRepairAttempt": {"runId": "repair-9"},
}
candidate = {
    "schemaVersion": 3,
    "runId": "target-200",
    "triggerSha": "b" * 40,
    "providers": [
        row("alpha", "FULL OK", False, "stale-carried-alpha"),
        row("beta", "PROOF REFRESH REQUIRED", False, "stale-carried-beta"),
        row("target", "NO PROOF", True, "fresh-target"),
    ],
    "counts": {"FULL OK": 1, "PROOF REFRESH REQUIRED": 1, "NO PROOF": 1},
    "repairQueue": ["target"],
    "environmentQueue": [],
    "lastRepairAttempt": {"runId": "stale-repair"},
}

merged = mod.merge(copy.deepcopy(base), copy.deepcopy(candidate), ["target"])
rows = {r["provider"]: r for r in merged["providers"]}
assert merged["runId"] == "fleet-100", merged
assert merged["triggerSha"] == "a" * 40, merged
assert merged["lastRepairAttempt"] == {"runId": "repair-9"}, merged
assert rows["alpha"]["marker"] == "fresh-alpha" and rows["alpha"]["testedThisRun"] is True, rows
assert rows["beta"]["marker"] == "fresh-beta" and rows["beta"]["status"] == "FULL OK", rows
assert rows["target"]["marker"] == "fresh-target" and rows["target"]["status"] == "NO PROOF", rows
assert rows["target"]["testedThisRun"] is True, rows
assert rows["target"]["targetedCensusRunId"] == "target-200", rows
assert rows["target"]["targetedCensusSha"] == "b" * 40, rows
overlay = merged["targetedCensusOverlay"]
assert overlay["baseRunId"] == "fleet-100" and overlay["runId"] == "target-200", overlay
assert overlay["providers"] == ["target"] and overlay["fleetAuthorityPreserved"] is True, overlay

try:
    mod.merge(copy.deepcopy(base), copy.deepcopy(candidate), ["absent"])
except ValueError as exc:
    assert "provider mismatch" in str(exc), exc
else:
    raise AssertionError("missing targeted provider must fail closed")

print("FIELD_TARGETED_CENSUS_STATE_TEST fleet_rows_preserved=true target_row_replaced=true")
