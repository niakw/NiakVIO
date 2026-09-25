#!/usr/bin/env python3
"""Fast provider-local Brain Repair lane.

This intentionally skips global engine migrations, full-catalogue materialization,
transport/WAF qualification and full Core regression suites. Those belong to
separate validation/retest lanes. The fast lane mutates only provider-local DATA
through the existing Brain orchestrator, then current-byte retests only accepted
compiled candidates.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "automation" / "provider-census-status.json"
BRAIN = ROOT / "automation" / "provider-brain-repair-latest.json"
SUMMARY = ROOT / "automation" / "provider-fast-repair-summary.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str, timeout: int | None = None) -> None:
    print("FIELD_PROVIDER_FAST_REPAIR_CMD " + " ".join(args), flush=True)
    subprocess.run(
        list(args),
        cwd=ROOT,
        env=os.environ.copy(),
        check=True,
        timeout=timeout,
    )


def selected_targets(status: dict[str, Any], requested: set[str]) -> list[str]:
    queue = {cid(value) for value in status.get("repairQueue") or [] if cid(value)}
    if requested:
        missing = sorted(requested - queue)
        if missing:
            raise ValueError(
                "explicit provider is not in current repairQueue: " + ",".join(missing)
            )
        return sorted(requested)
    return sorted(queue)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast provider-local Brain Repair")
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--waves", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=48)
    parser.add_argument("--time-budget-seconds", type=int, default=1200)
    parser.add_argument("--min-start-batch-seconds", type=int, default=120)
    parser.add_argument("--health-concurrency", type=int, default=0)
    parser.add_argument("--max-rounds-per-batch", type=int, default=1)
    args = parser.parse_args()

    if not STATUS.is_file():
        raise SystemExit("provider census status missing")
    status_before = load(STATUS)
    requested = {cid(value) for value in args.provider if cid(value)}
    targets = selected_targets(status_before, requested)
    if not targets:
        payload = {
            "schemaVersion": 1,
            "selectedProviders": [],
            "candidateProviders": [],
            "retestedProviders": [],
            "validatedProviders": [],
            "message": "current repairQueue is empty",
        }
        SUMMARY.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("FIELD_PROVIDER_FAST_REPAIR_EMPTY repair_queue=0", flush=True)
        return 0

    brain_cmd = [
        sys.executable,
        "scripts/run_provider_brain_repair.py",
        "--waves", str(max(1, min(args.waves, 6))),
        "--batch-size", str(max(4, min(args.batch_size, 96))),
        "--time-budget-seconds", str(max(300, min(args.time_budget_seconds, 14400))),
        "--min-start-batch-seconds", str(max(120, min(args.min_start_batch_seconds, args.time_budget_seconds))),
        "--max-rounds-per-batch", str(max(1, min(args.max_rounds_per_batch, 3))),
        "--output", str(BRAIN.relative_to(ROOT)),
    ]
    if args.health_concurrency > 0:
        brain_cmd.extend(["--health-concurrency", str(max(1, min(args.health_concurrency, 8)))])
    for provider in targets:
        brain_cmd.extend(["--provider", provider])
    run(
        *brain_cmd,
        timeout=max(600, int(args.time_budget_seconds) + 300),
    )
    brain = load(BRAIN)
    selected = sorted({cid(value) for value in brain.get("selectedProviders") or [] if cid(value)})
    fixed = {cid(value) for value in brain.get("fixedInLabProviders") or [] if cid(value)}
    compiled = {
        cid(value)
        for value in brain.get("acceptedProgramCompiledProviders") or []
        if cid(value)
    }
    candidates = sorted(fixed | compiled)

    # Only accepted/compiled candidates need an immediate current-byte replay.
    # Unchanged failures remain represented by the census that selected them.
    if candidates:
        retest_cmd = [
            sys.executable,
            "scripts/run_provider_retest.py",
            "--scope", "repair",
        ]
        for provider in candidates:
            retest_cmd.extend(["--provider", provider])
        run(*retest_cmd)
    status_after = load(STATUS)
    by_provider = {
        cid(row.get("provider")): str(row.get("status") or "")
        for row in status_after.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }
    validated = sorted(
        provider
        for provider in candidates
        if by_provider.get(provider) in {"FULL OK", "PARTIAL OK"}
    )
    unresolved = sorted(set(candidates) - set(validated))
    deferred_learning = sorted({
        cid(value)
        for value in brain.get("deferredLearningProviders") or []
        if cid(value)
    })
    remaining_brain = sorted({
        cid(value)
        for value in brain.get("remainingProviders") or []
        if cid(value)
    })
    learn_handoff = sorted((set(deferred_learning) | set(remaining_brain)) - set(validated))
    payload = {
        "schemaVersion": 2,
        "sourceCensusRunId": status_before.get("runId"),
        "repairRunId": str(os.environ.get("GITHUB_RUN_ID") or "local"),
        "selectedProviders": selected,
        "candidateProviders": candidates,
        "retestedProviders": candidates,
        "validatedProviders": validated,
        "unresolvedCandidates": unresolved,
        "brainAcceptedRepairCount": int(brain.get("acceptedRepairCount") or 0),
        "brainFixedInLabProviders": sorted(fixed),
        "brainCompiledProviders": sorted(compiled),
        "brainDeferredLearningProviders": deferred_learning,
        "brainRemainingProviders": remaining_brain,
        "learnHandoffProviders": learn_handoff,
        "brainNoProgressReason": brain.get("noProgressReason"),
        "brainTimeBudgetExhausted": brain.get("timeBudgetExhausted") is True,
        "repairQueueAfter": list(status_after.get("repairQueue") or []),
        "publicationAllowed": bool(candidates) and not unresolved,
        "publicationRule": (
            "provider-local Brain candidate only; publication still requires the workflow "
            "to persist exactly the validated current-byte changes"
        ),
    }
    SUMMARY.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Keep census status authority unchanged when no candidate is validated, but
    # always expose the latest Repair/FORCE attempt so the public dashboard never
    # looks frozen while the Brain is actively working.
    status_after["lastRepairAttempt"] = {
        "runId": payload["repairRunId"],
        "sourceCensusRunId": payload["sourceCensusRunId"],
        "selectedProviders": selected,
        "candidateProviders": candidates,
        "validatedProviders": validated,
        "acceptedRepairCount": payload["brainAcceptedRepairCount"],
        "deferredToLearningSlotProviders": learn_handoff,
        "noProgressReason": payload["brainNoProgressReason"],
        "timeBudgetExhausted": payload["brainTimeBudgetExhausted"],
        "publicationAllowed": payload["publicationAllowed"],
    }
    STATUS.write_text(
        json.dumps(status_after, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    run(
        sys.executable,
        "scripts/render_provider_census_status_from_state.py",
        "--status", str(STATUS.relative_to(ROOT)),
        "--output", "PROVIDER_CENSUS_STATUS.md",
    )
    print(
        "FIELD_PROVIDER_FAST_REPAIR_DONE "
        f"selected={len(selected)} candidates={len(candidates)} "
        f"validated={len(validated)} unresolved_candidates={len(unresolved)} "
        f"remaining={len(payload['brainRemainingProviders'])} "
        f"learn_handoff={len(payload['learnHandoffProviders'])}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
