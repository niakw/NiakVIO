#!/usr/bin/env python3
"""Learning-only repair for permissive CSS class regex token matching.

A JavaScript RegExp using a trailing \\b after a dynamic CSS class name treats
hyphen/underscore as token boundaries. That can make a requested class such as
"movie-card" also match "movie-card-format" or "movie-card-content".

This helper rewrites only class-attribute RegExp constructor expressions where
the dynamic class is immediately followed by a quoted \\b suffix. It contains
no provider names, domains, routes, or fixture-specific selectors.
"""
from __future__ import annotations

import re

MARKER = "/* NUVIO_HTML_CLASS_TOKEN_EXACT_V1 */"

_REGEXP = re.compile(
    r"new\s+RegExp\((?P<expr>[\s\S]*?),(?P<flags>[\"'][gimsuy]*[\"'])\s*\)"
)


def _rewrite_expr(expr: str) -> tuple[str, int]:
    if "class=" not in expr:
        return expr, 0
    output = expr
    changed = 0
    for old, new in (
        (r'+"\\b', r'+"(?![-_A-Za-z0-9])'),
        (r"+'\\b", r"+'(?![-_A-Za-z0-9])"),
    ):
        count = output.count(old)
        if count:
            output = output.replace(old, new)
            changed += count
    return output, changed


def apply(text: str) -> str:
    source = str(text or "")
    changed = False

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        expr, count = _rewrite_expr(match.group("expr"))
        if not count:
            return match.group(0)
        changed = True
        return f"new RegExp({expr},{match.group('flags')})"

    output = _REGEXP.sub(repl, source)
    if not changed:
        return source
    if MARKER not in output:
        output = MARKER + "\n" + output
    return output
