#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "merge_targeted_census_transport",
    ROOT / "scripts" / "merge_targeted_census_transport.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

status = {
    "runId": "census-1",
    "repairQueue": ["blocked", "healthy-repair", "verified"],
    "providers": [
        {
            "provider": "blocked",
            "status": "ROUTE PROVEN",
            "statusRepairEligible": True,
            "authorityRepairEligible": True,
            "repairEligible": True,
        },
        {
            "provider": "healthy-repair",
            "status": "CHAIN REACHED",
            "statusRepairEligible": True,
            "authorityRepairEligible": True,
            "repairEligible": True,
        },
        {
            "provider": "verified",
            "status": "ROUTE PROVEN",
            "statusRepairEligible": True,
            "authorityRepairEligible": True,
            "repairEligible": True,
        },
    ],
}
targeted = {
    "sourceCensusRunId": "census-1",
    "sourceVerdictRunId": "targeted-1",
    "providers": {
        "blocked": {
            "debugStages": {"movie": "provider_waf_challenge"},
            "network": {
                "movie": [
                    {"host": "api.themoviedb.org", "status": 200},
                    {"host": "provider.example", "status": 403},
                ]
            },
            "playableLanes": [],
            "verifiedLanes": [],
        },
        "healthy-repair": {
            "debugStages": {"movie": "provider_network_zero_result"},
            "network": {
                "movie": [
                    {"host": "provider.example", "status": 200},
                ]
            },
            "playableLanes": [],
            "verifiedLanes": [],
        },
        "verified": {
            "debugStages": {"movie": "provider_waf_challenge"},
            "network": {
                "movie": [
                    {"host": "provider.example", "status": 403},
                ]
            },
            "playableLanes": ["movie"],
            "verifiedLanes": ["movie"],
        },
    },
}

merged = mod.merge(status, targeted)
assert merged["repairQueue"] == ["healthy-repair", "verified"], merged["repairQueue"]
assert merged["targetedTransportBlockedQueue"] == ["blocked"]
blocked = next(row for row in merged["providers"] if row["provider"] == "blocked")
assert blocked["repairEligible"] is False
assert blocked["status"] == "ROUTE PROVEN"
assert blocked["targetedTransportClass"] == "provider-waf-challenge-current"
healthy = next(row for row in merged["providers"] if row["provider"] == "healthy-repair")
assert healthy["repairEligible"] is True
verified = next(row for row in merged["providers"] if row["provider"] == "verified")
assert verified["repairEligible"] is True

try:
    mod.merge(
        {"runId": "new", "providers": [], "repairQueue": []},
        {"sourceCensusRunId": "old", "providers": {}},
    )
except ValueError as exc:
    assert "not current for census" in str(exc)
else:
    raise AssertionError("stale targeted evidence must fail closed")
