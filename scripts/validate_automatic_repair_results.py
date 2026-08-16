#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate accepted automatic repairs with mode-appropriate safety policy."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from repair_identity_gate import (  # noqa: E402
    automatic_repair_identity_gate,
    automatic_repair_safety_gate,
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def validate(registry: dict[str, Any], health: dict[str, Any], repair: dict[str, Any]) -> list[str]:
    results = {
        str(row.get("key")): row
        for row in health.get("results") or []
        if isinstance(row, dict) and row.get("key")
    }
    repaired_candidates = [
        row for row in registry.get("candidates") or []
        if isinstance(row, dict) and row.get("repair_history")
    ]
    failures: list[str] = []
    accepted_events = 0
    mode = str(health.get("mode") or repair.get("mode") or "deep").casefold()
    gate = automatic_repair_safety_gate if mode == "quick" else automatic_repair_identity_gate

    for candidate in repaired_candidates:
        key = str(candidate.get("key") or "")
        history = [
            event for event in candidate.get("repair_history") or []
            if isinstance(event, dict) and event.get("accepted")
        ]
        accepted_events += len(history)
        result = results.get(key)
        if result is None:
            failures.append(f"{key}: accepted repair has no final health result")
            continue

        ok, reason = gate(result)
        if not ok:
            failures.append(f"{key}: {reason}")

    reported = int(repair.get("accepted_repairs") or 0)
    if reported != accepted_events:
        failures.append(
            f"repair accounting mismatch: report={reported} candidate_history={accepted_events}"
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=Path("staging"))
    parser.add_argument("--health", type=Path, default=Path("health-output/health-results.json"))
    parser.add_argument("--repairs", type=Path, default=Path("health-output/repair-report.json"))
    args = parser.parse_args()

    registry = _load(args.stage / "candidates.json")
    health = _load(args.health)
    repair = _load(args.repairs)
    failures = validate(registry, health, repair)
    if failures:
        raise SystemExit("automatic repair gate failed:\n- " + "\n- ".join(failures))
    print(
        "automatic repair gate passed: "
        f"mode={health.get('mode')} policy={repair.get('acceptance_policy') or 'strict_identity'} "
        f"accepted_repairs={int(repair.get('accepted_repairs') or 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
