#!/usr/bin/env python3
"""Persist sanitized native-reader failures as learning-only Brain memory.

This channel intentionally accepts incomplete reader evidence. A player that never
opens is still useful evidence for skill learning, but incomplete evidence may never
authorize provider JS mutation or production publication. The stricter readerBacklog
continues to own mutation-eligible, complete evidence separately.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def clean(value: Any, limit: int = 128) -> str:
    text = str(value or "").strip()
    folded = text.casefold()
    if "://" in text or any(token in folded for token in ("authorization=", "cookie=", "token=", "secret=")):
        return ""
    return text[:limit]


def count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def normalized_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, raw in value.items():
        name = clean(key, 96) or "unknown_failure"
        amount = count(raw)
        if amount:
            out[name] = out.get(name, 0) + amount
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--diagnostics-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-entries", type=int, default=1000)
    args = parser.parse_args()

    run_id = clean(args.run_id, 32)
    if not run_id.isdigit():
        raise SystemExit(f"invalid run id: {run_id!r}")
    state = load(args.state)
    output = args.output or args.state
    memory = state.setdefault("nativeReaderRepairMemory", {})
    if not isinstance(memory, dict):
        memory = {}
        state["nativeReaderRepairMemory"] = memory
    learning = memory.get("readerLearningFailures") if isinstance(memory.get("readerLearningFailures"), dict) else {}
    previous = [row for row in learning.get("entries") or [] if isinstance(row, dict)]
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in previous:
        provider = clean(row.get("providerId"), 128).casefold()
        failure = clean(row.get("failureClass"), 96) or "unknown_failure"
        if provider:
            by_key[(provider, failure)] = row

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    imported_files = 0
    incomplete_files = 0
    observations = 0
    for path in sorted(args.diagnostics_root.rglob("*brain.json")) if args.diagnostics_root.exists() else []:
        report = load(path)
        if not report:
            continue
        imported_files += 1
        complete = report.get("evidenceComplete") is True
        if not complete:
            incomplete_files += 1
        outcomes = [row for row in report.get("providerOutcomes") or [] if isinstance(row, dict)]
        for outcome in outcomes:
            provider = clean(outcome.get("provider"), 128).casefold()
            if not provider:
                continue
            classes = normalized_counts(outcome.get("failureClasses"))
            load_classes = normalized_counts(outcome.get("loadFailureClasses"))
            for failure, amount in load_classes.items():
                classes[failure] = classes.get(failure, 0) + amount
            unresolved = count(outcome.get("failures")) + count(outcome.get("loadFailures"))
            if not classes and unresolved:
                classes["native_reader_unclassified"] = unresolved
            clients = sorted({clean(v, 32).lower() for v in outcome.get("clients") or [] if clean(v, 32)})[:16]
            fixtures = sorted({clean(v, 96) for v in outcome.get("fixtures") or [] if clean(v, 96)})[:32]
            for failure, amount in classes.items():
                if amount <= 0:
                    continue
                key = (provider, failure)
                row = by_key.get(key) or {
                    "providerId": provider,
                    "failureClass": failure,
                    "occurrences": 0,
                    "incompleteOccurrences": 0,
                    "completeOccurrences": 0,
                    "clients": [],
                    "fixtures": [],
                    "firstSeenAt": now,
                }
                row["occurrences"] = count(row.get("occurrences")) + amount
                bucket = "completeOccurrences" if complete else "incompleteOccurrences"
                row[bucket] = count(row.get(bucket)) + amount
                row["clients"] = sorted(set([*(row.get("clients") or []), *clients]))[:16]
                row["fixtures"] = sorted(set([*(row.get("fixtures") or []), *fixtures]))[:32]
                row["lastSeenAt"] = now
                row["lastRunId"] = run_id
                row["learningOnly"] = True
                row["providerJsMutationAllowed"] = False
                row["productionWritesAllowed"] = False
                row["deepRetryRequested"] = True
                row["lastEvidenceComplete"] = complete
                by_key[key] = row
                observations += amount

    # Preserve a report-level failure even when the incomplete native run could not
    # attribute it to a provider. This improves instrumentation/skill learning but is
    # deliberately excluded from provider-targeted mutation or Deep provider hints.
    if imported_files and not by_key:
        aggregate = 0
        for path in sorted(args.diagnostics_root.rglob("*brain.json")):
            aggregate += count(load(path).get("readerFailures"))
        if aggregate:
            memory["unattributedReaderLearningFailures"] = {
                "occurrences": count((memory.get("unattributedReaderLearningFailures") or {}).get("occurrences")) + aggregate,
                "lastRunId": run_id,
                "lastSeenAt": now,
                "learningOnly": True,
                "providerJsMutationAllowed": False,
                "deepRetryRequested": False,
            }

    entries = sorted(
        by_key.values(),
        key=lambda row: (-count(row.get("occurrences")), str(row.get("providerId")), str(row.get("failureClass"))),
    )[: max(1, int(args.max_entries))]
    imported_runs = [clean(v, 32) for v in learning.get("importedRunIds") or [] if clean(v, 32).isdigit()]
    imported_runs = [v for v in imported_runs if v != run_id] + [run_id]
    memory["readerLearningFailures"] = {
        "schemaVersion": 1,
        "updatedAt": now,
        "entries": entries,
        "importedRunIds": imported_runs[-100:],
        "policy": {
            "learningAllowedFromIncompleteEvidence": True,
            "providerMutationAllowed": False,
            "productionWritesAllowed": False,
            "deepRetryUsesIndependentEvidence": True,
        },
    }
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_NATIVE_READER_LEARNING_MERGE run={run_id} files={imported_files} "
        f"incomplete_files={incomplete_files} observations={observations} entries={len(entries)} "
        "blocking=false mutation_allowed=false deep_retry=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
