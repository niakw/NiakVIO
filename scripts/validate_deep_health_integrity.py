#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail publication when the deep harness itself produced ambiguous evidence.

Provider failures are allowed. Harness failures are not: malformed invocation
arguments, missing structured exceptions, duplicate deterministic repair
retests, or accepted source rewrites without improved playable-stream proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--repairs", type=Path, required=True)
    args = parser.parse_args()

    health = load(args.health)
    repairs = load(args.repairs)
    errors: list[str] = []

    for result in health.get("results") or []:
        key = str(result.get("key") or result.get("canonical_id") or "unknown")
        for index, test in enumerate(result.get("tests") or []):
            label = (test.get("fixture") or {}).get("label") or index
            status = str(test.get("status") or "")
            detail = test.get("error_details") or {}
            if status == "runtime_error" and not (detail.get("message") or detail.get("name") or detail.get("code")):

                errors.append(f"{key}:{label}: runtime_error without structured error details")
            if test.get("worker_ok") is False and not (detail.get("message") or test.get("error")):
                errors.append(f"{key}:{label}: failed worker without diagnostic message")
            for observation in test.get("network_observations") or []:
                path_pattern = str(observation.get("path_pattern") or "").casefold()
                if observation.get("error_code") == "NUVIO_INVALID_REQUEST_ARGUMENT" or "object%20object" in path_pattern or "object object" in path_pattern:
                    errors.append(f"{key}:{label}: malformed invocation request was not contained")
            if status == "no_streams" and test.get("failure_class") != "content_lookup_completed_no_streams":
                errors.append(f"{key}:{label}: no_streams lacks successful content-lookup proof")

    fingerprints: set[tuple[str, str, str]] = set()
    for round_row in repairs.get("rounds") or []:
        round_number = round_row.get("round")
        for attempt in round_row.get("attempts") or []:
            if attempt.get("status") != "generated":
                continue
            fingerprint = (
                str(attempt.get("parent_sha256") or ""),
                str(attempt.get("profile") or ""),
                str(attempt.get("repair_sha256") or ""),
            )
            if fingerprint in fingerprints:
                errors.append(f"repair round {round_number}: identical deterministic repair retested: {fingerprint[1]}")
            fingerprints.add(fingerprint)
        for accepted in round_row.get("accepted") or []:
            before = int(accepted.get("streams_playable_before") or 0)
            after = int(accepted.get("streams_playable_after") or 0)
            if after <= before:
                errors.append(
                    f"repair round {round_number}:{accepted.get('parent_key')}: accepted without playable-stream improvement"
                )
            runtime_before = int(accepted.get("runtime_errors_before") or 0)
            runtime_after = int(accepted.get("runtime_errors_after") or 0)
            if runtime_after > runtime_before:
                errors.append(
                    f"repair round {round_number}:{accepted.get('parent_key')}: accepted after introducing runtime errors"
                )
            if accepted.get("reason") != "strict_playable_stream_improvement":
                errors.append(
                    f"repair round {round_number}:{accepted.get('parent_key')}: non-strict repair reason {accepted.get('reason')}"
                )
        for rejected in round_row.get("rejected") or []:
            if rejected.get("status") == "runtime_error" and not rejected.get("error_summary"):
                errors.append(
                    f"repair round {round_number}:{rejected.get('parent_key')}: runtime repair error not preserved"
                )

    if errors:
        print("Deep health integrity validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "deep health integrity validation passed "
        f"(providers={len(health.get('results') or [])}, accepted_repairs={repairs.get('accepted_repairs', 0)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
