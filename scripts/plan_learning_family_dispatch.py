#!/usr/bin/env python3
"""Plan bounded parallel Brain Learning cohorts from already-eligible providers.

This is a scheduling-only layer. provider_learning_dispatch_gate.py remains the
causal authority deciding which providers have a genuinely new strategy. This
planner chooses a bounded cohort per current repair family so independent
families can run in separate Learning workflows. The strongest/least-recent
oracle is first; siblings follow in the same workflow and consume phase memory.

It never grants mutation, proof, publication, or success authority.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def _timestamp_rank(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0.0, parsed.timestamp())


def learning_recency(memory: dict[str, Any]) -> tuple[dict[str, float], dict[str, str]]:
    latest_epoch: dict[str, float] = {}
    latest_text: dict[str, str] = {}
    experiment = memory.get("experimentMemory")
    if isinstance(experiment, dict):
        entries = experiment.get("entries") or []
    else:
        entries = memory.get("entries") or []
    for row in entries:
        if not isinstance(row, dict):
            continue
        provider = canon(row.get("providerId"))
        if not provider:
            continue
        raw = str(row.get("lastSeenAt") or "").strip()
        rank = _timestamp_rank(raw)
        if rank >= latest_epoch.get(provider, 0.0):
            latest_epoch[provider] = rank
            if raw:
                latest_text[provider] = raw

    queue = memory.get("learningQueue")
    if isinstance(queue, dict):
        state = queue.get("providerState")
        if isinstance(state, dict):
            for raw_provider, row in state.items():
                provider = canon(raw_provider)
                if not provider or not isinstance(row, dict):
                    continue
                raw = str(row.get("lastAttemptAt") or "").strip()
                rank = _timestamp_rank(raw)
                if rank >= latest_epoch.get(provider, 0.0):
                    latest_epoch[provider] = rank
                    if raw:
                        latest_text[provider] = raw
    return latest_epoch, latest_text


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
    max_family_providers: int = 8,
    learning_memory: dict[str, Any] | None = None,
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

    recent_epoch, recent_text = learning_recency(learning_memory or {})

    def provider_rank(provider: str) -> tuple[float, int, int, str]:
        row = by_provider.get(provider, {})
        return (
            recent_epoch.get(provider, 0.0),
            status_rank(row),
            evidence_rank(row),
            provider,
        )

    candidates: list[dict[str, Any]] = []
    for key, members in families.items():
        ranked = sorted(members, key=provider_rank)
        oracle = ranked[0]
        family_last_epoch = max((recent_epoch.get(member, 0.0) for member in ranked), default=0.0)
        family_last_text = ""
        if family_last_epoch > 0:
            family_last_text = max(
                (
                    recent_text.get(member, "")
                    for member in ranked
                    if recent_epoch.get(member, 0.0) == family_last_epoch
                ),
                default="",
            )
        family_limit = max(1, min(int(max_family_providers), 32))
        cohort_members = ranked[:family_limit]
        candidates.append({
            "familyKey": key,
            "provider": oracle,
            "providerFilter": ",".join(cohort_members),
            "familyProviderCount": len(ranked),
            "cohortProviderCount": len(cohort_members),
            "cohortProviders": cohort_members,
            "scheduledFamilyProviders": cohort_members[1:],
            "deferredFamilyProviders": ranked[family_limit:],
            "providerLastAttemptAt": recent_text.get(oracle, ""),
            "familyLastAttemptAt": family_last_text,
            "familyLastAttemptEpoch": family_last_epoch,
            **family_meta[key],
        })

    candidates.sort(
        key=lambda row: (
            float(row.get("familyLastAttemptEpoch") or 0.0),
            provider_rank(str(row["provider"])),
            str(row["familyKey"]),
        )
    )
    limit = max(1, min(int(max_cohorts), 16))
    cohorts = candidates[:limit]
    selected = {
        str(provider)
        for row in cohorts
        for provider in row.get("cohortProviders") or []
        if str(provider)
    }
    deferred = sorted(set(eligible) - selected)

    return {
        "schemaVersion": 1,
        "sourceCensusRunId": current_run,
        "sourceBatchPlanRunId": plan_run,
        "batchPlanCurrent": plan_current,
        "eligibleProviderCount": len(eligible),
        "familyCount": len(candidates),
        "maxCohorts": limit,
        "maxFamilyProviders": max(1, min(int(max_family_providers), 32)),
        "cohortCount": len(cohorts),
        "cohorts": cohorts,
        "selectionPolicy": "least-recent-family-then-bounded-family-cohort-oracle-first",
        "learningMemoryUsed": bool(learning_memory),
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
    parser.add_argument("--max-family-providers", type=int, default=8)
    parser.add_argument("--learning-memory", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    providers = [value for value in args.providers.split(",") if canon(value)]
    output = plan(
        providers,
        load(args.batch_plan),
        load(args.status),
        max_cohorts=args.max_cohorts,
        max_family_providers=args.max_family_providers,
        learning_memory=(
            load(args.learning_memory)
            if args.learning_memory is not None and args.learning_memory.is_file()
            else {}
        ),
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
        f"selected={len(output['selectedProviders'])} deferred={len(output['deferredProviders'])} "
        f"plan_current={str(output['batchPlanCurrent']).lower()} "
        f"memory_used={str(output['learningMemoryUsed']).lower()} "
        "policy=least-recent-family authority=scheduling-only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
