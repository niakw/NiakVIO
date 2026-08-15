#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate that every accepted automatic repair has strict playable identity proof."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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

        evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
        playable = int(evidence.get("streams_playable") or 0)
        contradictions = int(evidence.get("identity_contradiction_count") or 0)
        duration_mismatches = int(evidence.get("duration_identity_mismatch_count") or 0)
        verified = int(evidence.get("identity_verified_streams") or 0)
        unknown = int(evidence.get("identity_unverified_streams") or 0)

        if playable <= 0:
            failures.append(f"{key}: accepted repair has no playable proof")
        if contradictions > 0:
            failures.append(f"{key}: accepted repair has content identity contradiction")
        if duration_mismatches > 0:
            failures.append(f"{key}: accepted repair has duration identity mismatch")
        if verified <= 0:
            failures.append(f"{key}: accepted repair has no positive content identity proof")

        playable_tests = [
            test for test in result.get("tests") or []
            if isinstance(test, dict) and int(test.get("streams_playable") or 0) > 0
        ]
        if not playable_tests and (unknown > 0 or verified < playable):
            failures.append(f"{key}: accepted repair playable identity is unresolved")

        for test in playable_tests:
            count = int(test.get("streams_playable") or 0)
            test_verified = int(test.get("identity_verified_streams") or 0)
            test_unknown = int(test.get("identity_unverified_streams") or 0)
            test_contradictions = int(test.get("identity_contradiction_count") or 0)
            test_duration = int(test.get("duration_identity_mismatch_count") or 0)
            fixture = (
                (test.get("fixture") or {}).get("label")
                or (test.get("fixture") or {}).get("tmdbId")
                or "fixture"
            )
            if test_contradictions > 0:
                failures.append(f"{key}/{fixture}: playable repair sample has identity contradiction")
            if test_duration > 0:
                failures.append(f"{key}/{fixture}: playable repair sample has duration mismatch")
            if test_verified < count or test_unknown > 0:
                failures.append(f"{key}/{fixture}: playable repair sample is not fully identity-verified")

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
        raise SystemExit("automatic repair identity gate failed:\n- " + "\n- ".join(failures))
    print(
        "automatic repair identity gate passed: "
        f"mode={health.get('mode')} accepted_repairs={int(repair.get('accepted_repairs') or 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
