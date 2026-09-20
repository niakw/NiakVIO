#!/usr/bin/env python3
"""Merge WAF/native-transport diagnostics into an existing provider census.

This is intentionally NOT a census renderer. The Repair census remains authority
for playback/route/candidate/history depth. WAF diagnostics may update only the
transport classification of providers that were already in the harness queue.

That prevents a narrow transport probe from downgrading unrelated FULL/PARTIAL/
CANDIDATE/ROUTE/CHAIN evidence or expanding the provider-code repair queue.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import render_provider_census_status as census


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def merge_transport(
    baseline: dict[str, Any],
    waf: dict[str, Any],
    *,
    evidence_run_id: str = "",
    evidence_sha: str = "",
) -> dict[str, Any]:
    out = copy.deepcopy(baseline)
    providers = out.get("providers")
    if not isinstance(providers, list):
        raise ValueError("baseline census providers must be a list")

    baseline_environment = {
        str(value or "").strip().casefold()
        for value in (baseline.get("environmentQueue") or baseline.get("harnessQueue") or [])
        if str(value or "").strip()
    }
    waf_providers = {
        str(row.get("provider") or "").strip().casefold()
        for row in waf.get("rows") or []
        if isinstance(row, dict) and str(row.get("provider") or "").strip()
    }
    allowed = baseline_environment & waf_providers

    changed: list[str] = []
    for row in providers:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().casefold()
        if provider not in allowed:
            continue
        diagnostic = census.harness_transport_diagnostic(waf, provider)
        status = census.browser_harness_status(waf, provider)
        row["status"] = status
        row["color"] = census.STATUS_META[status][0]
        row["harnessTransportClass"] = diagnostic["classification"]
        row["harnessTransportEvidence"] = list(diagnostic["evidence"])
        row["action"] = census._harness_action(status, diagnostic["classification"])
        row["brainCheckRequired"] = True
        row["repairEligible"] = False
        # WAF transport diagnostics are not provider playback probes.
        row["testedThisRun"] = bool(row.get("testedThisRun", False)) and False
        changed.append(provider)

    # Membership authority is preserved. Transport diagnostics may move a member
    # between HARNESS MISMATCH and HARNESS/ENV BLOCKED, but may not add providers
    # to Repair or remove unrelated evidence.
    out["repairQueue"] = list(baseline.get("repairQueue") or [])
    out["environmentQueue"] = list(baseline.get("environmentQueue") or [])
    out["harnessQueue"] = list(baseline.get("harnessQueue") or out["environmentQueue"])
    out["symptomaticProviders"] = list(baseline.get("symptomaticProviders") or [])
    out["brainQueue"] = list(baseline.get("brainQueue") or out["symptomaticProviders"])

    out["counts"] = dict(sorted(Counter(
        str(row.get("status") or "")
        for row in providers
        if isinstance(row, dict) and str(row.get("status") or "")
    ).items()))
    out["harnessEvidenceRunId"] = str(evidence_run_id or waf.get("runId") or "")
    out["harnessEvidenceSha"] = str(evidence_sha or waf.get("triggerSha") or "")
    out["harnessTransportUpdatedProviders"] = sorted(changed)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--waf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--sha", default="")
    args = ap.parse_args()

    baseline = load(args.status)
    merged = merge_transport(
        baseline,
        load(args.waf),
        evidence_run_id=args.run_id,
        evidence_sha=args.sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_WAF_CENSUS_TRANSPORT_MERGE "
        f"repair_queue={len(merged.get('repairQueue') or [])} "
        f"environment_queue={len(merged.get('environmentQueue') or [])} "
        f"updated={len(merged.get('harnessTransportUpdatedProviders') or [])} "
        f"counts={json.dumps(merged.get('counts') or {}, sort_keys=True)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
