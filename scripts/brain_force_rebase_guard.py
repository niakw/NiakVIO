#!/usr/bin/env python3
"""Fail-closed guard for rebasing a validated Brain FORCE patch over neutral drift."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from import_external_brain_llm_guidance import source_drift

ROOT = SCRIPT_DIR.parent


def patch_changed_paths(patch: str) -> set[str]:
    """Read exact changed paths from the validated, allowlisted git diff.

    Fail closed on unknown paths/header formats. Only the Brain's known
    repository-relative file names are supported here; do not guess a path
    from a truncated, renamed, binary or quoted Git header.
    """
    headers = [line for line in patch.splitlines() if line.startswith("diff --git ")]
    if not headers:
        raise ValueError("architecture FORCE patch has no git file headers")
    paths: set[str] = set()
    for header in headers:
        match = re.fullmatch(r"diff --git a/([^\s\"\\]+) b/([^\s\"\\]+)", header)
        if not match or match.group(1) != match.group(2):
            raise ValueError("architecture FORCE patch path is ambiguous")
        path = match.group(1)
        if path.startswith("/") or path.startswith("../") or "/../" in path:
            raise ValueError("architecture FORCE patch escapes repository")
        paths.add(path)
    return paths


def classify(
    repo_root: Path,
    source_sha: str,
    current_sha: str,
    *,
    drift_fn: Callable[[Path, str, str], tuple[list[str], set[str]]] = source_drift,
    patch_paths: set[str] | None = None,
) -> dict[str, Any]:
    try:
        neutral_paths, drifted_providers = drift_fn(repo_root, source_sha, current_sha)
    except ValueError as exc:
        return {
            "safe": False,
            "reason": "non-neutral-drift",
            "detail": str(exc)[:1000],
            "neutralPaths": [],
            "driftedProviders": [],
        }
    if drifted_providers:
        return {
            "safe": False,
            "reason": "provider-drift",
            "detail": "",
            "neutralPaths": neutral_paths,
            "driftedProviders": sorted(drifted_providers),
        }
    # A change is neutral for provider identity without being neutral for
    # generated Brain code. In run 42411463034 another FORCE had already
    # appended to the same planner/runtime registries. The former guard
    # admitted the rebase and git apply then failed on these exact files.
    overlapping = sorted(set(neutral_paths).intersection(patch_paths or ()))
    if overlapping:
        return {
            "safe": False,
            "reason": "architecture-edit-overlap",
            "detail": ",".join(overlapping)[:1000],
            "neutralPaths": neutral_paths,
            "driftedProviders": [],
            "overlapPaths": overlapping,
        }
    return {
        "safe": True,
        "reason": "neutral-only",
        "detail": "",
        "neutralPaths": neutral_paths,
        "driftedProviders": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        generated_paths = patch_changed_paths(args.patch.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        print("FIELD_BRAIN_ARCH_FORCE_REBASE_GUARD safe=false reason=invalid-patch-paths")
        return 2
    result = classify(
        args.repo_root, args.source, args.current, patch_paths=generated_paths,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_ARCH_FORCE_REBASE_GUARD "
        f"safe={str(result['safe']).lower()} reason={result['reason']} "
        f"neutral={len(result['neutralPaths'])} providers={len(result['driftedProviders'])} "
        f"overlap={len(result.get('overlapPaths') or [])}"
    )
    return 0 if result["safe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
