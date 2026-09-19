#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate that a Deep run has publishable, internally consistent evidence.

This is the workflow-facing gate. It verifies that the staged transaction and
its evidence files exist and are structurally usable, then delegates the
per-provider/runtime/repair invariants to validate_deep_health_integrity.py.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HEALTH_VALIDATOR = ROOT / "scripts" / "validate_deep_health_integrity.py"


def load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{label}: missing or empty file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--repairs", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    candidates_path = args.stage / "candidates.json"

    try:
        candidates = load_object(candidates_path, "stage candidates")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        candidates = {}
        errors.append(str(exc))

    try:
        health = load_object(args.health, "health evidence")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        health = {}
        errors.append(str(exc))

    try:
        repairs = load_object(args.repairs, "repair evidence")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        repairs = {}
        errors.append(str(exc))

    staged_rows = candidates.get("candidates") if isinstance(candidates, dict) else None
    if not isinstance(staged_rows, list) or not staged_rows:
        errors.append("stage candidates: candidates[] is missing or empty")

    health_rows = health.get("results") if isinstance(health, dict) else None
    if not isinstance(health_rows, list) or not health_rows:
        errors.append("health evidence: results[] is missing or empty")

    if isinstance(repairs, dict) and not isinstance(repairs.get("rounds", []), list):
        errors.append("repair evidence: rounds must be an array")

    if not HEALTH_VALIDATOR.is_file():
        errors.append(f"missing delegated health validator: {HEALTH_VALIDATOR}")

    if errors:
        print("Deep evidence integrity validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    delegated = subprocess.run(
        [
            sys.executable,
            str(HEALTH_VALIDATOR),
            "--health",
            str(args.health),
            "--repairs",
            str(args.repairs),
        ],
        check=False,
    )
    if delegated.returncode != 0:
        return delegated.returncode

    print(
        "deep evidence integrity validation passed "
        f"(staged_candidates={len(staged_rows)}, providers={len(health_rows)}, "
        f"accepted_repairs={repairs.get('accepted_repairs', 0)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
