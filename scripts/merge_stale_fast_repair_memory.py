#!/usr/bin/env python3
"""Bridge executed negative Fast Brain experiments across safe stale SHA retries.

The previous run's GitHub artifact is a *prior*, never provider publication
authority. Workflow verifies same repository, run type, ancestry and identical
executable/provider bytes before invoking this script. Only negative,
execution-observed profiles are imported. No provider sources are touched.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

NEGATIVE = {"rejected", "profile_unavailable", "failed", "no_progress"}
MAX_ROWS = 1000


def key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("providerId") or "").strip().casefold().replace("_", "-"),
        str(row.get("signature") or ""),
        str(row.get("profile") or ""),
        str(row.get("positiveProgramFingerprint") or "").casefold(),
        str(row.get("strategyImplementationFingerprint") or "").casefold(),
        str(row.get("llmAdvisorExperimentFingerprint") or "").casefold(),
        str(max(0, int(row.get("experimentVariant") or 0))),
        str(max(1, int(row.get("experimentGeneration") or 1))),
    )


def merge_memory(
    baseline: dict[str, Any],
    imported: dict[str, Any],
    eligible_providers: set[str],
) -> tuple[dict[str, Any], dict[str, int]]:
    if baseline.get("schemaVersion") != 1 or imported.get("schemaVersion") != 1:
        raise ValueError("incompatible Fast Brain memory schema")
    original = baseline.get("entries")
    candidates = imported.get("entries")
    if not isinstance(original, list) or not isinstance(candidates, list):
        raise ValueError("Fast Brain memory entries must be lists")
    if len(original) > MAX_ROWS or len(candidates) > MAX_ROWS:
        raise ValueError("Fast Brain memory exceeds bounded schema")
    rows: dict[tuple[str, ...], dict[str, Any]] = {}
    for item in original:
        if isinstance(item, dict):
            identity = key(item)
            if all(identity[:3]):
                rows[identity] = copy.deepcopy(item)
    inspected = accepted = inserted = 0
    for item in candidates:
        if not isinstance(item, dict):
            continue
        inspected += 1
        identity = key(item)
        if (
            not all(identity[:3])
            or identity[0] not in eligible_providers
            or item.get("executionObserved") is not True
            or str(item.get("lastOutcome") or "") not in NEGATIVE
        ):
            continue
        before = rows.get(identity)
        if before is None:
            rows[identity] = copy.deepcopy(item)
            inserted += 1
        else:
            # Never override a current positive outcome with a stale negative.
            merged = copy.deepcopy(before)
            for counter in ("failures", "consecutiveFailures", "successes", "progresses"):
                merged[counter] = max(
                    0, int(before.get(counter) or 0), int(item.get(counter) or 0)
                )
            if str(before.get("lastOutcome") or "") in NEGATIVE:
                if int(item.get("failures") or 0) >= int(before.get("failures") or 0):
                    merged["lastOutcome"] = item.get("lastOutcome")
                    merged["lastReason"] = item.get("lastReason")
                    merged["executionObserved"] = True
            rows[identity] = merged
        accepted += 1
    out = {
        "schemaVersion": 1,
        "entries": sorted(
            rows.values(),
            key=lambda item: (
                -int(item.get("consecutiveFailures") or 0),
                -int(item.get("failures") or 0),
                str(item.get("providerId") or ""),
                str(item.get("signature") or ""),
                str(item.get("profile") or ""),
                int(item.get("experimentVariant") or 0),
                int(item.get("experimentGeneration") or 1),
            ),
        )[:MAX_ROWS],
    }
    return out, {"inspected": inspected, "accepted": accepted, "inserted": inserted}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--prior", type=Path, required=True)
    ap.add_argument("--census", type=Path, required=True)
    args = ap.parse_args()
    current = json.loads(args.current.read_text(encoding="utf-8"))
    prior = json.loads(args.prior.read_text(encoding="utf-8"))
    census = json.loads(args.census.read_text(encoding="utf-8"))
    queue = {
        str(p).strip().casefold().replace("_", "-")
        for p in (census.get("repairQueue") or [])
    }
    if not queue:
        raise ValueError("cannot replay stale experience without current repairQueue")
    merged, report = merge_memory(current, prior, queue)
    args.current.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_BRAIN_FAST_STALE_NEGATIVE_PRIORS "
        f"inspected={report['inspected']} accepted={report['accepted']} "
        f"inserted={report['inserted']} rows={len(merged['entries'])} "
        "publicationAuthority=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
