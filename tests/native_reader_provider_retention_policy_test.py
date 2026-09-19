#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_native_reader_brain_repair.py"

spec = importlib.util.spec_from_file_location("native_reader_brain_repair", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def plan(client: str, failure: str = "playback_http_access") -> dict:
    return {
        "provider": "moviesdrive",
        "client": client,
        "fixture": "sinners-2025",
        "requestType": "movie",
        "routeMode": "declared",
        "index": 0,
        "failureClass": failure,
        "action": "probe-targeted-repair",
        "hypotheses": [{"id": "replay-native-request-context"}],
    }


def healthy(client: str) -> dict:
    return {
        "provider": "moviesdrive",
        "client": client,
        "fixture": "sinners-2025",
        "requestType": "movie",
        "routeMode": "declared",
        "index": 0,
        "failureClass": "healthy",
        "state": "ready",
    }


# TV is the primary client: TV healthy vetoes a global mutation even if both other
# native client families fail the exact same provider/route/failure class.
eligible, compatibility = module.diagnosis_targets({
    "plans": [plan("mobile"), plan("desktop")],
    "observations": [healthy("tv")],
    "extractionHealthyObservations": [],
}, 24)
assert eligible == []
assert len(compatibility) == 1
row = compatibility[0]
assert row["healthyClients"] == ["tv"]
assert row["failingClients"] == ["desktop", "mobile"]
assert row["providerDisposition"] == "retained_tv_healthy"
assert row["tvHealthy"] is True
assert row["providerMutationAllowed"] is False
assert row["globalDisableAllowed"] is False

# TV failure is important, but still cannot condemn a provider when another real
# client proves that the same route works. Keep the issue platform-specific.
eligible, compatibility = module.diagnosis_targets({
    "plans": [plan("tv"), plan("desktop")],
    "observations": [healthy("mobile")],
    "extractionHealthyObservations": [],
}, 24)
assert eligible == []
assert len(compatibility) == 1
row = compatibility[0]
assert row["healthyClients"] == ["mobile"]
assert row["providerDisposition"] == "retained_healthy_peer"
assert row["tvHealthy"] is False
assert row["globalDisableAllowed"] is False

# A single client failure is compatibility evidence only, never a provider-global
# classification and never a disable signal.
eligible, compatibility = module.diagnosis_targets({
    "plans": [plan("tv")],
    "observations": [],
    "extractionHealthyObservations": [],
}, 24)
assert eligible == []
assert len(compatibility) == 1
row = compatibility[0]
assert row["reason"] == "insufficient_cross_client_confirmation"
assert row["providerDisposition"] == "compatibility_issue_only"
assert row["globalDisableAllowed"] is False

# Only same-cause cross-client failure with no healthy peer can enter the repair
# sandbox, and even then the Lab may repair but never automatically disable it.
eligible, compatibility = module.diagnosis_targets({
    "plans": [plan("tv"), plan("mobile")],
    "observations": [],
    "extractionHealthyObservations": [],
}, 24)
assert compatibility == []
assert len(eligible) == 1
row = eligible[0]
assert row["providerDisposition"] == "cross_client_repair_candidate"
assert row["providerMutationAllowed"] is True
assert row["globalDisableAllowed"] is False
assert row["primaryClient"] == "tv"

source = SCRIPT.read_text(encoding="utf-8")
for required in (
    '"anyHealthyClientPreventsGlobalDisable": True',
    '"tvIsPrimaryRetentionSignal": True',
    '"tvHealthyAlwaysRetainsProvider": True',
    '"nativeReaderFailureNeverDirectlyDisablesProvider": True',
    '"crossClientFailureMayRepairButNeverAutoDisable": True',
    '"globalProviderDisableCandidates": 0',
):
    assert required in source, required

print("native reader provider retention policy tests passed")
