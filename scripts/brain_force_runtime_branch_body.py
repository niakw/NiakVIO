#!/usr/bin/env python3
"""Deterministically scaffold a novel Brain-generated runtime branch body.

Qwen owns the NEW algorithm's statements, never the exhausted parent's guard
or the registration boilerplate. Ambiguous source structure fails closed.
"""
from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from typing import Any

RUNTIME = "scripts/adaptive_runtime/runtime_repair.py"
STRATEGY_ID = re.compile(r"[a-z][a-z0-9_]*_v\d+\Z")


def branch_body_edit(
    body: str,
    blueprint: dict[str, Any],
    *,
    root: Path,
    max_find: int = 600,
    max_replace: int = 5000,
) -> dict[str, str]:
    child = str(blueprint.get("strategyId") or "").strip()
    parent = str(blueprint.get("evolvesFromStrategyId") or "").strip()
    if not STRATEGY_ID.fullmatch(child) or not STRATEGY_ID.fullmatch(parent) or child == parent:
        raise ValueError("architecture FORCE invalid child/parent strategy IDs")
    code = textwrap.dedent(str(body or "")).strip("\n")
    if not code.strip() or len(code) > 4200 or "new_strategy_id" in code:
        raise ValueError("architecture FORCE branchBody must contain bounded statements, not guards")
    if "\t" in code:
        raise ValueError("architecture FORCE branchBody must use spaces")
    try:
        parsed = ast.parse("if True:\n" + textwrap.indent(code + "\n", "    "))
    except SyntaxError as exc:
        raise ValueError("architecture FORCE branchBody syntax invalid: " + str(exc.msg)) from exc
    nodes = parsed.body[0].body
    if not any(
        not isinstance(node, ast.Pass)
        and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
        for node in nodes
    ):
        raise ValueError("architecture FORCE branchBody has no executable behavior")
    if any(isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)) for node in ast.walk(parsed)):
        raise ValueError("architecture FORCE branchBody cannot change global/module scope")

    source = (root / RUNTIME).read_text(encoding="utf-8")
    parent_pattern = re.compile(
        rf'(?m)^(?P<indent>[ \t]*)(?:if|elif)\s+new_strategy_id\s*==\s*["\']{re.escape(parent)}["\']\s*:\s*$'
    )
    parents = list(parent_pattern.finditer(source))
    if len(parents) != 1:
        raise ValueError("architecture FORCE parent runtime guard ambiguous")
    original = parents[0]
    indent = original.group("indent")
    next_sibling = re.search(
        rf'(?m)^{re.escape(indent)}(?:elif\s+new_strategy_id\b|else\s*:)',
        source[original.end():],
    )
    if next_sibling is None:
        raise ValueError("architecture FORCE subsequent runtime sibling missing")
    offset = original.end() + next_sibling.start()
    line_end = source.find("\n", offset)
    if line_end < 0:
        raise ValueError("architecture FORCE subsequent runtime sibling line incomplete")
    find = source[offset:line_end + 1]
    if not find or len(find) > max_find or source.count(find) != 1:
        raise ValueError("architecture FORCE sibling insert anchor ambiguous")
    candidate = (
        f'{indent}elif new_strategy_id == "{child}":\n'
        + textwrap.indent(code + "\n", indent + "    ")
        + find
    )
    if len(candidate) > max_replace:
        raise ValueError("architecture FORCE generated branch exceeds bounded edit")
    return {"operation": "replace", "path": RUNTIME, "find": find, "replace": candidate}
