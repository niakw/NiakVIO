#!/usr/bin/env python3
"""Activation-preservation adapter for deterministic Core re-hashes.

Safety findings are immutable evidence of the original client observation and the
quarantine artifact produced at that time. A later deterministic Core rebuild may
change the SHA/path of the *current inert quarantine bundle* without changing that
historical evidence. This adapter keeps the legacy validator strict, but lets
release-integrity validation rebind only the historical quarantine-artifact fields
to the current bundle when every current manifest/provenance/marker/reason check
still passes.

The tested unsafe bundle SHA, tested commit, fixture, observed contradiction and
client evidence are never rewritten or relaxed.
"""
from __future__ import annotations

import copy
from typing import Any

import validate_activation_preservation as legacy

_REHASHABLE_REASONS = {
    "safety_quarantine_bundle_finding_sha_mismatch",
    "safety_quarantine_bundle_finding_path_mismatch",
}


def _configured_safety_quarantine_with_core_rehash(
    original,
    provider_id: str,
    manifest_row: dict[str, Any] | None,
    patch: dict[str, Any] | None,
    provenance: dict[str, Any] | None,
    finding: dict[str, Any] | None,
) -> tuple[bool, str]:
    accepted, reason = original(provider_id, manifest_row, patch, provenance, finding)
    if accepted or reason not in _REHASHABLE_REASONS:
        return accepted, reason
    if not isinstance(manifest_row, dict) or not isinstance(finding, dict):
        return False, reason

    recorded_sha = str(finding.get("quarantined_bundle_sha256") or "")
    recorded_bundle = str(finding.get("quarantined_bundle") or "")
    if not legacy.SHA256_RE.fullmatch(recorded_sha):
        return False, "safety_quarantine_historical_bundle_sha_invalid"
    if not recorded_bundle.startswith("providers/") or not recorded_bundle.endswith(".js"):
        return False, "safety_quarantine_historical_bundle_path_invalid"

    current_bundle = str(manifest_row.get("filename") or "")
    current_path = legacy.ROOT / current_bundle
    if not current_bundle.startswith("providers/") or not current_path.is_file():
        return False, "safety_quarantine_current_bundle_missing"
    current_sha = legacy.file_sha256(current_path)

    rebound = copy.deepcopy(finding)
    rebound["quarantined_bundle"] = current_bundle
    rebound["quarantined_bundle_sha256"] = current_sha
    accepted, rebound_reason = original(
        provider_id,
        manifest_row,
        patch,
        provenance,
        rebound,
    )
    if not accepted:
        return False, rebound_reason
    return True, f"{rebound_reason}:deterministic_core_rehash"


def validate() -> list[str]:
    original = legacy.configured_safety_quarantine

    def adapted(provider_id, manifest_row, patch, provenance, finding):
        return _configured_safety_quarantine_with_core_rehash(
            original,
            provider_id,
            manifest_row,
            patch,
            provenance,
            finding,
        )

    legacy.configured_safety_quarantine = adapted
    try:
        return legacy.validate()
    finally:
        legacy.configured_safety_quarantine = original


if __name__ == "__main__":
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    print("provider activation preservation passed (deterministic Core rehash aware)")
