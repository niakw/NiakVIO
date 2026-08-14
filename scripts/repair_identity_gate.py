#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Strict content-identity gate for automatic runtime repair promotion.

Existing published provider output may remain identity-unknown when there is no
contradiction. A newly generated automatic repair is stricter: every playable
sample used to justify replacing its parent must be positively tied to the
requested work, with no content contradiction or duration mismatch.
"""
from __future__ import annotations

from typing import Any


def _tests(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in result.get("tests") or [] if isinstance(row, dict)]


def automatic_repair_identity_gate(result: dict[str, Any]) -> tuple[bool, str]:
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

    playable_tests = [
        row for row in _tests(result)
        if int(row.get("streams_playable") or 0) > 0
    ]

    # Fail closed when the aggregate claims playability but the harness did not
    # retain fixture-level playable evidence. Aggregate identity counters can
    # include non-playable rows and are not sufficient to promote new bytes.
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
