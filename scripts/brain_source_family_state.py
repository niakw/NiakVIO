#!/usr/bin/env python3
"""Fail-closed installed-state check for the promoted inline episode source parser."""
from __future__ import annotations

from pathlib import Path
from typing import Any

STRATEGY_ID = "catalogue_inline_token_episode_source_family_v1"
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
