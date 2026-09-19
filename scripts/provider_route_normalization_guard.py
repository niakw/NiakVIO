#!/usr/bin/env python3
"""Guards for NiakVIO Provider v3 route normalization.

The legacy normalizer trims JavaScript punctuation from raw candidates. A semantic
placeholder at the end of a route (for example ``{query}``) must not be mistaken
for trailing JavaScript punctuation. This wrapper masks placeholders while the
legacy normalizer does its ordinary URL/path cleanup, then restores them.

It also rejects HTML data attributes that resemble paths (for example
``/data-video=``). Those are extraction hints, not HTTP routes.
"""
from __future__ import annotations

import re
from typing import Any

PLACEHOLDER_RE = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
HTML_ATTRIBUTE_ROUTE_RE = re.compile(r"^/data-[A-Za-z0-9_-]+=$", re.I)


def _mask_placeholders(value: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        token = f"__NIAKVIO_PH_{len(mapping)}__"
        mapping[token] = match.group(0)
        return token

    return PLACEHOLDER_RE.sub(repl, value), mapping


def _restore_placeholders(value: str, mapping: dict[str, str]) -> str:
    for token, placeholder in mapping.items():
        value = value.replace(token, placeholder)
    return value


def install(recognizer: Any) -> None:
    if getattr(recognizer, "_NIAKVIO_ROUTE_NORMALIZATION_GUARD_INSTALLED", False):
        return

    old_normalize = recognizer.normalize_dynamic
    old_junk = recognizer.route_is_junk

    def normalize_dynamic(value: str) -> str | None:
        raw = str(value or "")
        masked, mapping = _mask_placeholders(raw)
        route = old_normalize(masked)
        if not route:
            return None
        route = _restore_placeholders(route, mapping)
        if HTML_ATTRIBUTE_ROUTE_RE.fullmatch(route.strip()):
            return None
        return route

    def route_is_junk(route: str) -> bool:
        value = str(route or "").strip()
        if HTML_ATTRIBUTE_ROUTE_RE.fullmatch(value):
            return True
        return old_junk(value)

    recognizer.normalize_dynamic = normalize_dynamic
    recognizer.route_is_junk = route_is_junk
    recognizer._NIAKVIO_ROUTE_NORMALIZATION_GUARD_INSTALLED = True
