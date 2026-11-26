#!/usr/bin/env python3
"""Persist unresolved targeted Provider repair work as LEARN-owned state.

Only sanitized provider ids, media lanes, run ids and bounded counters are stored.
No routes, URLs, headers, request bodies, source code or secrets are copied from
repair artifacts.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PROVIDER_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
LANES = {"movie", "tv", "anime"}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def safe_provider(value: object) -> str:
    provider = cid(value)
    return provider if PROVIDER_ID.fullmatch(provider) else ""


def load(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return dict(default or {})
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def lost_lanes(summary: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, set[str]] = {}
    for row in summary.get("lostUpstreamPositivePairs") or []:
        if not isinstance(row, list) or len(row) < 2:
            continue
        provider = safe_provider(row[0])
        lane = cid(row[1])
        if provider and lane in LANES:
            out.setdefault(provider, set()).add(lane)
    return {provider: sorted(values) for provider, values in out.items()}


def merge_summary(
    registry: dict[str, Any],
    summary: dict[str, Any],
    *,
    run_id: str = "",
) -> dict[str, Any]:
    providers = registry.get("providers") if isinstance(registry.get("providers"), dict) else {}
    providers = {
        safe_provider(key): value
        for key, value in providers.items()
        if safe_provider(key) and isinstance(value, dict)
    }
    selected_summary = isinstance(summary.get("selectedProviders"), list)
    remat_summary = (
        selected_summary
        and isinstance(summary.get("candidateReplayProvenance"), dict)
        and isinstance(summary.get("statusesAfterRemat"), dict)
    )
    fast_summary = selected_summary and not remat_summary
    targeted = [
        provider
        for provider in (
            safe_provider(x)
            for x in (
                summary.get("selectedProviders")
                if selected_summary
                else summary.get("targetedProviders")
            ) or []
        )
        if provider
    ]
    if remat_summary:
        provenance = summary.get("candidateReplayProvenance") or {}
        verified = {
            provider
            for provider in targeted
            if isinstance(provenance.get(provider), dict)
            and provenance[provider].get("currentStrictRetestVerified") is True
        }
        remat_learn = {
            provider
            for provider in targeted
            if isinstance(provenance.get(provider), dict)
            and provenance[provider].get("currentStrictRetestVerified") is False
            and str(provenance[provider].get("nextRequiredAction") or "")
            == "locate_exact_candidate_program_or_reconstruct_via_Brain"
        }
    else:
        provenance = {}
        remat_learn = set()
        verified = {
            provider
            for provider in (
                safe_provider(x)
                for x in (
                    summary.get("validatedProviders")
                    if fast_summary
                    else summary.get("verifiedProviders")
                ) or []
            )
            if provider
        }
    deferred = {
        provider
        for provider in (safe_provider(x) for x in summary.get("brainDeferredLearningProviders") or [])
        if provider
    }
    remaining = {
        provider
        for provider in (safe_provider(x) for x in summary.get("brainRemainingProviders") or [])
        if provider
    }
    explicit_handoff = {
        provider
        for provider in (safe_provider(x) for x in summary.get("learnHandoffProviders") or [])
        if provider
    }
    # Fast Repair schema v2 owns the exact Learning handoff boundary. An empty
    # explicit list is meaningful: unresolved siblings may be intentionally
    # unvisited by the causal-family frontier and must not be reclassified as
    # Learning debt merely because they remain in the Repair queue.
    if fast_summary and "learnHandoffProviders" in summary:
        learn_owned = explicit_handoff
    else:
        learn_owned = deferred | remaining
    lost = lost_lanes(summary)
    attempts = max(0, min(int(summary.get("maxAttemptsPerTask") or 0), 20))

    for provider in targeted:
        if fast_summary and learn_owned and provider not in learn_owned:
            continue
        if remat_summary and provider not in verified and provider not in remat_learn:
            # Remat is diagnostic-only. Without an explicit causal handoff in
            # candidate provenance, preserve the existing owner rather than
            # inventing Learning authority.
            continue
        provider_lost_lanes = lost.get(provider, [])
        # Provider-level verification is intentionally weaker than lane-level
        # preservation. If movie is verified but TV lost an upstream-positive
        # lane, the TV debt remains LEARN-owned instead of being erased.
        if provider in verified and not provider_lost_lanes:
            providers.pop(provider, None)
            continue
        prior = providers.get(provider) if isinstance(providers.get(provider), dict) else {}
        observations = max(0, min(int(prior.get("repairObservations") or 0) + 1, 9999))
        if provider_lost_lanes:
            reason = "lost-upstream-positive"
        elif remat_summary and provider in remat_learn:
            reason = "remat-candidate-unverified"
        elif provider in deferred:
            reason = "brain-strategy-exhausted"
        elif provider in remaining:
            reason = "brain-unresolved"
        else:
            reason = "target-not-verified"
        source_lane = (
            "REMAT_TEST" if remat_summary
            else "FAST_REPAIR" if fast_summary
            else "TARGETED_REPAIR"
        )
        providers[provider] = {
            "owner": "LEARN",
            "status": "pending",
            "reason": reason,
            "mediaTypes": provider_lost_lanes,
            "sourceLane": source_lane,
            "lastRepairRunId": str(run_id or prior.get("lastRepairRunId") or "")[:32],
            "lastRepairAttemptsPerTask": attempts,
            "repairObservations": observations,
            "publicationAllowed": False,
        }

    return {
        "schemaVersion": 1,
        "policy": "Residual targeted repair failures, exhausted Fast Brain strategies, and Remat candidates whose exact executable program is absent are LEARN-owned; automatic repair/remat must not repeat exhausted evidence until LEARN produces a materially new strategy or validated evidence.",
        "providerCount": len(providers),
        "providers": dict(sorted(providers.items())),
        "publicationAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--summary", type=Path, action="append", default=[])
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    registry = load(args.registry, {"schemaVersion": 1, "providers": {}})
    for summary_path in args.summary:
        registry = merge_summary(registry, load(summary_path), run_id=args.run_id)
    write(args.registry, registry)
    print(
        "FIELD_PROVIDER_REPAIR_LEARN_HANDOFF "
        f"providers={registry.get('providerCount', 0)} "
        f"run_id={str(args.run_id)[:32] or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
