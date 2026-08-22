#!/usr/bin/env python3
"""Remove destructive generic unescaping immediately before structured parsing.

This repair is deliberately provider-agnostic. Some upstream bundles try to make an
escaped JSON container parseable with ``value.replace(/\\\\(.)/g, "$1")`` or first
collapse every doubled backslash and then run more escape replacements. Those
operations can silently corrupt valid JSON escapes, Unicode escapes, paths and
media metadata, and the staged form can make a backslash produced by one pass get
interpreted again by the next pass.

The repair never guesses a replacement encoding. It only removes the destructive
pre-transform when the temporary value is fed directly into ``JSON.parse`` shortly
afterward. Narrow Unicode/quote decoding already present upstream is preserved.
Existing strict parse/fallback behavior is otherwise preserved, and the normal
Brain before/after runtime gate decides whether a generated repair may win.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

MARKER = "NUVIO_SAFE_STRUCTURED_PARSE_V1"

_ASSIGN = re.compile(
    r"(?P<prefix>\b(?:const|let|var)\s+(?P<tmp>[A-Za-z_$][\w$]*)\s*=\s*)"
    r"(?P<source>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)"
    r"\.replace\(/\\\\\(\.\)/g,\s*(?P<q>[\"'])\$1(?P=q)\)"
    r"(?P<suffix>\s*;)"
)

_INLINE = re.compile(
    r"JSON\.parse\(\s*(?P<source>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)"
    r"\.replace\(/\\\\\(\.\)/g,\s*(?P<q>[\"'])\$1(?P=q)\)\s*\)"
)

# A second upstream pattern first turns every escaped backslash pair into a
# single backslash, then performs Unicode/quote substitutions and JSON.parse.
# Removing only that first collapse prevents a character produced by one
# unescape pass from becoming input to another while preserving the narrower
# substitutions that follow.
_ASSIGNMENT = re.compile(
    r"(?P<prefix>\b(?:const|let|var)\s+(?P<tmp>[A-Za-z_$][\w$]*)\s*=\s*)"
    r"(?P<expr>[^;\n]+)"
    r"(?P<suffix>\s*;)"
)
_BACKSLASH_COLLAPSE = r'.replace(/\\\\/g, "\\")'
_BACKSLASH_COLLAPSE_SINGLE_QUOTE = r".replace(/\\\\/g, '\\')"


def _temporary_is_parsed(source: str, end: int, name: str) -> bool:
    tail = source[end : end + 420]
    return re.search(rf"\bJSON\.parse\(\s*{re.escape(name)}\s*\)", tail) is not None


def _remove_staged_backslash_collapse(source: str) -> tuple[str, int]:
    cursor = 0
    parts: list[str] = []
    changes = 0
    for match in _ASSIGNMENT.finditer(source):
        if not _temporary_is_parsed(source, match.end(), match.group("tmp")):
            continue
        expr = match.group("expr")
        rewritten = expr.replace(_BACKSLASH_COLLAPSE, "").replace(
            _BACKSLASH_COLLAPSE_SINGLE_QUOTE, ""
        )
        if rewritten == expr:
            continue
        parts.append(source[cursor : match.start()])
        parts.append(match.group("prefix") + rewritten + match.group("suffix"))
        cursor = match.end()
        changes += 1
    if not changes:
        return source, 0
    parts.append(source[cursor:])
    return "".join(parts), changes


def apply(source: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    changes = 0
    cursor = 0
    parts: list[str] = []
    for match in _ASSIGN.finditer(source):
        if not _temporary_is_parsed(source, match.end(), match.group("tmp")):
            continue
        parts.append(source[cursor : match.start()])
        parts.append(match.group("prefix") + match.group("source") + match.group("suffix"))
        cursor = match.end()
        changes += 1
    if changes:
        parts.append(source[cursor:])
        output = "".join(parts)
    else:
        output = source

    output, inline_changes = _INLINE.subn(
        lambda match: f"JSON.parse({match.group('source')})",
        output,
    )
    changes += inline_changes

    output, staged_changes = _remove_staged_backslash_collapse(output)
    changes += staged_changes
    if not changes:
        return source

    marker = f"/* {MARKER}:{hashlib.sha256(str(changes).encode()).hexdigest()[:12]} */\n"
    if MARKER in output:
        return output
    return marker + output