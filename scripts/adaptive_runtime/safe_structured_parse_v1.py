#!/usr/bin/env python3
"""Learning-only repair for destructive backslash stripping before JSON.parse.

This helper belongs exclusively to adaptive_runtime Learning. It must never be
composed into durable Provider v3 bundles or referenced as a provider Core Lego.
"""
from __future__ import annotations

import re

MARKER = "/* NUVIO_SAFE_STRUCTURED_PARSE_V1 */"

_ASSIGN = re.compile(
    r"(?P<prefix>\b(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*)"
    r"(?P<raw>[A-Za-z_$][\w$]*)\.replace\(/\\\\\(\.\)/g,\s*[\"']\$1[\"']\s*\)"
)
_INLINE = re.compile(
    r"JSON\.parse\(\s*(?P<raw>[A-Za-z_$][\w$]*)\.replace\(/\\\\\(\.\)/g,\s*[\"']\$1[\"']\s*\)\s*\)"
)


def apply(text: str) -> str:
    source = str(text or "")
    changed = False

    def inline(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        return f"JSON.parse({match.group('raw')})"

    output = _INLINE.sub(inline, source)

    assignments = list(_ASSIGN.finditer(output))
    for match in reversed(assignments):
        name = match.group("name")
        tail = output[match.end():]
        if re.search(rf"JSON\.parse\(\s*{re.escape(name)}\s*\)", tail) is None:
            continue
        replacement = f"{match.group('prefix')}{match.group('raw')}"
        output = output[:match.start()] + replacement + output[match.end():]
        changed = True

    if not changed:
        return source
    if MARKER not in output:
        output = MARKER + "\n" + output
    return output
