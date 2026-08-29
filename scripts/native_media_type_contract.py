#!/usr/bin/env python3
"""Canonical media-type boundary for native NiakVIO/Nuvio evidence.

Client aliases describe how Nuvio surfaced an item; they do not own the final
content identity.

Rules:
- series/show/other are TV-series aliases by default;
- movie -> movie, tv -> tv, anime -> anime;
- an explicit trusted anime category wins over a series/tv-shaped client alias,
  so episodic anime is always resolved and sent to providers as anime.
"""
from __future__ import annotations

from typing import Any

CANONICAL_MEDIA_TYPES = frozenset({"movie", "tv", "anime"})
TV_ALIASES = frozenset({"series", "show", "other"})


def canonical_media_type(value: Any, *, category: Any = None) -> str:
    raw = str(value or "movie").strip().casefold()
    category_raw = str(category or "").strip().casefold()

    # Content identity beats client presentation. Nuvio may expose an anime as a
    # generic series, but NiakVIO must preserve the anime resolution.
    if category_raw == "anime":
        return "anime"

    if raw in TV_ALIASES:
        raw = "tv"
    if raw not in CANONICAL_MEDIA_TYPES:
        raise ValueError(
            f"unsupported media type {raw!r}; expected movie|tv|anime "
            "or a TV-series input alias series|show|other"
        )
    return raw


def fixture_media_type(fixture: dict[str, Any]) -> str:
    return canonical_media_type(
        fixture.get("mediaType") or fixture.get("type") or fixture.get("category") or "movie",
        category=fixture.get("category"),
    )
