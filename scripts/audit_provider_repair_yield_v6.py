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


def identity_safe(row: dict[str, Any]) -> bool:
    return int(row.get("contradictions") or 0) == 0 and str(row.get("status") or "") != "wrong_content"


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
    raw = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("raw") or 0) > 0 for v in vals))
    playable = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("playable") or 0) > 0 for v in vals))
    accepted_playable = sorted(
        pid for pid, vals in by_provider.items()
        if any(int(v.get("playable") or 0) > 0 and identity_safe(v) for v in vals)
    )
    verified = sorted(pid for pid, vals in by_provider.items() if any(int(v.get("verified") or 0) > 0 and identity_safe(v) for v in vals))
    wrong_content = sorted(pid for pid, vals in by_provider.items() if any(not identity_safe(v) for v in vals))

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
            if not fixture:
                fixture = cid(task.get("fixture"))
            if fixture != REPRESENTATIVE_SLUG.get(media):
                continue
            if int(task.get("streamCount") or 0) > 0 or int(task.get("rawStreamCount") or 0) > 0:
                upstream_positive.add((provider_id, media))

    # A reconstructed stream is not a preserved upstream positive if the identity
    # verifier says it contradicts the requested work/episode. Raw HTTP/player
    # success remains visible in diagnostics, but can never satisfy acceptance.
    reconstructed_positive = {
        (cid(row.get("provider_id")), cid(row.get("semantic_type")))
        for row in rows
        if int(row.get("raw") or 0) > 0 and identity_safe(row)
    }
    contradicted_positive = {
        (cid(row.get("provider_id")), cid(row.get("semantic_type")))
        for row in rows
        if int(row.get("raw") or 0) > 0 and not identity_safe(row)
    }
    lost = sorted(upstream_positive - reconstructed_positive)
    recovered = sorted(upstream_positive & reconstructed_positive)
    contradicted = sorted(upstream_positive & contradicted_positive)

    statuses = Counter(str(row.get("status") or "unknown") for row in rows)
    stages = Counter(str(row.get("debug_stage") or "unknown") for row in rows)
    report = {
        "schemaVersion": 7,
        "targetedProviderCount": len(targeted),
        "targetedProviders": sorted(targeted),
        "skippedAlreadyGreenProviders": sorted(skipped),
        "taskCount": len(tasks),
        "rawProviderCount": len(raw),
        "playableProviderCount": len(playable),
        "acceptedPlayableProviderCount": len(accepted_playable),
        "verifiedProviderCount": len(verified),
        "wrongContentProviderCount": len(wrong_content),
        "rawProviders": raw,
        "playableProviders": playable,
        "acceptedPlayableProviders": accepted_playable,
        "verifiedProviders": verified,
        "wrongContentProviders": wrong_content,
        "upstreamPositiveRepresentativePairs": [list(v) for v in sorted(upstream_positive)],
        "preservedUpstreamPositivePairs": [list(v) for v in recovered],
        "contradictedUpstreamPositivePairs": [list(v) for v in contradicted],
        "lostUpstreamPositivePairs": [list(v) for v in lost],
        "statusCounts": dict(sorted(statuses.items())),
        "debugStageCounts": dict(sorted(stages.items())),
        "rows": sorted(rows, key=lambda row: (cid(row.get("provider_id")), cid(row.get("semantic_type")))),
    }
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_REPAIR_YIELD_V7 "
        f"targeted={len(targeted)} tasks={len(tasks)} raw={len(raw)} playable={len(playable)} "
        f"accepted_playable={len(accepted_playable)} verified={len(verified)} wrong_content={len(wrong_content)} "
        f"upstream_positive={len(upstream_positive)} preserved={len(recovered)} "
        f"contradicted={len(contradicted)} lost={len(lost)}"
    )
    if playable:
        print("PROVIDER_REPAIR_YIELD_V7_PLAYABLE providers=" + ",".join(playable))
    if accepted_playable:
        print("PROVIDER_REPAIR_YIELD_V7_ACCEPTED_PLAYABLE providers=" + ",".join(accepted_playable))
    if contradicted:
        print("PROVIDER_REPAIR_YIELD_V7_CONTRADICTED pairs=" + ",".join(f"{p}:{m}" for p, m in contradicted))
    if lost:
        print("PROVIDER_REPAIR_YIELD_V7_LOST pairs=" + ",".join(f"{p}:{m}" for p, m in lost))
    if args.require_upstream_positive_preserved and lost:
        raise SystemExit(3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
