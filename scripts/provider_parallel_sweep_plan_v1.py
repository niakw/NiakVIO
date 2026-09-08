#!/usr/bin/env python3
"""Plan a deterministic parallel Provider sweep without conflating tested and green.

Selection authority:
- manifest.json defines the complete 96-provider catalogue;
- provider-repair-skip.json contains only already accepted green providers;
- provider-sweep-recent-v1.json prevents immediate duplicate work but does not
  declare anything healthy.

The planner selects the next N providers in manifest order and partitions them
into bounded batches. It performs no network work and never changes provider
state.
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
EXPECTED = 96


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


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
    green = {cid(value) for value in (skip_cfg.get("providers") or {}).keys() if cid(value)}
    recent = {cid(value) for value in recent_cfg.get("recentlySwept") or [] if cid(value)}
    eligible = [provider for provider in ids if provider not in green and provider not in recent]
    selected = eligible[:limit]
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
        "schemaVersion": 1,
        "catalogueCount": len(ids),
        "greenSkippedCount": len(green),
        "recentSkippedCount": len(recent),
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
