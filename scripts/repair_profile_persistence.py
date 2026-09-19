#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Normalize accepted repair metadata before durable profile persistence."""
from __future__ import annotations

from typing import Any


def ensure_repair_profile(
    repaired: dict[str, Any] | None,
    requested_profile: str | None,
) -> dict[str, Any] | None:
    """Fill a missing runtime repair profile from its stable strategy name.

    Older adaptive candidates deliberately left ``runtime_repair.profile``
    empty while storing ``strategy=adaptive_runtime_recovery``. The deep loop
    persists only named profiles, so without this normalization the same
    structural recovery can be rediscovered on every future deep run.
    """
    if not isinstance(repaired, dict):
        return repaired
    event = repaired.get("runtime_repair")
    if not isinstance(event, dict):
        return repaired
    if str(event.get("profile") or "").strip():
        return repaired
    inferred = str(event.get("strategy") or requested_profile or "").strip()
    if inferred:
        event["profile"] = inferred
    return repaired
