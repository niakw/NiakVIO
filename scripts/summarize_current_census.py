#!/usr/bin/env python3
"""Report this run's observed positives separately from the retained census state."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def observed_ids(report: dict[str, Any], field: str) -> list[str]:
    values = report.get(field + "_providers")
    count = report.get(field + "_provider_count")
    if not isinstance(values, list) or type(count) is not int:
        raise ValueError(f"Missing explicit current-run {field} evidence")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"Invalid current-run {field} identity")
    identities = sorted(set(values))
    if len(identities) != len(values) or len(identities) != count:
        raise ValueError(f"Current-run {field} count/identity mismatch")
    return identities


def summarize(report: dict[str, Any], state: dict[str, Any], *, run_id: int, sha: str) -> dict[str, Any]:
    if str(state.get("runId")) != str(run_id) or state.get("triggerSha") != sha:
        raise ValueError("Current census state run/SHA mismatch")
    rows = [row for row in state.get("providers") or [] if isinstance(row, dict)]
    count = len(rows)
    full = sorted(str(row["provider"]) for row in rows if row.get("status") == "FULL OK")
    partial = sorted(str(row["provider"]) for row in rows if row.get("status") == "PARTIAL OK")
    operational = sorted(set(full + partial))
    verified = observed_ids(report, "verified")
    accepted = observed_ids(report, "accepted_playable")
    tested = report.get("provider_count")
    if type(tested) is not int or tested < max(len(verified), len(accepted)):
        raise ValueError("Current-run evidence exceeds tested provider count")
    without_current_proof = sorted(set(operational) - set(verified))
    carried = sorted(str(row["provider"]) for row in rows
                     if row.get("status") in {"FULL OK", "PARTIAL OK"} and row.get("testedThisRun") is not True)
    target = math.ceil(count * 0.75)
    return {
        "schemaVersion": 3,
        "runId": run_id,
        "triggerSha": sha,
        "scope": report.get("resolved_scope") or report.get("requested_scope") or "unknown",
        "providerCount": count,
        "testedProviderCount": tested,
        "operationalOkCount": len(operational),
        "operationalOkProviders": operational,
        "fullOkCount": len(full),
        "fullOkProviders": full,
        "partialOkCount": len(partial),
        "partialOkProviders": partial,
        "carriedOperationalProviderCount": len(carried),
        "carriedOperationalProviders": carried,
        "operationalWithoutCurrentVerifiedCount": len(without_current_proof),
        "operationalWithoutCurrentVerifiedProviders": without_current_proof,
        "statusCounts": state.get("counts") or {},
        "brainQueue": state.get("brainQueue") or [],
        "verifiedProviderCount": len(verified),
        "verifiedProviders": verified,
        "acceptedPlayableProviderCount": len(accepted),
        "acceptedPlayableProviders": accepted,
        "wrongContentProviderCount": int(report.get("wrong_content_provider_count") or 0),
        "wrongContentProviders": report.get("wrong_content_providers") or [],
        "acceptanceTarget": target,
        # Preserve the existing aggregate progress metric; it is not an
        # exact-run playback or publication decision.
        "acceptanceBasis": "aggregate-operational-state-including-carried-evidence",
        "acceptanceReached": len(operational) >= target,
        "debugStageCounts": report.get("debug_stage_counts") or {},
        "debugStageProviders": report.get("debug_stage_providers") or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("report", "state", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    result = summarize(
        json.loads(args.report.read_text(encoding="utf-8")),
        json.loads(args.state.read_text(encoding="utf-8")),
        run_id=args.run_id, sha=args.sha,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FIELD_CURRENT_BYTES_PROVIDER_CENSUS " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
