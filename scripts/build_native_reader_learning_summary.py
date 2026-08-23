#!/usr/bin/env python3
"""Build the sanitized native-reader summary consumed by Brain skill learning."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
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


def number(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    state = load(args.state)
    memory = state.get("nativeReaderRepairMemory") if isinstance(state.get("nativeReaderRepairMemory"), dict) else {}
    learning = memory.get("readerLearningFailures") if isinstance(memory.get("readerLearningFailures"), dict) else {}
    entries = [row for row in learning.get("entries") or [] if isinstance(row, dict)]

    provider_failure_counts: Counter[str] = Counter()
    vendor_failure_counts: Counter[str] = Counter()
    providers_by_failure: dict[str, set[str]] = defaultdict(set)
    clients_by_failure: dict[str, set[str]] = defaultdict(set)
    by_provider: dict[str, dict[str, Any]] = {}
    vendor_rows: list[dict[str, Any]] = []
    repeated: list[dict[str, Any]] = []
    provider_total = 0
    vendor_total = 0

    for row in entries:
        provider = clean(row.get("providerId"), 128).casefold()
        failure = clean(row.get("failureClass"), 96) or "unknown_failure"
        owner = clean(row.get("owner"), 48) or "provider_learning"
        occurrences = number(row.get("occurrences"))
        if not provider or not occurrences:
            continue
        clients = {clean(v, 32).lower() for v in row.get("clients") or [] if clean(v, 32)}
        fixtures = {clean(v, 96) for v in row.get("fixtures") or [] if clean(v, 96)}

        if owner == "nuvio_vendor_wait":
            vendor_total += occurrences
            vendor_failure_counts[failure] += occurrences
            vendor_rows.append({
                "provider": provider,
                "failureClass": failure,
                "occurrences": occurrences,
                "clients": sorted(clients)[:8],
                "fixtures": sorted(fixtures)[:16],
                "owner": "nuvio_vendor_wait",
                "vendorWait": True,
                "providerMutationAllowed": False,
                "deepRetryRequested": False,
            })
            continue
        if owner != "provider_learning":
            continue

        provider_total += occurrences
        provider_failure_counts[failure] += occurrences
        providers_by_failure[failure].add(provider)
        clients_by_failure[failure].update(clients)
        target = by_provider.setdefault(provider, {
            "provider": provider,
            "occurrences": 0,
            "failureClasses": Counter(),
            "clients": set(),
            "fixtures": set(),
            "learningOnly": True,
            "providerMutationAllowed": False,
            "deepRetryRequested": True,
        })
        target["occurrences"] += occurrences
        target["failureClasses"][failure] += occurrences
        target["clients"].update(clients)
        target["fixtures"].update(fixtures)
        if occurrences >= 2:
            repeated.append({
                "provider": provider,
                "failureClass": failure,
                "occurrences": occurrences,
                "learningOnly": True,
                "providerMutationAllowed": False,
                "deepRetryRequested": True,
            })

    signals = [
        {
            "failureClass": failure,
            "occurrences": amount,
            "providers": sorted(providers_by_failure[failure])[:24],
            "clients": sorted(clients_by_failure[failure])[:8],
            "learningOnly": True,
            "owner": "provider_learning",
        }
        for failure, amount in provider_failure_counts.most_common()
    ]
    provider_rows = []
    for provider, row in sorted(by_provider.items(), key=lambda pair: (-pair[1]["occurrences"], pair[0])):
        provider_rows.append({
            "provider": provider,
            "occurrences": row["occurrences"],
            "failureClasses": dict(row["failureClasses"].most_common()),
            "clients": sorted(row["clients"])[:8],
            "fixtures": sorted(row["fixtures"])[:16],
            "learningOnly": True,
            "owner": "provider_learning",
            "providerMutationAllowed": False,
            "deepRetryRequested": True,
        })

    total_reader_failures = provider_total + vendor_total
    payload = {
        "schemaVersion": 2,
        "nativeReaderObserved": total_reader_failures,
        # Backward-compatible Brain field means provider-learning failures only.
        # Vendor-owned client/runtime failures are reported separately and must not
        # generate provider repair skills or satisfy provider repair accounting.
        "nativeReaderFailures": provider_total,
        "totalNativeReaderFailures": total_reader_failures,
        "providerLearningFailures": provider_total,
        "nuvioVendorWaitFailures": vendor_total,
        "readerFailureClasses": dict(provider_failure_counts.most_common()),
        "vendorFailureClasses": dict(vendor_failure_counts.most_common()),
        "readerFailureSignals": signals,
        "providerReaderFailures": provider_rows,
        "nuvioVendorWait": sorted(vendor_rows, key=lambda row: (-row["occurrences"], row["provider"], row["failureClass"]))[:120],
        "engineSignals": {"repeatedReaderFailures": repeated[:80]},
        "policy": {
            "failedReaderLearningIsNonBlocking": True,
            "incompleteEvidenceMayTrainSkills": True,
            "providerMutationFromIncompleteEvidence": False,
            "providerFailuresRequestIndependentDeepRetry": True,
            "nuvioClientRuntimeFailuresAreVendorWait": True,
            "vendorWaitDoesNotCreateProviderSkill": True,
            "labEmulationExcludedFromProviderLearning": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_NATIVE_READER_LEARNING_SUMMARY total_failures={total_reader_failures} "
        f"provider_learning={provider_total} vendor_wait={vendor_total} providers={len(provider_rows)} "
        f"classes={len(signals)} repeated={len(repeated)} blocking=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
