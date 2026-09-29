#!/usr/bin/env python3
"""Project fresh targeted transport evidence into census repair eligibility.

This overlay never changes provider playback/route status. It only prevents the
automated provider-mutation queue from re-scheduling providers whose same-census
targeted probe already proves a current provider-origin WAF/challenge boundary.

A later same-census targeted probe that no longer shows the transport blocker
restores transport repair eligibility automatically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "automation/provider-census-status.json"
TARGETED = ROOT / "automation/provider-targeted-regression-recovery-latest.json"

TMDB_HOSTS = {"api.themoviedb.org", "www.themoviedb.org"}
WAF_STAGE = "provider_waf_challenge"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def targeted_blocked(row: dict[str, Any]) -> tuple[bool, list[str]]:
    debug = row.get("debugStages") if isinstance(row.get("debugStages"), dict) else {}
    stages = {
        str(value or "").strip().casefold()
        for value in debug.values()
        if str(value or "").strip()
    }
    playable = [str(x) for x in row.get("playableLanes") or [] if str(x).strip()]
    verified = [str(x) for x in row.get("verifiedLanes") or [] if str(x).strip()]
    if playable or verified:
        return False, []

    network = row.get("network") if isinstance(row.get("network"), dict) else {}
    provider_rows: list[dict[str, Any]] = []
    evidence: list[str] = []
    for lane, values in network.items():
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            host = str(item.get("host") or "").strip().casefold()
            if not host or host in TMDB_HOSTS:
                continue
            provider_rows.append(item)
            status = int(item.get("status") or 0)
            evidence.append(f"{str(lane)[:24]}:{host[:96]}:{status}")

    # Status codes alone are not enough to transfer causal ownership away
    # from provider code. A plain provider_network_http_error on 403 remains in
    # Repair until the probe itself classifies an interactive WAF/challenge (or
    # a stronger browser/residential differential does so elsewhere).
    explicit_waf = WAF_STAGE in stages
    return bool(explicit_waf and provider_rows), evidence[:12]


def merge(status: dict[str, Any], targeted: dict[str, Any]) -> dict[str, Any]:
    census_run = str(status.get("runId") or "").strip()
    targeted_run = str(targeted.get("sourceCensusRunId") or "").strip()
    if not census_run or not targeted_run or census_run != targeted_run:
        raise ValueError(
            f"targeted evidence is not current for census: targeted={targeted_run or '-'} census={census_run or '-'}"
        )

    providers_block = targeted.get("providers")
    if not isinstance(providers_block, dict):
        raise ValueError("targeted evidence providers map is missing")

    rows = status.get("providers")
    if not isinstance(rows, list):
        raise ValueError("census providers list is missing")

    changed: list[str] = []
    blocked: list[str] = []
    for census_row in rows:
        if not isinstance(census_row, dict):
            continue
        provider = canon(census_row.get("provider"))
        if not provider:
            continue
        targeted_row = next(
            (
                value
                for key, value in providers_block.items()
                if canon(key) == provider and isinstance(value, dict)
            ),
            None,
        )
        if targeted_row is None:
            continue

        is_blocked, evidence = targeted_blocked(targeted_row)
        before = (
            census_row.get("transportRepairEligible"),
            census_row.get("repairEligible"),
            census_row.get("targetedTransportClass"),
        )
        census_row["transportRepairEligible"] = not is_blocked
        census_row["targetedTransportClass"] = (
            "provider-waf-challenge-current" if is_blocked else "not-applicable"
        )
        census_row["targetedTransportEvidence"] = evidence if is_blocked else []
        status_ok = census_row.get("statusRepairEligible") is True
        authority_ok = census_row.get("authorityRepairEligible") is not False
        census_row["repairEligible"] = bool(status_ok and authority_ok and not is_blocked)
        if is_blocked:
            census_row["action"] = (
                "current same-census targeted probe proves provider-origin WAF/challenge; "
                "exclude provider mutation until stronger residential/native replay disproves transport ownership"
            )
            blocked.append(provider)
        after = (
            census_row.get("transportRepairEligible"),
            census_row.get("repairEligible"),
            census_row.get("targetedTransportClass"),
        )
        if after != before:
            changed.append(provider)

    status["repairQueue"] = sorted(
        canon(row.get("provider"))
        for row in rows
        if isinstance(row, dict) and row.get("repairEligible") is True and canon(row.get("provider"))
    )
    status["targetedTransportBlockedQueue"] = sorted(set(blocked))
    status["targetedTransportEvidenceRunId"] = str(
        targeted.get("sourceVerdictRunId") or targeted.get("runId") or ""
    )
    status["targetedTransportSourceCensusRunId"] = targeted_run
    status["targetedTransportUpdatedProviders"] = sorted(set(changed))
    return status


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", type=Path, default=STATUS)
    ap.add_argument("--targeted", type=Path, default=TARGETED)
    ap.add_argument("--output", type=Path, default=STATUS)
    args = ap.parse_args()

    merged = merge(load(args.status), load(args.targeted))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "FIELD_TARGETED_CENSUS_TRANSPORT_MERGE "
        f"repair_queue={len(merged.get('repairQueue') or [])} "
        f"blocked={len(merged.get('targetedTransportBlockedQueue') or [])} "
        f"updated={len(merged.get('targetedTransportUpdatedProviders') or [])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
