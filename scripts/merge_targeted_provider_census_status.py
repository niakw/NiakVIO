#!/usr/bin/env python3
"""Overlay a targeted active-provider census onto the current fleet state.

A targeted census owns evidence only for explicitly measured provider rows. It
must never replace fleet-wide freshness/provenance for providers it did not
execute. The caller reapplies current transport/authority evidence afterwards so
derived queues/counts are rebuilt from the merged rows.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def parse_providers(value: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in str(value or "").split(","):
        provider = canon(raw)
        if provider and provider not in seen:
            seen.add(provider)
            out.append(provider)
    if not out:
        raise ValueError("targeted census merge requires at least one provider")
    return out


def merge(base: dict[str, Any], candidate: dict[str, Any], providers: list[str]) -> dict[str, Any]:
    base_run = str(base.get("runId") or "").strip()
    base_sha = str(base.get("triggerSha") or "").strip()
    candidate_run = str(candidate.get("runId") or "").strip()
    candidate_sha = str(candidate.get("triggerSha") or "").strip()
    if not base_run or not base_sha:
        raise ValueError("current fleet census lacks canonical provenance")
    if not candidate_run or not candidate_sha:
        raise ValueError("targeted census candidate lacks provenance")

    wanted = [canon(value) for value in providers if canon(value)]
    if not wanted:
        raise ValueError("targeted census merge has empty provider set")

    base_rows = [copy.deepcopy(row) for row in base.get("providers") or [] if isinstance(row, dict)]
    candidate_rows = {
        canon(row.get("provider")): row
        for row in candidate.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }
    base_index = {
        canon(row.get("provider")): index
        for index, row in enumerate(base_rows)
        if canon(row.get("provider"))
    }
    missing_base = sorted(set(wanted) - set(base_index))
    missing_candidate = sorted(set(wanted) - set(candidate_rows))
    if missing_base or missing_candidate:
        raise ValueError(
            "targeted census provider mismatch "
            f"missing_base={missing_base} missing_candidate={missing_candidate}"
        )

    for provider in wanted:
        row = copy.deepcopy(candidate_rows[provider])
        row["targetedCensusRunId"] = candidate_run
        row["targetedCensusSha"] = candidate_sha
        base_rows[base_index[provider]] = row

    out = copy.deepcopy(base)
    out["providers"] = base_rows
    out["targetedCensusOverlay"] = {
        "schemaVersion": 1,
        "runId": candidate_run,
        "triggerSha": candidate_sha,
        "providers": wanted,
        "baseRunId": base_run,
        "baseTriggerSha": base_sha,
        "fleetAuthorityPreserved": True,
        "providerRowAuthorityOnly": True,
    }
    out["runId"] = base_run
    out["triggerSha"] = base_sha
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--providers", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    providers = parse_providers(args.providers)
    merged = merge(load(args.base), load(args.candidate), providers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overlay = merged["targetedCensusOverlay"]
    print(
        "FIELD_TARGETED_CENSUS_STATE_MERGE "
        f"base_run={overlay['baseRunId']} target_run={overlay['runId']} "
        f"providers={','.join(overlay['providers'])} fleet_authority_preserved=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
