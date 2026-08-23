#!/usr/bin/env python3
"""Persist sanitized native-reader failures as nonblocking Brain memory.

Incomplete reader evidence is allowed to improve diagnosis and skill learning, but it
never authorizes provider mutation. Ownership is explicit:
- provider_stream/provider_extraction -> provider learning + independent Deep retry;
- client_runtime -> official Nuvio vendor-wait memory, no provider mutation/retry;
- lab_emulation -> excluded from provider learning and left to Lab final validation.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CLIENT_RUNTIME_CLASSES = {
    "playback_runtime_setup",
    "playback_player_error",
    "playback_decoder",
}


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


def owner_for(row: dict[str, Any]) -> str:
    domain = clean(row.get("failureDomain"), 64).casefold()
    failure = clean(row.get("failureClass"), 96) or "unknown_failure"
    if domain == "lab_emulation":
        return "lab_emulation"
    if domain == "client_runtime" or failure in CLIENT_RUNTIME_CLASSES:
        return "nuvio_vendor_wait"
    if domain in {"provider_stream", "provider_extraction"} or bool(row.get("providerMutationEligible")):
        return "provider_learning"
    if clean(row.get("failureStage"), 64).casefold() == "media_extraction":
        return "provider_learning"
    return "unresolved_nonblocking"


def key_for(provider: str, failure: str, owner: str) -> tuple[str, str, str]:
    return provider, failure, owner


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
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in previous:
        provider = clean(row.get("providerId"), 128).casefold()
        failure = clean(row.get("failureClass"), 96) or "unknown_failure"
        owner = clean(row.get("owner"), 48) or "provider_learning"
        if provider:
            by_key[key_for(provider, failure, owner)] = row

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    imported_files = 0
    incomplete_files = 0
    observed = 0
    lab_excluded = 0
    owner_counts: dict[str, int] = {}

    for path in sorted(args.diagnostics_root.rglob("*brain.json")) if args.diagnostics_root.exists() else []:
        report = load(path)
        if not report:
            continue
        imported_files += 1
        complete = report.get("evidenceComplete") is True
        if not complete:
            incomplete_files += 1

        observations = [row for row in report.get("observations") or [] if isinstance(row, dict)]
        for raw in observations:
            if clean(raw.get("routeMode"), 32).casefold() == "capability_probe":
                continue
            failure = clean(raw.get("failureClass"), 96) or "unknown_failure"
            if failure == "healthy":
                continue
            provider = clean(raw.get("provider"), 128).casefold()
            if not provider:
                continue
            owner = owner_for(raw)
            if owner == "lab_emulation":
                lab_excluded += 1
                owner_counts[owner] = owner_counts.get(owner, 0) + 1
                continue
            k = key_for(provider, failure, owner)
            row = by_key.get(k) or {
                "providerId": provider,
                "failureClass": failure,
                "owner": owner,
                "occurrences": 0,
                "incompleteOccurrences": 0,
                "completeOccurrences": 0,
                "clients": [],
                "fixtures": [],
                "firstSeenAt": now,
            }
            row["occurrences"] = count(row.get("occurrences")) + 1
            bucket = "completeOccurrences" if complete else "incompleteOccurrences"
            row[bucket] = count(row.get(bucket)) + 1
            client = clean(raw.get("client"), 32).lower()
            fixture = clean(raw.get("fixture"), 96)
            row["clients"] = sorted(set([*(row.get("clients") or []), *([client] if client else [])]))[:16]
            row["fixtures"] = sorted(set([*(row.get("fixtures") or []), *([fixture] if fixture else [])]))[:32]
            row["lastSeenAt"] = now
            row["lastRunId"] = run_id
            row["learningOnly"] = True
            row["providerJsMutationAllowed"] = False
            row["productionWritesAllowed"] = False
            row["deepRetryRequested"] = owner == "provider_learning"
            row["vendorWait"] = owner == "nuvio_vendor_wait"
            row["lastEvidenceComplete"] = complete
            by_key[k] = row
            observed += 1
            owner_counts[owner] = owner_counts.get(owner, 0) + 1

        # Backward-compatible fallback for older diagnoses without observation rows.
        if not observations:
            for outcome in [row for row in report.get("providerOutcomes") or [] if isinstance(row, dict)]:
                provider = clean(outcome.get("provider"), 128).casefold()
                if not provider:
                    continue
                provider_failures = count(outcome.get("providerEligibleFailures")) + count(outcome.get("extractionFailures"))
                vendor_failures = count(outcome.get("clientRuntimeFailures"))
                for failure, amount in (("native_reader_unclassified", provider_failures), ("playback_player_error", vendor_failures)):
                    if amount <= 0:
                        continue
                    owner = "provider_learning" if failure == "native_reader_unclassified" else "nuvio_vendor_wait"
                    k = key_for(provider, failure, owner)
                    row = by_key.get(k) or {
                        "providerId": provider, "failureClass": failure, "owner": owner,
                        "occurrences": 0, "incompleteOccurrences": 0, "completeOccurrences": 0,
                        "clients": [], "fixtures": [], "firstSeenAt": now,
                    }
                    row["occurrences"] = count(row.get("occurrences")) + amount
                    row["incompleteOccurrences" if not complete else "completeOccurrences"] = count(row.get("incompleteOccurrences" if not complete else "completeOccurrences")) + amount
                    row["lastSeenAt"] = now
                    row["lastRunId"] = run_id
                    row["learningOnly"] = True
                    row["providerJsMutationAllowed"] = False
                    row["productionWritesAllowed"] = False
                    row["deepRetryRequested"] = owner == "provider_learning"
                    row["vendorWait"] = owner == "nuvio_vendor_wait"
                    row["lastEvidenceComplete"] = complete
                    by_key[k] = row
                    observed += amount
                    owner_counts[owner] = owner_counts.get(owner, 0) + amount

    entries = sorted(
        by_key.values(),
        key=lambda row: (-count(row.get("occurrences")), str(row.get("providerId")), str(row.get("failureClass")), str(row.get("owner"))),
    )[: max(1, int(args.max_entries))]
    imported_runs = [clean(v, 32) for v in learning.get("importedRunIds") or [] if clean(v, 32).isdigit()]
    imported_runs = [v for v in imported_runs if v != run_id] + [run_id]
    memory["readerLearningFailures"] = {
        "schemaVersion": 2,
        "updatedAt": now,
        "entries": entries,
        "importedRunIds": imported_runs[-100:],
        "lastRunOwnershipCounts": dict(sorted(owner_counts.items())),
        "labEmulationExcluded": lab_excluded,
        "policy": {
            "learningAllowedFromIncompleteEvidence": True,
            "providerMutationAllowed": False,
            "productionWritesAllowed": False,
            "providerFailuresRequestIndependentDeepRetry": True,
            "nuvioClientRuntimeFailuresAreVendorWait": True,
            "labEmulationExcludedFromProviderLearning": True,
        },
    }
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_NATIVE_READER_LEARNING_MERGE run={run_id} files={imported_files} "
        f"incomplete_files={incomplete_files} observations={observed} entries={len(entries)} "
        f"provider_learning={owner_counts.get('provider_learning', 0)} "
        f"vendor_wait={owner_counts.get('nuvio_vendor_wait', 0)} lab_excluded={lab_excluded} "
        "blocking=false mutation_allowed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
