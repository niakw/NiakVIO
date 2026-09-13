#!/usr/bin/env python3
"""Run targeted Provider repair as a multi-provider batch with fail-closed quarantine.

The underlying fast repair gate is intentionally strict: any enabled upstream-positive
lane that is lost makes the candidate fail. Historically this made one flaky provider
discard every valid mutation in the same batch. This orchestrator keeps that strict
semantics while changing transaction granularity:

1. run the whole requested batch;
2. if the strict yield gate passes, run recent-corpus upstream parity on that same
   candidate batch before accepting it;
3. if either gate identifies explicit provider regressions, record only those
   providers as quarantined, hard-reset to the exact pre-attempt commit, and rerun
   the remaining providers together;
4. any failure without explicit provider evidence aborts instead of being hidden.

No lost/regressed provider mutation survives a reset. The final working tree contains
only a batch that passed both the strict representative yield gate and the selected
recent-corpus parity gate. Quarantined providers remain repair debt in a durable JSON
ledger for the next diagnostic pass.
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
YIELD_REPORT = ROOT / "automation/provider-repair-fast-yield.json"
SUMMARY_REPORT = ROOT / "automation/provider-repair-fast-summary.json"
PARITY_REPORT = ROOT / "automation/provider-repair-batch-parity.json"
OUT_DEFAULT = ROOT / "automation/provider-repair-batch-quarantine.json"
RUNNER = ROOT / "scripts/run_provider_repair_fast_targeted_v20.py"
PARITY = ROOT / "scripts/run_provider_upstream_parity_v3.py"
DEFAULT_SCOPE = "automation/evidence/hub-lab-matrix-46.json"


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def lost_pairs(report: dict[str, Any]) -> list[tuple[str, str]]:
    accounting = report.get("upstreamPositiveAccounting")
    raw: Any = None
    if isinstance(accounting, dict):
        raw = accounting.get("activeLostPairs")
    if not raw:
        raw = report.get("lostUpstreamPositivePairs")
    out: list[tuple[str, str]] = []
    for pair in raw or []:
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        provider, lane = cid(pair[0]), cid(pair[1])
        if provider and lane:
            out.append((provider, lane))
    return sorted(set(out))


def parity_regression_pairs(report: dict[str, Any]) -> list[tuple[str, str]]:
    """Return only certain recent-corpus regressions, never RESAMPLE/technical rows."""
    out: list[tuple[str, str]] = []
    for provider_row in report.get("providers") or []:
        if not isinstance(provider_row, dict):
            continue
        provider = cid(provider_row.get("providerId"))
        if not provider or str(provider_row.get("status") or "") != "REGRESSION":
            continue
        for lane_row in provider_row.get("lanes") or []:
            if not isinstance(lane_row, dict) or str(lane_row.get("status") or "") != "REGRESSION":
                continue
            lane = cid(lane_row.get("lane"))
            if lane:
                out.append((provider, lane))
    return sorted(set(out))


def provider_set(pairs: list[tuple[str, str]]) -> list[str]:
    return sorted({provider for provider, _lane in pairs})


def git(*args: str, capture: bool = False) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=capture,
        check=True,
    )
    return proc.stdout.strip() if capture else ""


def clean_to(base_sha: str) -> None:
    # The orchestrator/workflow are committed before execution, so resetting to
    # base_sha cannot erase the runner itself. Remove every failed candidate
    # mutation and untracked generated bundle before the next batch attempt.
    git("reset", "--hard", base_sha)
    git("clean", "-fd")


def run_batch(
    providers: list[str],
    *,
    skip_file: str,
    attempts: int,
    workers: int,
    timeout: int,
    defer_global_guard: bool,
) -> int:
    cmd = [
        sys.executable,
        str(RUNNER),
        "--skip-file", skip_file,
        "--attempts", str(attempts),
        "--workers", str(workers),
        "--timeout", str(timeout),
    ]
    if defer_global_guard:
        cmd.append("--defer-global-guard")
    for provider in providers:
        cmd.extend(["--provider", provider])
    print(
        "FIELD_PROVIDER_BATCH_QUARANTINE_ATTEMPT "
        f"providers={','.join(providers)} count={len(providers)}",
        flush=True,
    )
    proc = subprocess.run(cmd, cwd=ROOT, env=os.environ.copy(), check=False)
    return int(proc.returncode)


def run_parity(
    providers: list[str],
    *,
    samples: int,
    workers: int,
    timeout: int,
    seed: str,
    scope_matrix: str,
) -> tuple[int, dict[str, Any]]:
    cmd = [
        sys.executable,
        str(PARITY),
        "--scope-matrix", scope_matrix,
        "--samples-per-lane", str(samples),
        "--workers", str(workers),
        "--timeout", str(timeout),
        "--seed", seed,
        "--out", str(PARITY_REPORT.relative_to(ROOT)),
    ]
    for provider in providers:
        cmd.extend(["--provider", provider])
    print(
        "FIELD_PROVIDER_BATCH_PARITY_ATTEMPT "
        f"providers={','.join(providers)} samples_per_lane={samples}",
        flush=True,
    )
    proc = subprocess.run(cmd, cwd=ROOT, env=os.environ.copy(), check=False)
    report = load_json(PARITY_REPORT)
    return int(proc.returncode), report


def quarantine(
    *,
    pairs: list[tuple[str, str]],
    remaining: list[str],
    quarantined: dict[str, set[str]],
) -> tuple[list[str], list[str]]:
    lost_providers = [provider for provider in provider_set(pairs) if provider in remaining]
    for provider, lane in pairs:
        if provider in lost_providers:
            quarantined.setdefault(provider, set()).add(lane)
    survivors = [provider for provider in remaining if provider not in lost_providers]
    return lost_providers, survivors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--skip-file", default="automation/provider-repair-planner-authorized-skip.json")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--defer-global-guard", action="store_true")
    parser.add_argument("--parity-samples", type=int, default=12)
    parser.add_argument("--parity-workers", type=int, default=12)
    parser.add_argument("--parity-timeout", type=int, default=25)
    parser.add_argument("--parity-seed", default="20260913-batch-quarantine")
    parser.add_argument("--scope-matrix", default=DEFAULT_SCOPE)
    parser.add_argument("--output", default=str(OUT_DEFAULT.relative_to(ROOT)))
    parser.add_argument("--max-rounds", type=int, default=0)
    args = parser.parse_args()

    requested: list[str] = []
    for raw in args.provider:
        provider = cid(raw)
        if provider and provider not in requested:
            requested.append(provider)
    if not requested:
        raise SystemExit("empty provider batch")

    base_sha = git("rev-parse", "HEAD", capture=True)
    if not base_sha:
        raise SystemExit("unable to resolve baseline commit")
    if git("status", "--porcelain", capture=True):
        raise SystemExit("batch quarantine requires a clean working tree at start")

    remaining = list(requested)
    quarantined: dict[str, set[str]] = {}
    rounds: list[dict[str, Any]] = []
    max_rounds = int(args.max_rounds) if int(args.max_rounds) > 0 else len(requested) + 1

    for round_index in range(1, max_rounds + 1):
        if not remaining:
            break
        repair_rc = run_batch(
            remaining,
            skip_file=args.skip_file,
            attempts=max(1, min(int(args.attempts), 4)),
            workers=max(1, min(int(args.workers), 12)),
            timeout=max(15, min(int(args.timeout), 120)),
            defer_global_guard=bool(args.defer_global_guard),
        )
        yield_report = load_json(YIELD_REPORT)
        summary = load_json(SUMMARY_REPORT)
        strict_pairs = lost_pairs(yield_report)

        round_row: dict[str, Any] = {
            "round": round_index,
            "providers": list(remaining),
            "repairReturnCode": repair_rc,
            "targetGatePassed": bool(summary.get("targetGatePassed")),
            "strictLostPairs": [list(pair) for pair in strict_pairs],
        }

        if repair_rc != 0:
            lost_providers, survivors = quarantine(
                pairs=strict_pairs,
                remaining=remaining,
                quarantined=quarantined,
            )
            round_row["quarantineReason"] = "strict_yield_loss"
            round_row["quarantinedProviders"] = lost_providers
            rounds.append(round_row)
            if not lost_providers:
                print(
                    "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
                    f"round={round_index} reason=failed_without_explicit_lost_provider rc={repair_rc}",
                    flush=True,
                )
                return repair_rc or 2
            if not survivors:
                print(
                    "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
                    f"round={round_index} reason=all_providers_quarantined providers={','.join(lost_providers)}",
                    flush=True,
                )
                return 3
            print(
                "FIELD_PROVIDER_BATCH_QUARANTINE_DROP "
                f"round={round_index} gate=strict_yield lost={','.join(lost_providers)} "
                f"survivors={','.join(survivors)} action=hard_reset_and_retry_batch",
                flush=True,
            )
            clean_to(base_sha)
            remaining = survivors
            continue

        parity_rc, parity_report = run_parity(
            remaining,
            samples=max(1, min(32, int(args.parity_samples))),
            workers=max(1, min(16, int(args.parity_workers))),
            timeout=max(5, min(60, int(args.parity_timeout))),
            seed=str(args.parity_seed),
            scope_matrix=str(args.scope_matrix),
        )
        if parity_rc != 0 or not parity_report:
            round_row["parityReturnCode"] = parity_rc
            round_row["quarantineReason"] = "parity_harness_failure"
            rounds.append(round_row)
            print(
                "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
                f"round={round_index} reason=parity_harness_failure rc={parity_rc}",
                flush=True,
            )
            return parity_rc or 5

        parity_pairs = parity_regression_pairs(parity_report)
        parity_lost, survivors = quarantine(
            pairs=parity_pairs,
            remaining=remaining,
            quarantined=quarantined,
        )
        round_row["parityReturnCode"] = parity_rc
        round_row["parityStatusCounts"] = parity_report.get("statusCounts") or {}
        round_row["parityRegressionPairs"] = [list(pair) for pair in parity_pairs]
        round_row["quarantinedProviders"] = parity_lost
        rounds.append(round_row)

        if parity_lost:
            if not survivors:
                print(
                    "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
                    f"round={round_index} reason=all_providers_quarantined_by_parity "
                    f"providers={','.join(parity_lost)}",
                    flush=True,
                )
                return 6
            print(
                "FIELD_PROVIDER_BATCH_QUARANTINE_DROP "
                f"round={round_index} gate=recent_parity lost={','.join(parity_lost)} "
                f"survivors={','.join(survivors)} action=hard_reset_and_retry_batch",
                flush=True,
            )
            clean_to(base_sha)
            remaining = survivors
            continue

        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        payload = {
            "schemaVersion": 2,
            "baselineSha": base_sha,
            "requestedProviders": requested,
            "acceptedProviders": remaining,
            "quarantinedProviders": sorted(quarantined),
            "quarantinedLanes": {key: sorted(value) for key, value in sorted(quarantined.items())},
            "rounds": rounds,
            "strictYieldGatePreserved": True,
            "recentParityGatePreserved": True,
            "paritySamplesPerLane": max(1, min(32, int(args.parity_samples))),
            "failedCandidateMutationsPreserved": False,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            "FIELD_PROVIDER_BATCH_QUARANTINE_OK "
            f"requested={len(requested)} accepted={len(remaining)} quarantined={len(quarantined)} "
            f"rounds={round_index} providers={','.join(remaining)} "
            f"quarantine={','.join(sorted(quarantined)) or 'none'} "
            f"parity_samples={max(1, min(32, int(args.parity_samples)))}",
            flush=True,
        )
        return 0

    print(
        "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
        f"reason=round_budget_exhausted rounds={len(rounds)} remaining={','.join(remaining)}",
        flush=True,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
