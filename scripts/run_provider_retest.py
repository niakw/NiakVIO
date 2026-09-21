#!/usr/bin/env python3
"""Observational current-byte Provider retest lane.

This lane never mutates Provider DATA, ProviderBase, manifests or repair programs.
It only executes the already-published/current working-tree providers, refreshes
proof history/census, and rebuilds the Repair batch plan.
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
AUTHORITY = ROOT / "automation" / "provider-authority-status.json"
HISTORY = ROOT / "automation" / "provider-census-proof-history.json"
REPORT = ROOT / "automation" / "provider-retest-latest.json"
TARGETS = ROOT / "automation" / "provider-retest-targets-latest.json"
CENSUS_MD = ROOT / "PROVIDER_CENSUS_STATUS.md"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str) -> None:
    print("FIELD_PROVIDER_RETEST_CMD " + " ".join(args), flush=True)
    subprocess.run(list(args), cwd=ROOT, env=os.environ.copy(), check=True)


def authority_map(authority: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        cid(row.get("provider")): row
        for row in authority.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }


def lifecycle_disabled(row: dict[str, Any]) -> bool:
    action = str(row.get("action") or row.get("authorityAction") or "")
    klass = str(row.get("authorityClass") or "")
    return action in {
        "KEEP_DISABLED",
        "DISABLE_MANUAL_POLICY",
        "DISABLE_SOURCE_REMOVED",
        "DISABLE_AUTHORITY_EXHAUSTED",
    } or klass in {"disabled", "manual-off", "source-removed", "stale-direct"}


def select_providers(
    status: dict[str, Any],
    authority: dict[str, Any],
    *,
    scope: str,
    requested: set[str],
    include_disabled: bool = False,
) -> list[str]:
    rows = {
        cid(row.get("provider")): row
        for row in status.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }
    auth = authority_map(authority)
    if requested:
        unknown = sorted(requested - set(rows))
        if unknown:
            raise ValueError("unknown census providers: " + ",".join(unknown))
        return sorted(requested)

    if scope == "repair":
        candidates = {cid(value) for value in status.get("repairQueue") or [] if cid(value)}
    elif scope == "all":
        candidates = set(rows)
    else:
        candidates = {
            provider
            for provider, row in rows.items()
            if str(row.get("status") or "") != "FULL OK"
        }

    selected: list[str] = []
    for provider in sorted(candidates):
        row = rows.get(provider) or {}
        authority_row = auth.get(provider) or {}
        if include_disabled:
            selected.append(provider)
            continue
        if str(row.get("status") or "") == "DISABLED":
            continue
        if lifecycle_disabled(authority_row or row):
            continue
        # Search/domain authority blockers are handled by Domain rather than by
        # repeatedly replaying stale provider bytes. An explicit --provider can
        # still force a diagnostic replay when needed.
        if authority_row and authority_row.get("repairEligible") is False:
            continue
        selected.append(provider)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="Retest current Provider bytes without repair mutation")
    parser.add_argument("--scope", choices=("non-full", "repair", "all"), default="non-full")
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args()

    if not STATUS.is_file():
        raise SystemExit("provider census status missing")
    run(sys.executable, "scripts/classify_provider_authority.py")
    status = load(STATUS)
    authority = load(AUTHORITY) if AUTHORITY.is_file() else {"providers": []}
    requested = {cid(value) for value in args.provider if cid(value)}
    selected = select_providers(
        status,
        authority,
        scope=args.scope,
        requested=requested,
        include_disabled=args.include_disabled,
    )
    TARGETS.parent.mkdir(parents=True, exist_ok=True)
    TARGETS.write_text(
        json.dumps({
            "schemaVersion": 1,
            "scope": args.scope,
            "explicit": bool(requested),
            "providerCount": len(selected),
            "providers": selected,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not selected:
        print(f"FIELD_PROVIDER_RETEST_EMPTY scope={args.scope}", flush=True)
        return 0

    output = args.output if args.output.is_absolute() else ROOT / args.output
    cmd = [
        sys.executable,
        "scripts/audit_provider_quick_yield.py",
        "--scope", "all",
        "--output", str(output),
    ]
    for provider in selected:
        cmd.extend(["--provider", provider])
    run(*cmd)

    run_id = str(os.environ.get("GITHUB_RUN_ID") or "local")
    sha = str(os.environ.get("GITHUB_SHA") or "local")
    if HISTORY.is_file():
        run(
            sys.executable,
            "scripts/update_provider_census_proof_history.py",
            str(output.relative_to(ROOT)),
            "--history", str(HISTORY.relative_to(ROOT)),
            "--run-id", f"{run_id}-retest",
            "--sha", sha,
        )

    render_cmd = [
        sys.executable,
        "scripts/render_provider_census_status.py",
        str(output.relative_to(ROOT)),
        "--output", str(CENSUS_MD.relative_to(ROOT)),
        "--json-output", str(STATUS.relative_to(ROOT)),
        "--history", str(HISTORY.relative_to(ROOT)),
        "--baseline-status", str(STATUS.relative_to(ROOT)),
        "--provider-overrides", "provider-overrides.json",
        "--authority-status", str(AUTHORITY.relative_to(ROOT)),
        "--run-id", f"{run_id}-retest",
        "--sha", sha,
    ]
    waf = ROOT / "automation" / "provider-waf-browser-session-latest.json"
    if waf.is_file():
        render_cmd.extend(["--waf-browser-evidence", str(waf.relative_to(ROOT))])
    candidate = ROOT / "automation" / "provider-repair-candidate-evidence.json"
    if candidate.is_file():
        render_cmd.extend(["--repair-candidate-evidence", str(candidate.relative_to(ROOT))])
    run(*render_cmd)

    # Re-apply the latest transport/residential differential after current-byte
    # interpretation. This is essential for cases where the provider runtime
    # reports a network exception even though the exact route is already proven
    # native-like reachable on GitHub/Tailscale: those must return to normal
    # CHAIN/ROUTE/Brain states instead of regressing to NETWORK BLOCKED.
    if waf.is_file():
        merged = ROOT / "automation" / ".provider-retest-census-transport.json"
        run(
            sys.executable,
            "scripts/merge_waf_census_transport.py",
            "--status", str(STATUS.relative_to(ROOT)),
            "--waf", str(waf.relative_to(ROOT)),
            "--authority-status", str(AUTHORITY.relative_to(ROOT)),
            "--output", str(merged.relative_to(ROOT)),
            "--run-id", f"{run_id}-retest-transport",
            "--sha", sha,
        )
        merged.replace(STATUS)
        run(
            sys.executable,
            "scripts/render_provider_census_status_from_state.py",
            "--status", str(STATUS.relative_to(ROOT)),
            "--output", str(CENSUS_MD.relative_to(ROOT)),
        )

    run(
        sys.executable,
        "scripts/build_provider_repair_batch_plan.py",
        "--status", str(STATUS.relative_to(ROOT)),
        "--overrides", "provider-overrides.json",
        "--output", "automation/provider-repair-batch-plan-latest.json",
    )

    refreshed = load(STATUS)
    by_provider = {
        cid(row.get("provider")): str(row.get("status") or "")
        for row in refreshed.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }
    summary = ",".join(f"{provider}:{by_provider.get(provider, 'missing')}" for provider in selected)
    print(
        "FIELD_PROVIDER_RETEST_DONE "
        f"scope={args.scope} providers={len(selected)} "
        f"repair_queue={len(refreshed.get('repairQueue') or [])} "
        f"environment={len(refreshed.get('environmentQueue') or [])} "
        f"statuses={summary}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
