#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "batch_quarantine",
    ROOT / "scripts/run_provider_repair_batch_quarantine_v1.py",
)
assert spec and spec.loader
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

strict = {
    "lostUpstreamPositivePairs": [["Alpha", "anime"], ["beta", "tv"]],
    "upstreamPositiveAccounting": {
        "activeLostPairs": [["Alpha", "anime"]],
        "repairDebtPairs": [["beta", "tv"]],
    },
}
assert q.lost_pairs(strict) == [("alpha", "anime")]

fallback = {"lostUpstreamPositivePairs": [["Alpha", "anime"], ["beta", "tv"]]}
assert q.lost_pairs(fallback) == [("alpha", "anime"), ("beta", "tv")]

parity = {
    "providers": [
        {
            "providerId": "Alpha",
            "status": "REGRESSION",
            "lanes": [
                {"lane": "anime", "status": "REGRESSION"},
                {"lane": "tv", "status": "POSITIVE"},
            ],
        },
        {
            "providerId": "Beta",
            "status": "RESAMPLE",
            "lanes": [{"lane": "movie", "status": "RESAMPLE"}],
        },
        {
            "providerId": "Gamma",
            "status": "ZERO",
            "lanes": [{"lane": "movie", "status": "TECHNICAL_UNRESOLVED"}],
        },
    ]
}
assert q.parity_regression_pairs(parity) == [("alpha", "anime")]

quarantined: dict[str, set[str]] = {}
lost, survivors = q.quarantine(
    pairs=[("alpha", "anime"), ("alpha", "tv")],
    remaining=["alpha", "beta", "gamma"],
    quarantined=quarantined,
)
assert lost == ["alpha"]
assert survivors == ["beta", "gamma"]
assert quarantined == {"alpha": {"anime", "tv"}}

# RESAMPLE/technical evidence is never silently converted into a provider drop.
lost, survivors = q.quarantine(
    pairs=[],
    remaining=["beta", "gamma"],
    quarantined=quarantined,
)
assert lost == []
assert survivors == ["beta", "gamma"]

print("PROVIDER_REPAIR_BATCH_QUARANTINE_TEST_OK strict_loss_only=true parity_regression_only=true reset_required=true")
