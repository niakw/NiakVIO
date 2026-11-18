#!/usr/bin/env python3
"""Canonical Provider-v3 executable generation hash."""
from __future__ import annotations

import hashlib
from typing import Any, Iterable


def canonical_provider_id(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def materialization_generation(rows: Iterable[dict[str, Any]]) -> str:
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("materialization generation row must be an object")
        provider_id = canonical_provider_id(row.get("provider"))
        digest = str(row.get("sha256") or "").strip().casefold()
        if not provider_id or provider_id in seen:
            raise ValueError(
                f"{provider_id or '<empty>'}: invalid/duplicate materialization provider"
            )
        if len(digest) != 64:
            raise ValueError(
                f"{provider_id}: invalid materialization digest during generation"
            )
        try:
            bytes.fromhex(digest)
        except ValueError as exc:
            raise ValueError(
                f"{provider_id}: invalid materialization digest during generation"
            ) from exc
        seen.add(provider_id)
        normalized.append((provider_id, digest))
    if not normalized:
        raise ValueError("materialization generation requires at least one provider")

    aggregate = hashlib.sha256()
    for provider_id, digest in sorted(normalized):
        aggregate.update(provider_id.encode("utf-8"))
        aggregate.update(bytes.fromhex(digest))
    return aggregate.hexdigest()
