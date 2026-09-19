#!/usr/bin/env python3
"""Boundary-aware literal replacement helpers for provider overrides.

Domain migrations must be idempotent.  A historical host such as
``flemmix.me`` is a prefix of the valid target ``flemmix.men``; plain
``str.replace`` would therefore mutate an already-patched bundle to
``flemmix.menn``.  These helpers use token boundaries for host/URL-like
values while preserving ordinary literal replacement for code snippets.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

_HOST_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z0-9-]+(?::\d+)?$", re.I)
_TOKEN_CHARS = r"A-Za-z0-9._-"


def _hostish(value: str) -> bool:
    value = str(value or "").strip()
    if not value or any(ch.isspace() for ch in value):
        return False
    if "://" in value:
        parsed = urlparse(value)
        return bool(parsed.scheme and parsed.hostname)
    return bool(_HOST_RE.fullmatch(value.rstrip("/")))


def _pattern(value: str) -> re.Pattern[str] | None:
    value = str(value)
    if not _hostish(value):
        return None
    # Do not match inside a longer hostname/token.  Slashes, quotes, colons,
    # query separators and whitespace remain valid boundaries.
    return re.compile(rf"(?<![{_TOKEN_CHARS}]){re.escape(value)}(?![{_TOKEN_CHARS}])", re.I)


def contains_literal(text: str, value: str) -> bool:
    value = str(value)
    pattern = _pattern(value)
    return bool(pattern.search(text)) if pattern else value in text


def replace_literal(text: str, old: str, new: str) -> tuple[str, int]:
    old, new = str(old), str(new)
    pattern = _pattern(old)
    if pattern:
        return pattern.subn(lambda _match: new, text)
    count = text.count(old)
    return (text.replace(old, new), count) if count else (text, 0)
