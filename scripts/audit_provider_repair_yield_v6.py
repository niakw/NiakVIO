#!/usr/bin/env python3
"""Target-only post-reconstruction yield audit for portfolio repair v6."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import audit_provider_quick_yield as base

ROOT = Path(__file__).resolve().parents[1]
REPRESENTATIVE_SLUG = {
    "movie": "interstellar",
    "tv": "breaking-bad-s01e01",
    "anime": "jujutsu-kaisen-s01e01",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--skip-file", type=Path, default=Path("automation/provider-repair-skip.json"))
    parser.add_argument("--output", type=Path, default=Path("automation/provider-repair-yield-v6.json"))
    parser.add_argument("--require-upstream-positive-preserved", action="store_true")
    args = parser.parse_args()

    recovery = load(ROOT / args.recovery)
    skip_cfg = load(ROOT / args.skip_file)
    skipped = {cid(value) for value in (skip_cfg.get("providers") or {}).keys()}
    targeted = {
        cid(row.get("providerId"))
        for row in recovery.get("providers") or []
        if isinstance(row, dict) and cid(row.get("providerId")) and cid(row.get("providerId")) not in skipped
    }

    all_tasks, _ = base.build_tasks()
    tasks = [task for task in all_tasks if cid(task.get("provider_id")) in targeted]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=base.WORKERS) as pool:
        futures = [pool.submit(base.run, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())

    by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_provider[cid(row.get("provider_id"))].append(row)
    playable = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("playable") or 0) > 0 for v in vals))
    verified = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("verified") or 0) > 0 for v in vals))
    raw = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("raw") or 0) > 0 for v in vals))

    upstream_positive: set[tuple[str, str]] = set()
    for provider in recovery.get("providers") or []:
        if not isinstance(provider, dict):
            continue
        provider_id = cid(provider.get("providerId"))
        if provider_id not in targeted:
            continue
        for task in provider.get("tasks") or []:
            if not isinstance(task, dict):
                continue
            media = cid(task.get("semanticType"))
            fixture = cid((task.get("fixture") or {}).get("slug") if isinstance(task.get("fixture"), dict) else task.get("fixture"))
            # Current recovery report stores fixture as slug text in task rows.
            if not fixture:
                fixture = cid(task.get("fixture"))
            if fixture != REPRESENTATIVE_SLUG.get(media):
                continue
            if int(task.get("streamCount") or 0) > 0 or int(task.get("rawStreamCount") or 0) > 0:
                upstream_positive.add((provider_id, media))

    reconstructed_positive = {
        (cid(row.get("provider_id")), cid(row.get("semantic_type")))
        for row in rows if int(row.get("raw") or 0) > 0
    }
    lost = sorted(upstream_positive - reconstructed_positive)
    recovered = sorted(upstream_positive & reconstructed_positive)

    statuses = Counter(str(row.get("status") or "unknown") for row in rows)
    stages = Counter(str(row.get("debug_stage") or "unknown") for row in rows)
    report = {
        "schemaVersion": 6,
        "targetedProviderCount": len(targeted),
        "targetedProviders": sorted(targeted),
        "skippedAlreadyGreenProviders": sorted(skipped),
        "taskCount": len(tasks),
        "rawProviderCount": len(raw),
        "playableProviderCount": len(playable),
        "verifiedProviderCount": len(verified),
        "rawProviders": raw,
        "playableProviders": playable,
        "verifiedProviders": verified,
        "upstreamPositiveRepresentativePairs": [list(v) for v in sorted(upstream_positive)],
        "preservedUpstreamPositivePairs": [list(v) for v in recovered],
        "lostUpstreamPositivePairs": [list(v) for v in lost],
        "statusCounts": dict(sorted(statuses.items())),
        "debugStageCounts": dict(sorted(stages.items())),
        "rows": sorted(rows, key=lambda row: (cid(row.get("provider_id")), cid(row.get("semantic_type")))),
    }
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_REPAIR_YIELD_V6 "
        f"targeted={len(targeted)} tasks={len(tasks)} raw={len(raw)} playable={len(playable)} verified={len(verified)} "
        f"upstream_positive={len(upstream_positive)} preserved={len(recovered)} lost={len(lost)}"
    )
    if playable:
        print("PROVIDER_REPAIR_YIELD_V6_PLAYABLE providers=" + ",".join(playable))
    if lost:
        print("PROVIDER_REPAIR_YIELD_V6_LOST pairs=" + ",".join(f"{p}:{m}" for p, m in lost))
    if args.require_upstream_positive_preserved and lost:
        raise SystemExit(3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
