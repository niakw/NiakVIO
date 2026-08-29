#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from select_brain_learning_target import diagnostic, norm, provider_rows


def load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    return value


def manifest_ids(manifest: dict[str, Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = norm(row.get("id") or row.get("name"))
        if not provider_id or provider_id in seen:
            continue
        seen.add(provider_id)
        out.append(provider_id)
    return out


def build_queue(
    manifest: dict[str, Any],
    health: dict[str, Any],
    previous: dict[str, Any],
    explicit: str = "",
) -> dict[str, Any]:
    ids = manifest_ids(manifest)
    if not ids:
        return {
            "schemaVersion": 1,
            "providers": [],
            "pendingProviders": [],
            "coreIsAuthoritative": False,
            "reason": "empty_manifest",
        }

    health_by_id: dict[str, dict[str, Any]] = {}
    for row in provider_rows(health):
        provider_id = norm(row.get("id") or row.get("canonical_id"))
        if provider_id:
            health_by_id[provider_id] = row

    if explicit:
        provider_id = norm(explicit)
        if provider_id not in set(ids):
            raise ValueError(f"unknown Learning provider: {explicit}")
        ids = [provider_id]

    info: dict[str, dict[str, Any]] = {}
    for provider_id in ids:
        row = health_by_id.get(provider_id)
        if row is None:
            info[provider_id] = {
                "provider": provider_id,
                "status": "not_observed_by_core",
                "score": 50,
                "needs_route_search": False,
                "core_is_authoritative": False,
            }
        else:
            entry = diagnostic(row)
            entry["core_is_authoritative"] = False
            info[provider_id] = entry

    scheduler = previous.get("learningScheduler") if isinstance(previous.get("learningScheduler"), dict) else {}
    previous_pending = [
        norm(value)
        for value in scheduler.get("pendingProviders") or []
        if norm(value) in info
    ]
    previous_pending = list(dict.fromkeys(previous_pending))

    if explicit:
        ordered_ids = ids
        cycle_reason = "manual_provider"
    elif previous_pending:
        tail = [provider_id for provider_id in ids if provider_id not in set(previous_pending)]
        anomalies = sorted(
            [provider_id for provider_id in tail if info[provider_id].get("status") not in {"healthy", "reachable"}],
            key=lambda provider_id: (-int(info[provider_id].get("score") or 0), provider_id),
        )
        healthy = sorted(
            [provider_id for provider_id in tail if provider_id not in set(anomalies)],
            key=lambda provider_id: provider_id,
        )
        ordered_ids = [*previous_pending, *anomalies, *healthy]
        cycle_reason = "resume_previous_pending_then_anomalies"
    else:
        anomalies = sorted(
            [provider_id for provider_id in ids if info[provider_id].get("status") not in {"healthy", "reachable"}],
            key=lambda provider_id: (-int(info[provider_id].get("score") or 0), provider_id),
        )
        healthy = sorted(
            [provider_id for provider_id in ids if provider_id not in set(anomalies)],
            key=lambda provider_id: provider_id,
        )
        ordered_ids = [*anomalies, *healthy]
        cycle_reason = "new_cycle_anomalies_then_hidden_failure_exploration"

    providers = []
    for index, provider_id in enumerate(ordered_ids):
        row = dict(info[provider_id])
        row.update(
            {
                "provider": provider_id,
                "queueIndex": index,
                "priority": "core_anomaly" if row.get("status") not in {"healthy", "reachable"} else "hidden_failure_exploration",
                "coreHypothesisOnly": True,
            }
        )
        providers.append(row)

    return {
        "schemaVersion": 1,
        "coreIsAuthoritative": False,
        "resumeAcrossDays": True,
        "reason": cycle_reason,
        "providerCount": len(providers),
        "providers": providers,
        "pendingProviders": [row["provider"] for row in providers],
        "previousPendingCount": len(previous_pending),
        "completedProviders": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    parser.add_argument("--health", type=Path, default=Path("health-report.json"))
    parser.add_argument("--state", type=Path, default=Path("brain-learning-input/previous.json"))
    parser.add_argument("--provider", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = load(args.manifest, {})
    health = load(args.health, {})
    previous = load(args.state, {})
    result = build_queue(manifest, health, previous, args.provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_QUEUE "
        f"providers={result['providerCount']} previous_pending={result['previousPendingCount']} "
        f"reason={result['reason']} core_authoritative=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
