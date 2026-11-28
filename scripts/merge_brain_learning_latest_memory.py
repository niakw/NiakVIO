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

from run_brain_learning_queue import (
    _phase_experiment_key,
    apply_diagnostic_network_backfill,
    merge_phase_learning_state,
)


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



def telemetry_backfills(
    base: dict[str, Any],
    current: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return same-experiment telemetry enrichments without inventing attempts."""
    before = by_key(base)
    output: list[dict[str, Any]] = []
    for key, row in by_key(current).items():
        old = before.get(key)
        if old is None:
            continue
        summary = row.get("networkExecutionSummary")
        delta = row.get("networkExecutionDelta")
        summary_changed = (
            isinstance(summary, dict)
            and "providerRequestCount" in summary
            and summary != old.get("networkExecutionSummary")
        )
        delta_changed = (
            isinstance(delta, dict)
            and "providerRequestDelta" in delta
            and delta != old.get("networkExecutionDelta")
        )
        if not summary_changed and not delta_changed:
            continue
        output.append(copy.deepcopy(row))
    output.sort(key=_phase_experiment_key)
    return output



def _queue_ids(value: Any) -> list[str]:
    rows = value if isinstance(value, list) else []
    output: list[str] = []
    seen: set[str] = set()
    for raw in rows:
        provider = str(raw or "").strip().casefold().replace("_", "-")[:128]
        if provider and provider not in seen:
            seen.add(provider)
            output.append(provider)
    return output[:256]


def merge_learning_queue_delta(
    base: dict[str, Any],
    previous: dict[str, Any],
    current: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply only the current cohort's provider-local queue delta.

    Parallel family runs may start from the same queue snapshot. The latest
    publisher must preserve sibling updates already on the durable branch while
    allowing a freshly re-observed provider to clear its own stale hidden state.
    """
    base_queue = base.get("learningQueue") if isinstance(base.get("learningQueue"), dict) else {}
    previous_queue = previous.get("learningQueue") if isinstance(previous.get("learningQueue"), dict) else {}
    current_queue = current.get("learningQueue") if isinstance(current.get("learningQueue"), dict) else {}
    if not previous_queue and not current_queue:
        return {}, {
            "processedProviders": [],
            "hiddenClearedProviders": [],
            "hiddenAddedProviders": [],
        }

    output = copy.deepcopy(previous_queue or base_queue or current_queue)
    processed = _queue_ids(current_queue.get("processedThisRun"))
    processed_set = set(processed)

    previous_hidden = _queue_ids(output.get("hiddenFailureProviders"))
    current_hidden = _queue_ids(current_queue.get("hiddenFailureProviders"))
    current_hidden_set = set(current_hidden)
    hidden_cleared = [
        provider for provider in processed
        if provider in set(previous_hidden) and provider not in current_hidden_set
    ]
    hidden_added = [
        provider for provider in processed
        if provider in current_hidden_set and provider not in set(previous_hidden)
    ]
    output["hiddenFailureProviders"] = _queue_ids([
        *[provider for provider in previous_hidden if provider not in processed_set],
        *current_hidden,
    ])

    for field in ("pendingProviders", "retryProviders", "completedInCycle"):
        existing = _queue_ids(output.get(field))
        current_ids = _queue_ids(current_queue.get(field))
        current_set = set(current_ids)
        next_rows = [provider for provider in existing if provider not in processed_set]
        next_rows.extend(
            provider for provider in processed
            if provider in current_set
        )
        output[field] = _queue_ids(next_rows)

    previous_state = output.get("providerState") if isinstance(output.get("providerState"), dict) else {}
    current_state = current_queue.get("providerState") if isinstance(current_queue.get("providerState"), dict) else {}
    merged_provider_state = copy.deepcopy(previous_state)
    for provider in processed:
        if isinstance(current_state.get(provider), dict):
            merged_provider_state[provider] = copy.deepcopy(current_state[provider])
    output["providerState"] = merged_provider_state
    output["processedThisRun"] = processed

    for field in (
        "schemaVersion",
        "cycle",
        "resumeAcrossDays",
        "coreEvidenceAuthority",
        "timeBudgetExhausted",
        "remainingProviderCount",
        "retryProviderCount",
        "budgetMinutes",
        "generatedAt",
    ):
        if field in current_queue:
            output[field] = copy.deepcopy(current_queue[field])

    return output, {
        "processedProviders": processed,
        "hiddenClearedProviders": hidden_cleared,
        "hiddenAddedProviders": hidden_added,
    }


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
    telemetry = telemetry_backfills(base, current)
    merged_state = merge_phase_learning_state(
        {
            "experimentMemory": copy.deepcopy(
                previous.get("experimentMemory") or {}
            )
        },
        changes,
        max_entries=max_entries,
    )
    for backfill in telemetry:
        merged_rows = (
            merged_state.get("experimentMemory", {}).get("entries", [])
            if isinstance(merged_state.get("experimentMemory"), dict)
            else []
        )
        key = _phase_experiment_key(backfill)
        if any(
            isinstance(row, dict) and _phase_experiment_key(row) == key
            for row in merged_rows
        ):
            merged_state = apply_diagnostic_network_backfill(
                merged_state,
                backfill,
            )
        else:
            # A concurrent compaction may have removed the historical row.
            # Reinsert the exact sanitized current row without recounting it.
            merged_state = merge_phase_learning_state(
                merged_state,
                [backfill],
                max_entries=max_entries,
            )
    previous_is_newer = generated_ms(previous) >= generated_ms(current) > 0
    output = copy.deepcopy(previous if previous_is_newer else current)
    output["experimentMemory"] = copy.deepcopy(
        merged_state.get("experimentMemory") or {}
    )
    merged_queue, queue_delta = merge_learning_queue_delta(
        base, previous, current
    )
    if merged_queue:
        output["learningQueue"] = merged_queue
    output["publicationAllowed"] = False
    output["productionWritesAllowed"] = False
    output["concurrentMemoryMerge"] = {
        "schemaVersion": 1,
        "baseRows": len(entries(base)),
        "previousRows": len(entries(previous)),
        "currentRows": len(entries(current)),
        "deltaRows": len(changes),
        "telemetryDeltaRows": len(telemetry),
        "mergedRows": len(entries(output)),
        "metadataSource": "previous" if previous_is_newer else "current",
        "queueProcessedProviders": queue_delta["processedProviders"],
        "queueHiddenClearedProviders": queue_delta["hiddenClearedProviders"],
        "queueHiddenAddedProviders": queue_delta["hiddenAddedProviders"],
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
        f"merged={meta['mergedRows']} "
        f"queue_processed={len(meta['queueProcessedProviders'])} "
        f"queue_hidden_cleared={len(meta['queueHiddenClearedProviders'])} "
        f"publication_authority=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
