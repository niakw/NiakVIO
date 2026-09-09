#!/usr/bin/env python3
"""Plan deterministic parallel Provider sweeps without conflating tested and green.

Selection authority:
- manifest.json defines the complete 96-provider catalogue;
- provider-repair-skip.json contains only already accepted green providers;
- provider-sweep-recent-v1.json prevents immediate duplicate automatic work but
  does not declare anything healthy;
- provider-repair-learn-handoff-v1.json marks residual repair work owned by LEARN;
- provider-fast-trigger.json may provide explicitProviders for one-off repair
  revalidation and regressionGuardProviders for deliberate green revalidation.

Explicit repair requests still respect the accepted-green skip set. Regression
guards intentionally bypass it: their purpose is to prove that known-good
providers have not regressed after shared runtime changes.

The planner partitions selected providers into bounded batches. It performs no
network work and never changes provider state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
SKIP = ROOT / "automation" / "provider-repair-skip.json"
RECENT = ROOT / "automation" / "provider-sweep-recent-v1.json"
TRIGGER = ROOT / "automation" / "provider-fast-trigger.json"
LEARN_HANDOFF = ROOT / "automation" / "provider-repair-learn-handoff-v1.json"
EXPECTED = 96


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        provider = cid(raw)
        if provider and provider not in seen:
            out.append(provider)
            seen.add(provider)
    return out


def catalogue() -> list[str]:
    manifest = load(MANIFEST)
    ids = [cid(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]
    if len(ids) != EXPECTED or len(set(ids)) != EXPECTED:
        raise SystemExit(f"provider catalogue must be exactly {EXPECTED} unique ids, got {len(ids)}/{len(set(ids))}")
    return ids


def plan(limit: int, batch_size: int) -> dict[str, Any]:
    ids = catalogue()
    skip_cfg = load(SKIP)
    recent_cfg = load(RECENT)
    trigger_cfg = load(TRIGGER) if TRIGGER.exists() else {}
    handoff_cfg = load(LEARN_HANDOFF) if LEARN_HANDOFF.exists() else {}

    green = {cid(value) for value in (skip_cfg.get("providers") or {}).keys() if cid(value)}
    recent = {cid(value) for value in recent_cfg.get("recentlySwept") or [] if cid(value)}
    learn_owned = {cid(value) for value in (handoff_cfg.get("providers") or {}).keys() if cid(value)}
    explicit = unique(list(trigger_cfg.get("explicitProviders") or []))
    guards = unique(list(trigger_cfg.get("regressionGuardProviders") or []))

    unknown = [provider for provider in unique([*explicit, *guards]) if provider not in ids]
    if unknown:
        raise SystemExit("unknown explicit/guard providers: " + ",".join(unknown))

    if explicit or guards:
        selected = unique([
            *[provider for provider in explicit if provider not in green],
            *guards,
        ])
        selection_mode = "explicit-revalidation-with-regression-guards" if guards else "explicit-revalidation"
        eligible = [provider for provider in ids if provider not in green and provider not in learn_owned]
    else:
        eligible = [
            provider for provider in ids
            if provider not in green
            and provider not in recent
            and provider not in learn_owned
        ]
        selected = eligible[:limit]
        selection_mode = "automatic-next-wave"

    batches = [selected[index:index + batch_size] for index in range(0, len(selected), batch_size)]
    matrix = {
        "include": [
            {
                "batch": f"wave-{index + 1:02d}",
                "providers": " ".join(batch),
                "providerCount": len(batch),
            }
            for index, batch in enumerate(batches)
            if batch
        ]
    }
    return {
        "schemaVersion": 3,
        "selectionMode": selection_mode,
        "catalogueCount": len(ids),
        "greenSkippedCount": len(green),
        "recentSkippedCount": len(recent),
        "learnHandoffSkippedCount": len(learn_owned),
        "learnHandoffProviders": sorted(learn_owned),
        "regressionGuardProviders": guards,
        "eligibleCount": len(eligible),
        "selectedCount": len(selected),
        "batchSize": batch_size,
        "batchCount": len(matrix["include"]),
        "selectedProviders": selected,
        "matrix": matrix,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--matrix-only", action="store_true")
    args = parser.parse_args()
    limit = max(1, min(int(args.limit), EXPECTED))
    batch_size = max(1, min(int(args.batch_size), 12))
    value = plan(limit, batch_size)
    if args.matrix_only:
        print(json.dumps(value["matrix"], ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if value["selectedCount"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
