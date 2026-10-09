#!/usr/bin/env python3
"""Keep new provider failures in bounded Brain-negative memory.

A global failures-descending 1000-row cap can discard the first genuine
negative evidence for a previously underrepresented provider, making the
next run repeat the same experiment. Retain at least a few unique signatures
per observed provider before using remaining room for higher-ranked rows.
"""
from __future__ import annotations

from typing import Any


def select_bounded_negative_memory(
    records: list[dict[str, Any]],
    *,
    limit: int = 1000,
    minimum_per_provider: int = 12,
) -> list[dict[str, Any]]:
    cap = max(1, min(10000, int(limit)))
    floor = max(1, min(32, int(minimum_per_provider)))
    ranked = sorted(
        [item for item in records if isinstance(item, dict)],
        key=lambda row: (
            -int(row.get("consecutiveFailures") or 0),
            -int(row.get("failures") or 0),
            str(row.get("providerId") or ""),
            str(row.get("signature") or ""),
            str(row.get("profile") or ""),
            int(row.get("experimentVariant") or 0),
            max(1, int(row.get("experimentGeneration") or 1)),
        ),
    )
    # Round-robin within each provider so a newly observed family with one
    # failure survives even when existing hot providers dominate counters.
    by_provider: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for idx, row in enumerate(ranked):
        provider = str(row.get("providerId") or "").strip().casefold()
        by_provider.setdefault(provider, []).append((idx, row))
    chosen: set[int] = set()
    ordered = sorted(by_provider)
    for depth in range(floor):
        for provider in ordered:
            records_for_provider = by_provider[provider]
            if depth < len(records_for_provider) and len(chosen) < cap:
                chosen.add(records_for_provider[depth][0])
    for idx, _ in enumerate(ranked):
        if len(chosen) >= cap:
            break
        chosen.add(idx)
    # Re-sort by original global rank to keep stable on-disk output and cache.
    return [row for idx, row in enumerate(ranked) if idx in chosen][:cap]
