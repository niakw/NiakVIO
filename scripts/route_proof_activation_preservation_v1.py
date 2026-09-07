#!/usr/bin/env python3
"""Activation-preservation bridge for explicit proof-v5 route neutralization.

The legacy activation guard correctly rejects ordinary network/no-stream failures as
inconclusive. A proof-v5 route census is different evidence: when an explicit
activation policy records that a provider has zero executable/proven routes, the
provider may remain present but disabled without pretending that a network outage or
quality gate conclusively failed.

This adapter is intentionally narrow. It accepts only the dedicated action emitted by
``enforce_route_proof_manifest_policy_v1.py`` and cross-checks it against the current
provider-route-recovery-v5 report. All other activation decisions are delegated to the
existing deterministic Core-rehash-aware validator unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import activation_preservation_core_rehash as core_rehash
import validate_activation_preservation as legacy

ROOT = Path(__file__).resolve().parents[1]
ROUTE_REPORT = ROOT / "automation" / "provider-route-recovery-v5.json"
ROUTE_PROOF_DISABLE_ACTION = "published-disabled-no-proven-route"
ROUTE_PROOF_FAILED_GATE = "route_proof_no_proven_route"
ROUTE_PROOF_AUTHORITY = "provider-route-recovery-v5"


def _cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _strict_int(value: object) -> int | None:
    """Parse an explicit integer without treating numeric zero as missing."""
    if value is None or isinstance(value, bool):
        return None
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(text)
    except (TypeError, ValueError):
        return None


def _load_route_report() -> dict[str, Any] | None:
    if not ROUTE_REPORT.is_file():
        return None
    try:
        value = json.loads(ROUTE_REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _proof_row(provider_id: str) -> dict[str, Any] | None:
    report = _load_route_report()
    if not isinstance(report, dict) or _strict_int(report.get("schemaVersion")) != 5:
        return None
    for row in report.get("providers") or []:
        if isinstance(row, dict) and _cid(row.get("providerId")) == provider_id:
            return row
    return None


def conclusive_disablement_with_route_proof(
    original: Callable[..., tuple[bool, str]],
    record: dict[str, Any] | None,
    *,
    missing: bool,
) -> tuple[bool, str]:
    if not isinstance(record, dict) or str(record.get("action") or "") != ROUTE_PROOF_DISABLE_ACTION:
        return original(record, missing=missing)
    if missing:
        return False, "route_proof_neutralization_may_not_remove_provider"
    if record.get("enabled") is not False:
        return False, "route_proof_disable_record_still_enabled"

    failed = {str(value) for value in record.get("failed_gates") or [] if str(value)}
    if ROUTE_PROOF_FAILED_GATE not in failed:
        return False, "route_proof_disable_missing_failed_gate"

    evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
    provider_id = _cid(record.get("id") or evidence.get("provider_id"))
    if not provider_id:
        return False, "route_proof_disable_missing_provider_id"
    if _strict_int(evidence.get("route_proof_version")) != 5:
        return False, "route_proof_disable_wrong_proof_version"
    evidence_routes = _strict_int(evidence.get("proven_route_count"))
    if evidence_routes is None:
        return False, "route_proof_disable_invalid_evidence_routes"
    if evidence_routes != 0:
        return False, "route_proof_disable_nonzero_evidence_routes"
    if str(evidence.get("authority") or "") != ROUTE_PROOF_AUTHORITY:
        return False, "route_proof_disable_wrong_authority"
    if str(evidence.get("status") or "").casefold() != "no-proven-route":
        return False, "route_proof_disable_wrong_status"

    proof = _proof_row(provider_id)
    if not isinstance(proof, dict):
        return False, "route_proof_disable_current_report_missing_provider"
    routes = [str(value) for value in proof.get("routes") or [] if str(value).strip()]
    if str(proof.get("status") or "").casefold() != "no-proven-route" or routes:
        return False, "route_proof_disable_current_report_not_zero_route"
    return True, ROUTE_PROOF_DISABLE_ACTION


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
    print("provider activation preservation passed (proof-v5 route neutralization aware)")
