#!/usr/bin/env python3
"""Compare native-reader outcomes before/after a Brain sandbox mutation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def aggregate(diagnosis: dict[str, Any], fixture: str) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for raw in diagnosis.get("observations") or []:
        if not isinstance(raw, dict) or str(raw.get("fixture") or "") != fixture:
            continue
        provider = str(raw.get("provider") or "").casefold().strip()
        if not provider:
            continue
        row = output.setdefault(provider, {"observed": 0, "healthy": 0, "failures": 0, "failureClasses": {}})
        row["observed"] += 1
        failure = str(raw.get("failureClass") or "unknown_failure")
        if failure == "healthy":
            row["healthy"] += 1
        else:
            row["failures"] += 1
            row["failureClasses"][failure] = int(row["failureClasses"].get(failure) or 0) + 1
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--repair-report", type=Path, required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    before = aggregate(load_json(args.before), args.fixture)
    after = aggregate(load_json(args.after), args.fixture)
    repair = load_json(args.repair_report)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    inconclusive: list[dict[str, Any]] = []

    for proposal in repair.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        provider = str(proposal.get("provider") or "").casefold().strip()
        pre = before.get(provider, {"observed": 0, "healthy": 0, "failures": 0, "failureClasses": {}})
        post = after.get(provider, {"observed": 0, "healthy": 0, "failures": 0, "failureClasses": {}})
        row = {
            "provider": provider,
            "candidateFile": proposal.get("candidateFile"),
            "skills": proposal.get("skills") or [],
            "before": pre,
            "after": post,
        }
        if int(pre["failures"]) <= 0:
            row["reason"] = "no_baseline_reader_failure_for_fixture"
            inconclusive.append(row)
        elif int(post["observed"]) <= 0:
            row["reason"] = "no_fresh_reader_evidence_after_mutation"
            inconclusive.append(row)
        elif int(post["failures"]) == 0 and int(post["healthy"]) == int(post["observed"]):
            row["reason"] = "fresh_native_reader_proof_green"
            accepted.append(row)
        else:
            row["reason"] = "reader_failure_persisted_or_changed"
            rejected.append(row)

    payload = {
        "schemaVersion": 1,
        "fixture": args.fixture,
        "acceptedCount": len(accepted),
        "rejectedCount": len(rejected),
        "inconclusiveCount": len(inconclusive),
        "acceptedProviders": [row["provider"] for row in accepted],
        "rejectedProviders": [row["provider"] for row in rejected],
        "accepted": accepted,
        "rejected": rejected,
        "inconclusive": inconclusive,
        "policy": {
            "productionWritesAllowed": False,
            "publicationAllowed": False,
            "acceptedRequiresAllPlayedStreamsHealthy": True,
            "freshNativeReaderProofRequired": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_NATIVE_READER_REPAIR_COMPARE fixture={args.fixture} accepted={len(accepted)} "
        f"rejected={len(rejected)} inconclusive={len(inconclusive)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
