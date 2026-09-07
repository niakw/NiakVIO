#!/usr/bin/env python3
"""Fast targeted acceptance for Provider repair iterations.

This is deliberately NOT a publication gate. It executes the same proof-first
migrations and target recovery/yield checks as the canonical V6 pipeline, but it
materializes only explicitly requested providers and skips the full 96-provider
portfolio baseline/rematerialization. A candidate that passes here must still run
the canonical full portfolio gate before promotion/publication.
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
MANIFEST = ROOT / "manifest.json"
DEFAULT_SKIP = ROOT / "automation" / "provider-repair-skip.json"
TARGET_REPORT = ROOT / "automation" / "provider-repair-fast-targeted.json"
MERGED_REPORT = ROOT / "automation" / "provider-repair-fast-merged.json"
YIELD_REPORT = ROOT / "automation" / "provider-repair-fast-yield.json"
SUMMARY = ROOT / "automation" / "provider-repair-fast-summary.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str, timeout: int | None = None) -> None:
    print("FIELD_PROVIDER_FAST_CMD " + " ".join(args), flush=True)
    subprocess.run(list(args), cwd=ROOT, env=os.environ.copy(), check=True, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--skip-file", type=Path, default=DEFAULT_SKIP.relative_to(ROOT))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()

    manifest = load(MANIFEST)
    catalogue = [cid(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]
    if len(catalogue) != 96 or len(set(catalogue)) != 96:
        raise SystemExit(f"provider catalogue must be exactly 96, got {len(catalogue)}")

    skip_path = args.skip_file if args.skip_file.is_absolute() else ROOT / args.skip_file
    skip_cfg = load(skip_path)
    skipped = {cid(value) for value in (skip_cfg.get("providers") or {}).keys() if cid(value)}
    requested = []
    for raw in args.provider:
        provider = cid(raw)
        if provider and provider not in requested:
            requested.append(provider)
    unknown = [value for value in requested if value not in catalogue]
    if unknown:
        raise SystemExit("unknown providers: " + ",".join(unknown))
    targets = [value for value in requested if value not in skipped]
    if not targets:
        raise SystemExit("all requested providers are already in skip/green set")

    attempts = max(1, min(int(args.attempts), 4))
    print(
        "FIELD_PROVIDER_FAST_SCOPE "
        f"catalogue=96 targeted={len(targets)} skipped_green={len(skipped)} "
        f"attempts={attempts} providers={','.join(targets)}",
        flush=True,
    )

    migrations = [
        "scripts/prepatch_identity_cleanup_shared_owner_v1.py",
        "scripts/apply_core_identity_ownership_cleanup.py",
        "scripts/upgrade_provider_worker_route_proof_v1.py",
        "scripts/upgrade_provider_base_runtime_v5.py",
        "scripts/upgrade_provider_base_route_requests_v1.py",
        "scripts/upgrade_provider_route_authority_v5.py",
        "scripts/upgrade_route_recovery_request_specs_v1.py",
        "scripts/upgrade_provider_v3_source_plan_v5.py",
        "scripts/upgrade_provider_repair_v6.py",
        "scripts/upgrade_provider_repair_v7.py",
        "scripts/upgrade_provider_repair_v8.py",
        "scripts/upgrade_provider_text_body_request_v9.py",
        "scripts/upgrade_provider_text_body_request_v9_1.py",
        "scripts/upgrade_provider_source_plan_v10.py",
        "scripts/upgrade_provider_external_identity_route_v11_1.py",
        "scripts/upgrade_provider_source_plan_v12.py",
        "scripts/upgrade_provider_route_plan_v13_2.py",
        "scripts/upgrade_provider_search_request_plan_v14.py",
        "scripts/upgrade_provider_search_request_plan_v14_1.py",
        "scripts/upgrade_provider_source_plan_v15.py",
        "scripts/upgrade_provider_route_retry_v1.py",
        "scripts/upgrade_provider_base_runtime_v11.py",
    ]
    for migration in migrations:
        run(sys.executable, migration)

    run("node", "--check", "scripts/provider_worker.cjs")
    for test in (
        "tests/provider_repair_v6_recipe_regression_test.py",
        "tests/provider_repair_merge_typed_recipe_test.py",
        "tests/provider_repair_v8_partial_typed_resolver_test.py",
        "tests/provider_text_body_request_v9_test.py",
        "tests/provider_source_plan_v10_regression_test.py",
        "tests/provider_external_identity_route_v11_test.py",
        "tests/provider_source_plan_v12_regression_test.py",
        "tests/provider_route_plan_v13_regression_test.py",
        "tests/provider_search_request_plan_v14_contract_test.py",
        "tests/provider_search_request_plan_v14_1_contract_test.py",
        "tests/provider_source_plan_v15_contract_test.py",
        "tests/global_identity_policy_ownership_test.py",
    ):
        run(sys.executable, test)

    cmd = [
        sys.executable,
        "scripts/recover_provider_routes_from_upstreams.py",
        "--workers", str(max(1, min(int(args.workers), 12))),
        "--timeout", str(max(15, min(int(args.timeout), 120))),
        "--attempts", str(attempts),
        "--out", str(TARGET_REPORT.relative_to(ROOT)),
    ]
    for provider in targets:
        cmd.extend(["--provider", provider])
    run(*cmd, timeout=max(600, len(targets) * max(15, int(args.timeout)) * attempts))

    run(
        sys.executable,
        "scripts/merge_provider_repair_report_v6.py",
        "--baseline", "automation/provider-route-recovery-v5.json",
        "--targeted", str(TARGET_REPORT.relative_to(ROOT)),
        "--output", str(MERGED_REPORT.relative_to(ROOT)),
    )
    run(sys.executable, "scripts/apply_provider_route_recovery_report.py", str(MERGED_REPORT.relative_to(ROOT)))
    run(
        sys.executable,
        "scripts/enforce_route_proof_manifest_policy_v1.py",
        "--report", str(MERGED_REPORT.relative_to(ROOT)),
        "--manifest", "manifest.json",
        "--overrides", "provider-overrides.json",
    )

    # The speed-up: rebuild only providers under investigation. Common ProviderBase
    # source is the same source used by full materialization, and each target still
    # passes the one-provider structural/minimizer invariants.
    for provider in targets:
        run(sys.executable, "scripts/materialize_provider_v3_one.py", provider)

    run(sys.executable, "scripts/validate_published_provider_config.py", "--expected", "96")
    for test in (
        "tests/global_stream_output_guard_test.py",
        "tests/episodic_identity_runtime_test.py",
        "tests/episodic_year_identity_regression_test.py",
        "tests/global_media_type_resolution_test.py",
        "tests/native_dual_id_identity_test.py",
    ):
        run(sys.executable, test)

    yield_cmd = [
        sys.executable,
        "scripts/audit_provider_repair_yield_v6.py",
        "--recovery", str(TARGET_REPORT.relative_to(ROOT)),
        "--skip-file", str(skip_path.relative_to(ROOT) if skip_path.is_relative_to(ROOT) else skip_path),
        "--output", str(YIELD_REPORT.relative_to(ROOT)),
        "--require-upstream-positive-preserved",
    ]
    yield_proc = subprocess.run(yield_cmd, cwd=ROOT, env=os.environ.copy(), check=False)
    yield_report = load(YIELD_REPORT) if YIELD_REPORT.exists() else {}
    target_report = load(TARGET_REPORT)
    summary = {
        "schemaVersion": 1,
        "publicationAllowed": False,
        "fullPortfolioGateRequired": True,
        "catalogueProviderCount": 96,
        "targetedProviders": targets,
        "targetedProviderCount": len(targets),
        "maxAttemptsPerTask": attempts,
        "providersWithProvenRoutes": int(target_report.get("providersWithProvenRoutes") or 0),
        "provenRouteCount": int(target_report.get("provenRouteCount") or 0),
        "playableProviders": yield_report.get("playableProviders") or [],
        "verifiedProviders": yield_report.get("verifiedProviders") or [],
        "lostUpstreamPositivePairs": yield_report.get("lostUpstreamPositivePairs") or [],
        "targetGatePassed": yield_proc.returncode == 0,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_FAST_FINAL "
        f"targeted={len(targets)} proven={summary['providersWithProvenRoutes']} "
        f"playable={len(summary['playableProviders'])} verified={len(summary['verifiedProviders'])} "
        f"lost={len(summary['lostUpstreamPositivePairs'])} "
        f"target_gate={str(summary['targetGatePassed']).lower()} full_portfolio_gate_required=true",
        flush=True,
    )
    return 0 if summary["targetGatePassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
