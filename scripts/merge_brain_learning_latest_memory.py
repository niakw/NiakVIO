#!/usr/bin/env python3
"""Three-way merge concurrent sanitized Brain Learning experiment memory.

Parallel targeted Learning cohorts are isolated by workflow concurrency keys.
Their publish jobs are globally serialized, but each experiment may have started
from the same older memory snapshot. Merge only the current cohort's delta over
that start snapshot into the latest already-published memory. This prevents both
lost family experience and double-counting historical counters.

This script has no provider mutation or publication authority.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from run_brain_learning_queue import _phase_experiment_key, merge_phase_learning_state


COUNTERS = ("attempts", "successes", "failures", "progresses")


def load(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    memory = payload.get("experimentMemory")
    if not isinstance(memory, dict):
        return []
    return [
        copy.deepcopy(row)
        for row in memory.get("entries") or []
        if isinstance(row, dict)
    ]


def by_key(payload: dict[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {_phase_experiment_key(row): row for row in entries(payload)}


def experiment_delta(
    base: dict[str, Any],
    current: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return only counter/outcome changes produced after the base snapshot."""
    before = by_key(base)
    delta: list[dict[str, Any]] = []
    for key, row in by_key(current).items():
        old = before.get(key)
        if old is None:
            delta.append(copy.deepcopy(row))
            continue

        counter_delta = {
            field: max(
                0,
                int(row.get(field) or 0) - int(old.get(field) or 0),
            )
            for field in COUNTERS
        }
        execution_new = (
            row.get("executionObserved") is True
            and old.get("executionObserved") is not True
        )
        generation_new = (
            row.get("generationAttemptObserved") is True
            and old.get("generationAttemptObserved") is not True
        )
        outcome_changed = (
            str(row.get("lastOutcome") or "")
            != str(old.get("lastOutcome") or "")
            or str(row.get("lastReason") or "")
            != str(old.get("lastReason") or "")
        )
        if (
            not any(counter_delta.values())
            and not execution_new
            and not generation_new
            and not outcome_changed
        ):
            continue

        item = copy.deepcopy(row)
        for field, value in counter_delta.items():
            item[field] = value
        item["consecutiveFailures"] = max(
            0,
            int(row.get("consecutiveFailures") or 0)
            - int(old.get("consecutiveFailures") or 0),
        )
        # merge_phase_learning_state treats a present row as one experiment.
        # Every changed phase is one observed experiment event.
        item["attempts"] = max(1, int(item.get("attempts") or 0))
        item["executionObserved"] = row.get("executionObserved") is True
        item["generationAttemptObserved"] = (
            row.get("generationAttemptObserved") is True
        )
        delta.append(item)
    delta.sort(key=_phase_experiment_key)
    return delta



def generated_ms(payload: dict[str, Any]) -> int:
    raw = str(payload.get("generatedAt") or "").strip()
    if not raw:
        return 0
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp() * 1000)


def merge_latest(
    base: dict[str, Any],
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    max_entries: int | None = None,
) -> dict[str, Any]:
    changes = experiment_delta(base, current)
    merged_state = merge_phase_learning_state(
        {
            "experimentMemory": copy.deepcopy(
                previous.get("experimentMemory") or {}
            )
        },
        changes,
        max_entries=max_entries,
    )
    previous_is_newer = generated_ms(previous) >= generated_ms(current) > 0
    output = copy.deepcopy(previous if previous_is_newer else current)
    output["experimentMemory"] = copy.deepcopy(
        merged_state.get("experimentMemory") or {}
    )
    output["publicationAllowed"] = False
    output["productionWritesAllowed"] = False
    output["concurrentMemoryMerge"] = {
        "schemaVersion": 1,
        "baseRows": len(entries(base)),
        "previousRows": len(entries(previous)),
        "currentRows": len(entries(current)),
        "deltaRows": len(changes),
        "mergedRows": len(entries(output)),
        "metadataSource": "previous" if previous_is_newer else "current",
        "publicationAuthority": False,
        "providerMutationAuthority": False,
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = merge_latest(
        load(args.base),
        load(args.previous),
        load(args.current),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    meta = output["concurrentMemoryMerge"]
    print(
        "FIELD_BRAIN_LEARNING_CONCURRENT_MEMORY_MERGE "
        f"base={meta['baseRows']} previous={meta['previousRows']} "
        f"current={meta['currentRows']} delta={meta['deltaRows']} "
        f"merged={meta['mergedRows']} publication_authority=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
