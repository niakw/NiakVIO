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
    # Harmless leading Qwen comments are metadata, not an executor algorithm;
    # remove only comment-only prefix lines before inspecting a wrapper guard.
    lines = code.splitlines(keepends=True)
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
    code = "".join(lines).strip("\n")
    if not code.strip() or len(code) > 4200:
        raise ValueError("architecture FORCE branchBody must contain bounded statements")
    if "\t" in code:
        raise ValueError("architecture FORCE branchBody must use spaces")

    # Qwen 7B sometimes wraps an otherwise valid branchBody in the NEW child's
    # if/elif guard, despite the body-only schema. Strip ONLY an exactly
    # child-bound single guard, by AST; never import/copy/modify the exhausted
    # parent, or accept multiple branches or an else fallback.
    if re.match(r"^\s*(?:if|elif)\s+new_strategy_id\s*(?:==|in\b)", code):
        guarded = re.sub(r"^\s*elif\b", "if", code, count=1)
        try:
            guarded_tree = ast.parse(guarded + "\n")
        except SyntaxError as exc:
            raise ValueError("architecture FORCE branchBody guard syntax invalid") from exc
        if len(guarded_tree.body) != 1 or not isinstance(guarded_tree.body[0], ast.If):
            raise ValueError("architecture FORCE branchBody must contain one new child guard")
        branch = guarded_tree.body[0]
        condition = branch.test
        condition_is_child = (
            isinstance(condition, ast.Compare)
            and isinstance(condition.left, ast.Name)
            and condition.left.id == "new_strategy_id"
            and len(condition.ops) == 1
            and len(condition.comparators) == 1
            and (
                (
                    isinstance(condition.ops[0], ast.Eq)
                    and isinstance(condition.comparators[0], ast.Constant)
                    and condition.comparators[0].value == child
                )
                or (
                    isinstance(condition.ops[0], ast.In)
                    and isinstance(condition.comparators[0], (ast.Set, ast.List, ast.Tuple))
                    and len(condition.comparators[0].elts) == 1
                    and isinstance(condition.comparators[0].elts[0], ast.Constant)
                    and condition.comparators[0].elts[0].value == child
                )
            )
        )
        if branch.orelse or not condition_is_child:
            raise ValueError("architecture FORCE branchBody guard is not isolated to new child")
        # Source extraction preserves the LLM-authored algorithm; the guard is
        # Brain-owned and regenerated from the trusted blueprint.
        lines = guarded.splitlines(keepends=True)
        code = textwrap.dedent("".join(lines[1:])).strip("\n")

    try:
        parsed = ast.parse("if True:\n" + textwrap.indent(code + "\n", "    "))
    except SyntaxError as exc:
        raise ValueError("architecture FORCE branchBody syntax invalid: " + str(exc.msg)) from exc
    # The old substring ban rejected valid Python whenever a Qwen comment or
    # media label merely mentioned "new_strategy_id". Guard ownership is an
    # AST property, NOT a byte substring property: only executable references
    # to the selector are forbidden. Constants/comments cannot alter strategy
    # selection and must not burn an entire FORCE run.
    if any(
        isinstance(node, ast.Name) and node.id == "new_strategy_id"
        for node in ast.walk(parsed)
    ):
        raise ValueError("architecture FORCE branchBody cannot read or mutate runtime strategy selector")
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
