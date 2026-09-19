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
    targeted = [
        provider
        for provider in (safe_provider(x) for x in summary.get("targetedProviders") or [])
        if provider
    ]
    verified = {
        provider
        for provider in (safe_provider(x) for x in summary.get("verifiedProviders") or [])
        if provider
    }
    lost = lost_lanes(summary)
    attempts = max(0, min(int(summary.get("maxAttemptsPerTask") or 0), 20))

    for provider in targeted:
        provider_lost_lanes = lost.get(provider, [])
        # Provider-level verification is intentionally weaker than lane-level
        # preservation. If movie is verified but TV lost an upstream-positive
        # lane, the TV debt remains LEARN-owned instead of being erased.
        if provider in verified and not provider_lost_lanes:
            providers.pop(provider, None)
            continue
        prior = providers.get(provider) if isinstance(providers.get(provider), dict) else {}
        observations = max(0, min(int(prior.get("repairObservations") or 0) + 1, 9999))
        providers[provider] = {
            "owner": "LEARN",
            "status": "pending",
            "reason": "lost-upstream-positive" if provider_lost_lanes else "target-not-verified",
            "mediaTypes": provider_lost_lanes,
            "lastRepairRunId": str(run_id or prior.get("lastRepairRunId") or "")[:32],
            "lastRepairAttemptsPerTask": attempts,
            "repairObservations": observations,
            "publicationAllowed": False,
        }

    return {
        "schemaVersion": 1,
        "policy": "Residual targeted repair failures are LEARN-owned per semantic lane; automatic route/data repair skips them until LEARN or a deliberate explicit regression/priority run resolves them.",
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
