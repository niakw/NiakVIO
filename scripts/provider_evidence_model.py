#!/usr/bin/env python3
"""Provider-agnostic evidence model for stream rows and media fixtures."""
from __future__ import annotations

from typing import Any, Iterable

ROW_VERIFIED = "verified"
ROW_UNKNOWN = "unknown"
ROW_REJECTED = "rejected"
FIXTURE_VERIFIED = "verified"
FIXTURE_UNVERIFIED = "unverified"
FIXTURE_EMPTY = "empty"
FIXTURE_UNSAFE = "unsafe"


def classify_probe(probe: dict[str, Any]) -> str:
    playable = bool(probe.get("playable"))
    identity = probe.get("identity") if isinstance(probe.get("identity"), dict) else {}
    identity_status = str(identity.get("status") or "unknown").casefold()
    duration_mismatch = bool(probe.get("duration_identity_mismatch"))
    if identity_status == "contradiction" or duration_mismatch or not playable:
        return ROW_REJECTED
    if identity_status == "match":
        return ROW_VERIFIED
    return ROW_UNKNOWN


def summarize_fixture(probes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(probes)
    classes = [classify_probe(row) for row in rows]
    verified = classes.count(ROW_VERIFIED)
    unknown = classes.count(ROW_UNKNOWN)
    rejected = classes.count(ROW_REJECTED)
    playable_contradictions = sum(
        1 for row in rows
        if bool(row.get("playable"))
        and (
            str(((row.get("identity") or {}).get("status") or "")).casefold() == "contradiction"
            or bool(row.get("duration_identity_mismatch"))
        )
    )
    if playable_contradictions:
        state = FIXTURE_UNSAFE
    elif verified:
        state = FIXTURE_VERIFIED
    elif unknown:
        state = FIXTURE_UNVERIFIED
    else:
        state = FIXTURE_EMPTY
    return {
        "state": state,
        "verified_rows": verified,
        "unknown_rows": unknown,
        "rejected_rows": rejected,
        "playable_contradictions": playable_contradictions,
        "row_count": len(rows),
    }


def provider_fixture_is_safe(summary: dict[str, Any]) -> bool:
    return int(summary.get("playable_contradictions") or 0) == 0
