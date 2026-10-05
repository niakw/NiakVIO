#!/usr/bin/env python3
"""Fail-closed guard for rebasing a validated Brain FORCE patch over neutral drift."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from import_external_brain_llm_guidance import source_drift

ROOT = Path(__file__).resolve().parents[1]


def classify(
    repo_root: Path,
    source_sha: str,
    current_sha: str,
    *,
    drift_fn: Callable[[Path, str, str], tuple[list[str], set[str]]] = source_drift,
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = classify(args.repo_root, args.source, args.current)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_ARCH_FORCE_REBASE_GUARD "
        f"safe={str(result['safe']).lower()} reason={result['reason']} "
        f"neutral={len(result['neutralPaths'])} providers={len(result['driftedProviders'])}"
    )
    return 0 if result["safe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
