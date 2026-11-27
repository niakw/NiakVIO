#!/usr/bin/env python3
"""Fail-closed installed-state check for the promoted inline episode source parser."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

STRATEGY_ID = "catalogue_inline_token_episode_source_family_v1"
RESOLVER_STRATEGY_ID = "catalogue_inline_token_resolver_v2"
RESOLVER_CONTRACT = "same-origin-api-lien-j-l-v1"
RESOLVER_FAILURE_CLASS = "chain_terminal_gap"
SOURCE_BLUEPRINT: dict[str, Any] = {
    "strategyId": STRATEGY_ID,
    "gapKind": "missing_source_contract_family_executable",
    "targetLayer": "brain",
    "requiresNewExecutableRepairProfile": False,
    "requiresNewSourceFamilyLego": True,
    "sourceCompilerContract": "reader-matrix-v2",
    "providers": ["source-family-installed-state"],
}


def source_family_artifact_paths() -> list[str]:
    from brain_architecture_force_materializer import _source_family_artifact_paths
    row = _source_family_artifact_paths({"blueprint": SOURCE_BLUEPRINT})
    return [row["modulePath"], row["runtimePath"], row["testPath"]]


def source_family_parser_installed(root: Path) -> bool:
    """Return true only when the promoted parser still passes its trusted oracle."""
    try:
        from brain_architecture_force_materializer import validate_source_family_implementation
        paths = source_family_artifact_paths()
        root = root.resolve()
        if any(not (root / path).is_file() for path in paths):
            return False
        validate_source_family_implementation(paths, SOURCE_BLUEPRINT, root=root)
        return True
    except (ImportError, OSError, UnicodeError, ValueError):
        return False

def source_family_resolver_installed(root: Path) -> bool:
    """Require all executable selection gates plus the exact sanitized resolver contract."""
    try:
        root = root.resolve()
        required = (
            "scripts/brain_repair_runtime.py",
            "engine_v2/scripts/plan-repairs.mjs",
            "scripts/adaptive_runtime/runtime_repair.py",
        )
        texts: dict[str, str] = {}
        for relative in required:
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                return False
            texts[relative] = path.read_text(encoding="utf-8")
            if RESOLVER_STRATEGY_ID not in texts[relative]:
                return False
        runtime = texts["scripts/adaptive_runtime/runtime_repair.py"]
        begin = runtime.find("POST_EXHAUSTION_STRATEGY_PROFILES = {")
        end = runtime.find("\n}", begin)
        if begin < 0 or end < 0:
            return False
        if runtime[begin:end + 1].count(f'    "{RESOLVER_STRATEGY_ID}",\n') != 1:
            return False
        if not re.search(
            rf'(?m)^[ \t]*(?:if|elif)\s+new_strategy_id\s*==\s*["\']{re.escape(RESOLVER_STRATEGY_ID)}["\']\s*:\s*$',
            runtime,
        ):
            return False
        if RESOLVER_CONTRACT not in runtime:
            return False
        planner = texts["engine_v2/scripts/plan-repairs.mjs"]
        if planner.count(f'profile: "{RESOLVER_STRATEGY_ID}"') != 1:
            return False
        brain = texts["scripts/brain_repair_runtime.py"]
        p0 = brain.find("POST_EXHAUSTION_STRATEGY_PROFILES = {")
        p1 = brain.find("\n}", p0)
        if p0 < 0 or p1 < 0 or brain[p0:p1 + 1].count(
            f'    "{RESOLVER_STRATEGY_ID}",\n'
        ) != 1:
            return False
        return True
    except (OSError, UnicodeError, ValueError):
        return False
