#!/usr/bin/env python3
"""Plan bounded parallel Brain Learning cohorts from already-eligible providers.

This is a scheduling-only layer. provider_learning_dispatch_gate.py remains the
causal authority deciding which providers have a genuinely new strategy. This
planner only chooses at most one oracle per current repair family so independent
families can run in separate Learning workflows.

It never grants mutation, proof, publication, or success authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def evidence_rank(row: dict[str, Any]) -> int:
    values = [
        str(value or "").split("=", 1)[-1].strip().casefold()
        for value in row.get("evidenceDepth") or []
    ]
    if "chain_reached" in values:
        return 0
    if "lookup_only" in values:
        return 1
    if values and all(value == "none" for value in values):
        return 3
    return 2


def status_rank(row: dict[str, Any]) -> int:
    status = str(row.get("status") or "").strip().upper()
    return {
        "CANDIDATE OK": 0,
        "REGRESSION PROVIDER": 1,
        "CHAIN REACHED": 2,
        "NO PROOF": 3,
        "PROVIDER NETWORK BLOCKED": 4,
    }.get(status, 5)


def plan(
    providers: list[str],
    batch_plan: dict[str, Any],
    status: dict[str, Any],
    *,
    max_cohorts: int = 8,
) -> dict[str, Any]:
    eligible = []
    seen: set[str] = set()
    for value in providers:
        provider = canon(value)
        if provider and provider not in seen:
            eligible.append(provider)
            seen.add(provider)

    by_provider = {
        canon(row.get("provider")): row
        for row in status.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }
    current_run = str(status.get("runId") or "")
    plan_run = str(batch_plan.get("sourceRunId") or "")
    plan_current = bool(current_run and current_run == plan_run)

    group_by_provider: dict[str, dict[str, Any]] = {}
    if plan_current:
        for raw in batch_plan.get("groups") or []:
            if not isinstance(raw, dict):
                continue
            family = {
                "groupId": str(raw.get("groupId") or ""),
                "repairScope": canon(raw.get("repairScope")) or "unknown",
                "capabilityStrategy": canon(raw.get("capabilityStrategy")) or "unknown",
                "runtimeFamilySignature": canon(raw.get("runtimeFamilySignature")) or "unknown",
            }
            for value in raw.get("providers") or []:
                provider = canon(value)
                if provider and provider not in group_by_provider:
                    group_by_provider[provider] = family

    families: dict[str, list[str]] = {}
    family_meta: dict[str, dict[str, Any]] = {}
    for provider in eligible:
        family = group_by_provider.get(provider)
        if not family:
            # A stale/missing family plan has no cross-provider grouping
            # authority. Keep the provider isolated.
            family = {
                "groupId": f"provider-local:{provider}",
                "repairScope": "provider-local",
                "capabilityStrategy": "provider-local",
                "runtimeFamilySignature": "provider-local",
            }
        key = str(family["groupId"] or f"provider-local:{provider}")
        families.setdefault(key, []).append(provider)
        family_meta[key] = family

    def provider_rank(provider: str) -> tuple[int, int, str]:
        row = by_provider.get(provider, {})
        return (status_rank(row), evidence_rank(row), provider)

    candidates: list[dict[str, Any]] = []
    for key, members in families.items():
        ranked = sorted(members, key=provider_rank)
        oracle = ranked[0]
        candidates.append({
            "familyKey": key,
            "provider": oracle,
            "providerFilter": oracle,
            "familyProviderCount": len(ranked),
            "deferredFamilyProviders": ranked[1:],
            **family_meta[key],
        })

    candidates.sort(
        key=lambda row: (
            provider_rank(str(row["provider"])),
            str(row["familyKey"]),
        )
    )
    limit = max(1, min(int(max_cohorts), 16))
    cohorts = candidates[:limit]
    selected = {str(row["provider"]) for row in cohorts}
    deferred = sorted(set(eligible) - selected)

    return {
        "schemaVersion": 1,
        "sourceCensusRunId": current_run,
        "sourceBatchPlanRunId": plan_run,
        "batchPlanCurrent": plan_current,
        "eligibleProviderCount": len(eligible),
        "familyCount": len(candidates),
        "maxCohorts": limit,
        "cohortCount": len(cohorts),
        "cohorts": cohorts,
        "selectedProviders": sorted(selected),
        "deferredProviders": deferred,
        "safety": {
            "causalEligibilityAuthority": "provider_learning_dispatch_gate.py",
            "familyPlannerAuthority": "scheduling-only",
            "providerMutationAuthority": False,
            "publicationAuthority": False,
            "proofAuthority": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers", required=True)
    parser.add_argument("--batch-plan", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--max-cohorts", type=int, default=8)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    providers = [value for value in args.providers.split(",") if canon(value)]
    output = plan(
        providers,
        load(args.batch_plan),
        load(args.status),
        max_cohorts=args.max_cohorts,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_BRAIN_LEARNING_FAMILY_DISPATCH "
        f"eligible={output['eligibleProviderCount']} "
        f"families={output['familyCount']} cohorts={output['cohortCount']} "
        f"deferred={len(output['deferredProviders'])} "
        f"plan_current={str(output['batchPlanCurrent']).lower()} "
        "authority=scheduling-only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
