#!/usr/bin/env python3
"""Single canonical distinction between provisional and durable Brain repairs.

Historical Deep reports without the new field remain readable, but every
newly produced event carries the explicit strict-identity outcome. No URL,
HTTP status or Quick improvement alone establishes a repaired provider.
"""
from __future__ import annotations
from typing import Any


def durable_accepted_event(event: dict[str, Any]) -> bool:
    if not isinstance(event, dict):
        return False
    reason = str(event.get("reason") or "").strip().casefold()
    if reason.startswith("provisional_quick_"):
        return False
    status = event.get("durable_promotion_eligible")
    if status is False:
        return False
    if status is True:
        try:
            playable = int(event.get("streams_playable_after") or 0)
        except (TypeError, ValueError):
            return False
        return (playable > 0 and
                event.get("identity_strict_reason") == "positive_content_identity_proof")
    # Legacy Deep reports were persisted before strict fields existed. Keep
    # historical evidence readable; they are NOT current-byte validation.
    return True


def provisional_accepted_event(event: dict[str, Any]) -> bool:
    return isinstance(event, dict) and not durable_accepted_event(event)
