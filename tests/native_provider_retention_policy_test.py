#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_native_reader_brain_repair.py"

spec = importlib.util.spec_from_file_location("native_reader_brain_repair", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def diagnosis(*, healthy: list[str], failing: list[str], failure_class: str = "playback_http_access") -> dict:
    plans = [
        {
            "provider": "example",
            "client": client,
            "fixture": "fixture",
            "requestType": "movie",
            "routeMode": "declared",
            "failureClass": failure_class,
            "action": "probe-targeted-repair",
            "hypotheses": [{"id": "replay-native-request-context"}],
        }
        for client in failing
    ]
    observations = [
        {
            "provider": "example",
            "client": client,
            "fixture": "fixture",
            "requestType": "movie",
            "routeMode": "declared",
            "failureClass": "healthy",
            "state": "ready",
        }
        for client in healthy
    ]
    return {"plans": plans, "observations": observations}


def main() -> int:
    assert module.PRIMARY_NATIVE_CLIENT == "tv"

    # TV success is the strongest retention proof. Desktop/Mobile failures are
    # compatibility evidence only and can never disable or mutate the provider.
    eligible, compatibility = module.diagnosis_targets(
        diagnosis(healthy=["tv"], failing=["desktop", "mobile"]),
        12,
        "fixture",
    )
    assert eligible == []
    assert len(compatibility) == 1
    row = compatibility[0]
    assert row["providerDisposition"] == "retained_tv_healthy"
    assert row["tvHealthy"] is True
    assert row["providerMutationAllowed"] is False
    assert row["globalDisableAllowed"] is False

    # TV may be the principal client, but a genuine success on another real client
    # still proves the provider itself is not globally dead.
    eligible, compatibility = module.diagnosis_targets(
        diagnosis(healthy=["desktop"], failing=["tv", "mobile"]),
        12,
        "fixture",
    )
    assert eligible == []
    assert len(compatibility) == 1
    row = compatibility[0]
    assert row["providerDisposition"] == "retained_healthy_peer"
    assert row["tvHealthy"] is False
    assert row["providerMutationAllowed"] is False
    assert row["globalDisableAllowed"] is False

    # A lone TV failure is never enough to condemn or mutate a provider globally.
    eligible, compatibility = module.diagnosis_targets(
        diagnosis(healthy=[], failing=["tv"]),
        12,
        "fixture",
    )
    assert eligible == []
    assert len(compatibility) == 1
    row = compatibility[0]
    assert row["providerDisposition"] == "compatibility_issue_only"
    assert row["reason"] == "insufficient_cross_client_confirmation"
    assert row["globalDisableAllowed"] is False

    # Even genuine cross-client consensus is only a bounded repair-candidate signal;
    # this Lab never authorizes provider deactivation.
    eligible, compatibility = module.diagnosis_targets(
        diagnosis(healthy=[], failing=["tv", "mobile"]),
        12,
        "fixture",
    )
    assert compatibility == []
    assert len(eligible) == 1
    row = eligible[0]
    assert row["providerDisposition"] == "cross_client_repair_candidate"
    assert row["providerMutationAllowed"] is True
    assert row["globalDisableAllowed"] is False

    print("native provider retention policy tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
