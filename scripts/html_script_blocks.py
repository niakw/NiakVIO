#!/usr/bin/env python3
"""Bounded HTML script-element extraction without regex tag filtering."""
from __future__ import annotations

_OPEN = "<script"
_CLOSE = "</script"
_BOUNDARY = frozenset(" \t\r\n\f/>")


def _tag_end(source: str, start: int) -> int:
    quote = ""
    for index in range(start, len(source)):
        ch = source[index]
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in {'"', "'"}:
            quote = ch
        elif ch == ">":
            return index
    return -1


def _find_tag(source: str, lowered: str, needle: str, start: int) -> int:
    cursor = max(0, start)
    while True:
        pos = lowered.find(needle, cursor)
        if pos < 0:
            return -1
        after = pos + len(needle)
        if after >= len(source) or source[after] in _BOUNDARY:
            return pos
        cursor = pos + 1


def extract_script_elements(source: str, *, limit: int = 256) -> list[tuple[str, str]]:
    """Return bounded attribute/body pairs; malformed trailing close attributes are tolerated."""
    if not isinstance(source, str):
        return []
    maximum = max(1, min(int(limit), 1024))
    lowered = source.casefold()
    rows: list[tuple[str, str]] = []
    cursor = 0
    while len(rows) < maximum:
        opened = _find_tag(source, lowered, _OPEN, cursor)
        if opened < 0:
            break
        open_end = _tag_end(source, opened + len(_OPEN))
        if open_end < 0:
            break
        closed = _find_tag(source, lowered, _CLOSE, open_end + 1)
        if closed < 0:
            break
        close_end = _tag_end(source, closed + len(_CLOSE))
        if close_end < 0:
            break
        rows.append((source[opened + len(_OPEN):open_end], source[open_end + 1:closed]))
        cursor = close_end + 1
    return rows


def extract_script_blocks(source: str, *, limit: int = 256) -> list[str]:
    return [body for _attrs, body in extract_script_elements(source, limit=limit)]
