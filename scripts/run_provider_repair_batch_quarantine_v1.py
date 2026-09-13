#!/usr/bin/env python3
"""Run targeted Provider repair as a multi-provider batch with fail-closed quarantine.

The underlying fast repair gate is intentionally strict: any enabled upstream-positive
lane that is lost makes the candidate fail. Historically this made one flaky provider
discard every valid mutation in the same batch. This orchestrator keeps that strict
semantics while changing transaction granularity:

1. run the whole requested batch;
2. if it passes, keep the workspace as the accepted candidate;
3. if it fails *and* the yield report names lost upstream-positive providers,
   record those providers as quarantined, hard-reset the workspace to the exact
   pre-attempt commit, and rerun the remaining providers together;
4. any failure without explicit lost-provider evidence aborts instead of being hidden.

No lost provider mutation survives a reset. The final working tree therefore contains
only a batch that passed the existing strict yield gate. Quarantined providers remain
repair debt and are emitted in a durable JSON ledger for the next diagnostic pass.
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
OUT_DEFAULT = ROOT / "automation/provider-repair-batch-quarantine.json"
RUNNER = ROOT / "scripts/run_provider_repair_fast_targeted_v20.py"


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
    # The workflow containing this orchestrator is committed before execution, so
    # resetting to base_sha cannot erase the runner itself. Remove all failed
    # candidate mutations and untracked generated bundles before the next batch.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--skip-file", default="automation/provider-repair-planner-authorized-skip.json")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--defer-global-guard", action="store_true")
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
        rc = run_batch(
            remaining,
            skip_file=args.skip_file,
            attempts=max(1, min(int(args.attempts), 4)),
            workers=max(1, min(int(args.workers), 12)),
            timeout=max(15, min(int(args.timeout), 120)),
            defer_global_guard=bool(args.defer_global_guard),
        )
        yield_report = load_json(YIELD_REPORT)
        summary = load_json(SUMMARY_REPORT)
        pairs = lost_pairs(yield_report)
        lost_providers = [provider for provider in provider_set(pairs) if provider in remaining]
        rounds.append({
            "round": round_index,
            "providers": list(remaining),
            "returnCode": rc,
            "targetGatePassed": bool(summary.get("targetGatePassed")),
            "lostPairs": [list(pair) for pair in pairs],
            "lostProviders": list(lost_providers),
        })

        if rc == 0:
            out_path = Path(args.output)
            if not out_path.is_absolute():
                out_path = ROOT / out_path
            payload = {
                "schemaVersion": 1,
                "baselineSha": base_sha,
                "requestedProviders": requested,
                "acceptedProviders": remaining,
                "quarantinedProviders": sorted(quarantined),
                "quarantinedLanes": {key: sorted(value) for key, value in sorted(quarantined.items())},
                "rounds": rounds,
                "strictYieldGatePreserved": True,
                "failedCandidateMutationsPreserved": False,
            }
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(
                "FIELD_PROVIDER_BATCH_QUARANTINE_OK "
                f"requested={len(requested)} accepted={len(remaining)} quarantined={len(quarantined)} "
                f"rounds={round_index} providers={','.join(remaining)} "
                f"quarantine={','.join(sorted(quarantined)) or 'none'}",
                flush=True,
            )
            return 0

        # Only explicit upstream-positive losses are eligible for quarantine.
        # Wrong-content on such a lane is represented as a lost pair and remains
        # fail-closed; any unrelated harness/migration/test failure aborts here.
        if not lost_providers:
            print(
                "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
                f"round={round_index} reason=failed_without_explicit_lost_provider rc={rc}",
                flush=True,
            )
            return rc or 2

        survivors = [provider for provider in remaining if provider not in lost_providers]
        if not survivors:
            print(
                "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
                f"round={round_index} reason=all_providers_quarantined providers={','.join(lost_providers)}",
                flush=True,
            )
            return 3

        for provider, lane in pairs:
            if provider in lost_providers:
                quarantined.setdefault(provider, set()).add(lane)
        print(
            "FIELD_PROVIDER_BATCH_QUARANTINE_DROP "
            f"round={round_index} lost={','.join(lost_providers)} survivors={','.join(survivors)} "
            "action=hard_reset_and_retry_batch",
            flush=True,
        )
        clean_to(base_sha)
        remaining = survivors

    print(
        "FIELD_PROVIDER_BATCH_QUARANTINE_ABORT "
        f"reason=round_budget_exhausted rounds={len(rounds)} remaining={','.join(remaining)}",
        flush=True,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
