#!/usr/bin/env python3
"""Select an exact, current continuation cohort from a previous Repair report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def unique(values: object) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values if isinstance(values, list) else []:
        value = canon(raw)
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def select_resume_targets(status: dict[str, Any], report: dict[str, Any]) -> tuple[list[str], str]:
    if report.get("resumeRecommended") is not True:
        return [], "report-not-resumable"
    last = status.get("lastRepairAttempt")
    if not isinstance(last, dict) or last.get("timeBudgetExhausted") is not True:
        return [], "status-not-budget-exhausted"
    report_source = str(report.get("sourceCensusRunId") or "").strip()
    status_source = str(last.get("sourceCensusRunId") or "").strip()
    if not report_source or report_source != status_source:
        return [], "source-census-mismatch"

    selected = unique(report.get("selectedProviders"))
    status_selected = unique(last.get("selectedProviders"))
    if not selected or set(selected) != set(status_selected):
        return [], "selected-cohort-mismatch"

    processed = set(unique(report.get("processedProviders")))
    unvisited = unique(report.get("unvisitedProviders"))
    if not unvisited:
        return [], "no-unvisited-provider"
    if any(provider not in selected or provider in processed for provider in unvisited):
        return [], "invalid-unvisited-partition"

    repair_queue = set(unique(status.get("repairQueue")))
    current = [provider for provider in unvisited if provider in repair_queue]
    if not current:
        return [], "unvisited-resolved"
    return current, "resume-current-unvisited"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--format", choices=("lines", "json"), default="lines")
    args = parser.parse_args()
    status = json.loads(args.status.read_text(encoding="utf-8"))
    report = json.loads(args.report.read_text(encoding="utf-8"))
    targets, reason = select_resume_targets(status, report)
    if args.format == "json":
        print(json.dumps({"providers": targets, "providerCount": len(targets), "reason": reason}, sort_keys=True))
    else:
        for provider in targets:
            print(provider)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
