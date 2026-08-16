#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Content-safety gates for automatic runtime repair.

Two different decisions deliberately use two different gates:

* routine quick repair is *repair first, classify later*: a generated candidate
  may survive staging when it has playable media and no positive evidence of
  wrong content or duration mismatch. Identity may still be unknown; the full
  catalogue/media audit remains mandatory before publication and may quarantine
  conclusive offenders before rerunning the exact final audit.
* deep repair is allowed to teach/persist a structural profile only when every
  playable sample used to justify replacement is positively tied to the
  requested work.

The gate consumes already-probed media evidence. Quick health classification
first uses a bounded alternate catalogue fixture per category so an absent title
is not mislabeled as structural failure. Adaptive recovery must then resolve and
positively verify media-looking URLs before they reach this policy layer;
filename extensions alone never turn a repair into playable proof.

Keeping these decisions separate prevents the quick loop from repairing a
provider and immediately throwing the candidate away merely because the bounded
probe could not prove identity, without weakening deep learning or final
publication safety.
"""
from __future__ import annotations

from typing import Any


def _tests(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in result.get("tests") or [] if isinstance(row, dict)]


def automatic_repair_safety_gate(result: dict[str, Any]) -> tuple[bool, str]:
    """Accept a provisional quick repair only when it is playable and not wrong.

    Unknown identity is intentionally allowed here. A contradiction is not.
    The caller must still run the publication catalogue/media audit before the
    candidate can become authoritative.
    """
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    playable = int(evidence.get("streams_playable") or 0)
    contradictions = int(evidence.get("identity_contradiction_count") or 0)
    duration_mismatches = int(evidence.get("duration_identity_mismatch_count") or 0)

    if playable <= 0:
        return False, "safety_gate:no_playable_proof"
    if contradictions > 0:
        return False, "safety_gate:content_identity_contradiction"
    if duration_mismatches > 0:
        return False, "safety_gate:duration_identity_mismatch"

    playable_tests = [row for row in _tests(result) if int(row.get("streams_playable") or 0) > 0]
    if not playable_tests:
        return False, "safety_gate:no_fixture_level_playable_proof"

    for row in playable_tests:
        row_contradictions = int(row.get("identity_contradiction_count") or 0)
        row_duration = int(row.get("duration_identity_mismatch_count") or 0)
        fixture = (row.get("fixture") or {}).get("label") or (row.get("fixture") or {}).get("tmdbId") or "fixture"
        if row_contradictions > 0:
            return False, f"safety_gate:{fixture}:content_identity_contradiction"
        if row_duration > 0:
            return False, f"safety_gate:{fixture}:duration_identity_mismatch"

    return True, "playable_without_identity_contradiction"


def automatic_repair_identity_gate(result: dict[str, Any]) -> tuple[bool, str]:
    """Strict deep-learning gate: playable media must have positive identity."""
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    playable = int(evidence.get("streams_playable") or 0)
    contradictions = int(evidence.get("identity_contradiction_count") or 0)
    duration_mismatches = int(evidence.get("duration_identity_mismatch_count") or 0)
    verified = int(evidence.get("identity_verified_streams") or 0)
    unknown = int(evidence.get("identity_unverified_streams") or 0)

    if playable <= 0:
        return False, "identity_gate:no_playable_proof"
    if contradictions > 0:
        return False, "identity_gate:content_identity_contradiction"
    if duration_mismatches > 0:
        return False, "identity_gate:duration_identity_mismatch"
    if verified <= 0:
        return False, "identity_gate:no_positive_content_identity_proof"

    playable_tests = [row for row in _tests(result) if int(row.get("streams_playable") or 0) > 0]
    if not playable_tests:
        return False, "identity_gate:no_fixture_level_playable_identity_proof"

    for row in playable_tests:
        count = int(row.get("streams_playable") or 0)
        row_verified = int(row.get("identity_verified_streams") or 0)
        row_unknown = int(row.get("identity_unverified_streams") or 0)
        row_contradictions = int(row.get("identity_contradiction_count") or 0)
        row_duration = int(row.get("duration_identity_mismatch_count") or 0)
        fixture = (row.get("fixture") or {}).get("label") or (row.get("fixture") or {}).get("tmdbId") or "fixture"

        if row_contradictions > 0:
            return False, f"identity_gate:{fixture}:content_identity_contradiction"
        if row_duration > 0:
            return False, f"identity_gate:{fixture}:duration_identity_mismatch"
        if row_verified < count or row_unknown > 0:
            return False, f"identity_gate:{fixture}:playable_identity_not_fully_verified"

    if unknown > 0 and verified < playable:
        return False, "identity_gate:aggregate_playable_identity_unresolved"

    return True, "positive_content_identity_proof"
