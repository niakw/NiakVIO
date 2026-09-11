#!/usr/bin/env python3
"""Activation-preservation guard for route-proof diagnostics.

Route proof is diagnostic evidence only. It may classify a provider's route/DATA state
as unresolved or off, but it may not justify removing or disabling a canonical provider
from the published catalogue. Runtime behavior can still fail closed when no reliable
route exists.

The public function name is retained because release-integrity validation imports it.
Legacy proof-v5 disable records are now explicitly rejected rather than granted a
special disablement exception.
"""
from __future__ import annotations

from typing import Any, Callable

import activation_preservation_core_rehash as core_rehash
import validate_activation_preservation as legacy

ROUTE_PROOF_DIAGNOSTIC_ACTION = "route-proof-no-proven-route-diagnostic"
LEGACY_ROUTE_PROOF_DISABLE_ACTION = "published-disabled-no-proven-route"
ROUTE_PROOF_DISABLE_ACTION = LEGACY_ROUTE_PROOF_DISABLE_ACTION
ROUTE_PROOF_FAILED_GATE = "route_proof_no_proven_route"
ROUTE_PROOF_AUTHORITY = "provider-route-recovery-v5"


def conclusive_disablement_with_route_proof(
    original: Callable[..., tuple[bool, str]],
    record: dict[str, Any] | None,
    *,
    missing: bool,
) -> tuple[bool, str]:
    if not isinstance(record, dict):
        return original(record, missing=missing)
    action = str(record.get("action") or "")
    if action == ROUTE_PROOF_DIAGNOSTIC_ACTION:
        return False, "route_proof_diagnostic_may_not_disable_provider"
    if action == LEGACY_ROUTE_PROOF_DISABLE_ACTION:
        return False, "legacy_route_proof_disablement_forbidden_force_all_enabled"
    return original(record, missing=missing)


def validate() -> list[str]:
    original = legacy.conclusive_disablement

    def wrapped(record: dict[str, Any] | None, *, missing: bool) -> tuple[bool, str]:
        return conclusive_disablement_with_route_proof(original, record, missing=missing)

    legacy.conclusive_disablement = wrapped
    try:
        return core_rehash.validate()
    finally:
        legacy.conclusive_disablement = original


if __name__ == "__main__":
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    print("provider activation preservation passed (route proof diagnostic-only)")
