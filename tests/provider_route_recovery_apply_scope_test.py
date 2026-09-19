#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_provider_route_recovery_report as apply_report  # noqa: E402
import current_provider_scope as scope  # noqa: E402
import recover_provider_routes_from_upstreams as recovery  # noqa: E402

ids = sorted(scope.active_provider_ids())
assert ids
report = {
    "schemaVersion": recovery.PROOF_VERSION,
    "providerCount": len(ids),
    "catalogueProviderCount": len(ids),
    "providers": [{"providerId": provider_id} for provider_id in ids],
}
rows = apply_report.validate_report_scope(report)
assert len(rows) == len(ids)

bad_count = copy.deepcopy(report)
bad_count["providerCount"] = len(ids) + 1
try:
    apply_report.validate_report_scope(bad_count)
except SystemExit as exc:
    assert "expected_current_active" in str(exc), exc
else:
    raise AssertionError("stale provider count must fail")

bad_identity = copy.deepcopy(report)
bad_identity["providers"][-1]["providerId"] = "historical-provider-not-current"
try:
    apply_report.validate_report_scope(bad_identity)
except SystemExit as exc:
    assert "active identity mismatch" in str(exc), exc
else:
    raise AssertionError("non-current provider identity must fail")

duplicate = copy.deepcopy(report)
duplicate["providers"][-1]["providerId"] = ids[0]
try:
    apply_report.validate_report_scope(duplicate)
except SystemExit as exc:
    assert "duplicate provider ids" in str(exc), exc
else:
    raise AssertionError("duplicate provider identity must fail")

print(
    "provider route recovery apply scope passed: "
    f"current_active={len(ids)} exact_identity=1 magic_count=0"
)
