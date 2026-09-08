#!/usr/bin/env python3
"""Fast targeted acceptance for Provider repair iterations.

This is deliberately NOT a publication gate. It executes the same proof-first
migrations and target recovery/yield checks as the canonical V6 pipeline, but it
materializes only explicitly requested providers and skips the full 96-provider
portfolio baseline/rematerialization.

Failed experiments stop before the expensive 96-provider output guard. A target
candidate must first prove an actual targeted yield gain. The canonical full
portfolio gate remains mandatory before promotion/publication.
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
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
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


def _row_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in report.get("providers") or []:
        if not isinstance(row, dict):
            continue
        provider = cid(row.get("providerId") or row.get("id") or row.get("provider"))
        if provider:
            out[provider] = row
    return out


def _query_bearing(row: dict[str, Any]) -> bool:
    route = str(row.get("route") or "").casefold()
    if "{query}" in route or any(token in route for token in ("?q=", "&q=", "?s=", "&s=", "keyword=")):
        return True
    spec = row.get("requestSpec") if isinstance(row.get("requestSpec"), dict) else {}
    body = spec.get("body") if isinstance(spec.get("body"), dict) else {}
    return any("{query}" in str(value) for value in body.values())


def verify_structured_plan_wiring(targets: list[str]) -> None:
    """Verify that positive proof retains executable authority without imposing a shape.

    Three top-level entry plans is a normal optimization target, not an invariant.
    A provider may legitimately expose >3 evidence-backed authorities or a
    search/detail/player/source fan-out. The wiring gate therefore fails only when
    positive proof loses *all* executable authority; high counts are audited.
    """
    targeted = _row_map(load(TARGET_REPORT))
    overrides = load(OVERRIDES)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    knowledge = load(KNOWLEDGE) if KNOWLEDGE.exists() else {}
    kproviders = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    missing: list[str] = []
    for provider in targets:
        row = targeted.get(provider) or {}
        positive_search = False
        for proof in row.get("routeData") or []:
            if not isinstance(proof, dict) or proof.get("requestSpecReusable") is not True:
                continue
            if int(proof.get("taskStreamCount") or 0) <= 0 and int(proof.get("taskRawStreamCount") or 0) <= 0:
                continue
            if str(proof.get("role") or "").casefold() == "search" or _query_bearing(proof):
                positive_search = True
                break
        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        krow = kproviders.get(provider) if isinstance(kproviders.get(provider), dict) else {}
        model = krow.get("model") if isinstance(krow.get("model"), dict) else krow
        search_plan = patch.get("search_request_plan") or model.get("searchRequestPlan") or model.get("search_request_plan") or []
        external_plan = patch.get("external_identity_plan") or model.get("externalIdentityPlan") or model.get("external_identity_plan") or []
        provider_value_plan = patch.get("provider_value_plan") or model.get("providerValuePlan") or []
        api_recipe = patch.get("api_recipe") or model.get("apiRecipe")
        learned_routes = patch.get("learned_routes") or model.get("routes") or []
        authority_count = (
            len(provider_value_plan) if isinstance(provider_value_plan, list) else int(bool(provider_value_plan))
        ) + int(bool(api_recipe)) + (
            len(external_plan) if isinstance(external_plan, list) else int(bool(external_plan))
        ) + (
            len(search_plan) if isinstance(search_plan, list) else int(bool(search_plan))
        ) + (
            len(learned_routes) if isinstance(learned_routes, list) else int(bool(learned_routes))
        )
        route_proof = model.get("routeProof") if isinstance(model.get("routeProof"), dict) else {}
        authority_audit = route_proof.get("canonicalExecutionAuthority") if isinstance(route_proof.get("canonicalExecutionAuthority"), dict) else {}
        preferred_count = int(authority_audit.get("preferredCount") or authority_audit.get("selectedCount") or 0)
        normal_target = int(route_proof.get("normalRuntimeEntryPlanTarget") or 3)
        target_exceeded = authority_count > normal_target
        print(
            "FIELD_PROVIDER_FAST_PLAN "
            f"provider={provider} positive_search={str(positive_search).lower()} "
            f"provider_value={len(provider_value_plan) if isinstance(provider_value_plan, list) else int(bool(provider_value_plan))} "
            f"recipe={int(bool(api_recipe))} "
            f"search_plan={len(search_plan) if isinstance(search_plan, list) else int(bool(search_plan))} "
            f"external_plan={len(external_plan) if isinstance(external_plan, list) else int(bool(external_plan))} "
            f"routes={len(learned_routes) if isinstance(learned_routes, list) else int(bool(learned_routes))} "
            f"top_level_authorities={authority_count} preferred_authorities={preferred_count} "
            f"normal_target={normal_target} target_exceeded={str(target_exceeded).lower()} "
            "overflow_is_error=false",
            flush=True,
        )
        # A positive structured search may legitimately be absorbed by a stronger
        # provider-value/API authority. Require an executable authority, not a
        # redundant SearchRequestPlan field or a particular authority count.
        if positive_search and authority_count == 0:
            missing.append(provider)
    if missing:
        raise SystemExit("positive proof lost before materialization: " + ",".join(missing))


def write_summary(
    *,
    targets: list[str],
    attempts: int,
    target_report: dict[str, Any],
    yield_report: dict[str, Any],
    target_gate: bool,
    global_guard: bool,
    global_guard_deferred: bool = False,
) -> None:
    summary = {
        "schemaVersion": 3,
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
        "targetGatePassed": bool(target_gate),
        "globalNonNetworkGuardPassed": bool(global_guard),
        "globalNonNetworkGuardDeferred": bool(global_guard_deferred),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_FAST_FINAL "
        f"targeted={len(targets)} proven={summary['providersWithProvenRoutes']} "
        f"playable={len(summary['playableProviders'])} verified={len(summary['verifiedProviders'])} "
        f"lost={len(summary['lostUpstreamPositivePairs'])} "
        f"target_gate={str(target_gate).lower()} global_guard={str(global_guard).lower()} "
        f"global_guard_deferred={str(global_guard_deferred).lower()} "
        "full_portfolio_gate_required=true",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--skip-file", type=Path, default=DEFAULT_SKIP.relative_to(ROOT))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument(
        "--defer-global-guard",
        action="store_true",
        help="Defer the repeated 96-provider non-network guard to the consolidated candidate gate.",
    )
    args = parser.parse_args()

    manifest = load(MANIFEST)
    catalogue = [cid(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]
    if len(catalogue) != 96 or len(set(catalogue)) != 96:
        raise SystemExit(f"provider catalogue must be exactly 96, got {len(catalogue)}")

    skip_path = args.skip_file if args.skip_file.is_absolute() else ROOT / args.skip_file
    skip_cfg = load(skip_path)
    skipped = {cid(value) for value in (skip_cfg.get("providers") or {}).keys() if cid(value)}
    requested: list[str] = []
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
        f"attempts={attempts} defer_global_guard={str(args.defer_global_guard).lower()} "
        f"providers={','.join(targets)}",
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
        "scripts/upgrade_provider_search_detail_bridge_v17.py",
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
        "tests/runtime_route_plan_cap_v1_test.py",
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
    verify_structured_plan_wiring(targets)

    for provider in targets:
        run(sys.executable, "scripts/materialize_provider_v3_one.py", provider)

    run(sys.executable, "scripts/validate_published_provider_config.py", "--expected", "96")
    for test in (
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
    if yield_proc.returncode != 0:
        write_summary(
            targets=targets,
            attempts=attempts,
            target_report=target_report,
            yield_report=yield_report,
            target_gate=False,
            global_guard=False,
            global_guard_deferred=False,
        )
        print("FIELD_PROVIDER_FAST_EARLY_STOP reason=target_gate_failed expensive_global_guard_skipped=1", flush=True)
        return 1

    if args.defer_global_guard:
        write_summary(
            targets=targets,
            attempts=attempts,
            target_report=target_report,
            yield_report=yield_report,
            target_gate=True,
            global_guard=False,
            global_guard_deferred=True,
        )
        print(
            "FIELD_PROVIDER_FAST_DEFERRED_GLOBAL_GUARD "
            "reason=parallel_sweep consolidated_candidate_guard_required=1",
            flush=True,
        )
        return 0

    run(sys.executable, "tests/global_stream_output_guard_test.py")
    write_summary(
        targets=targets,
        attempts=attempts,
        target_report=target_report,
        yield_report=yield_report,
        target_gate=True,
        global_guard=True,
        global_guard_deferred=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
