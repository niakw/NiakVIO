#!/usr/bin/env python3
"""Strict Provider v3 reconstruction: one provider, all declared types, then next.

For each provider in manifest order:
1. materialize provider N candidate JS from its current candidate DATA;
2. probe that candidate JS with real fixtures for its declared semantic types;
3. capture HTTP evidence while keeping playback verification separate;
4. refuse to advance until every declared type has one successful live type route
   (or verified direct output for that type), unless the provider is proven
   terminally blocked/unreachable;
5. finalize structured DATA for provider N;
6. immediately rematerialize provider N final JS from live DATA;
7. re-probe the final JS and re-prove every declared type;
8. only then materialize or touch provider N+1.

Internal search/status/player/source requests remain chain evidence; they are not
an arbitrary coverage denominator. There is no inter-provider concurrency and no
global candidate materialization pass.
"""
from __future__ import annotations

import argparse
import copy
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from assert_active_provider_live_coverage import main as active_coverage_main
from materialize_provider_v3_one import materialize_one
from validate_provider_v3_routes_live import EXPECTED, KNOWLEDGE, OUTPUT, OVERRIDES, load, run_task, write
from validate_provider_v3_routes_sequential import (
    build_provider_queue,
    evaluate_provider,
    finalize_provider,
    provider_origins,
    probe_origin,
    should_pass,
)

ROOT = Path(__file__).resolve().parents[1]


def is_qualified(evaluation: dict[str, Any]) -> bool:
    """All declared types must be proven; internal request counts never substitute."""
    if not should_pass(evaluation):
        return False
    if evaluation.get("directOutputOnly"):
        return True
    return bool(
        int(evaluation.get("liveValidatedRouteCount") or 0) > 0
        and evaluation.get("providerSuccessHttp") is True
    )


def final_model_from_live(model: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(model)
    live_data = copy.deepcopy(model.get("routeData") or [])
    live_routes = list(model.get("routes") or [])
    value["candidateRouteData"] = live_data
    value["candidateRoutes"] = live_routes
    return value


def terminal_state(
    evaluation: dict[str, Any],
    model: dict[str, Any],
    patch: dict[str, Any],
    origin_timeout: int,
) -> tuple[str | None, list[dict[str, Any]]]:
    origins = provider_origins(model, patch)
    evidence: list[dict[str, Any]] = []
    if evaluation.get("providerRequestCount", 0) == 0 or not evaluation.get("providerSuccessHttp"):
        evidence = [probe_origin(url, origin_timeout) for url in origins]

    if evaluation.get("directOutputOnly") and evaluation.get("typeComplete"):
        return "direct-output-verified", evidence
    if evaluation.get("providerBlockedOnly") and evaluation.get("providerRequestCount", 0) > 0:
        return "terminal-blocked", evidence
    if origins and evidence and not any(row.get("reachable") for row in evidence):
        return "terminal-unreachable", evidence
    return None, evidence


def run_until_qualified(
    provider: dict[str, Any],
    model: dict[str, Any],
    minimum: float,
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    used_tasks: list[dict[str, Any]] = []
    evaluation = evaluate_provider(provider["provider_id"], model, rows, minimum)
    for task_index, task in enumerate(provider["tasks"], start=1):
        result = run_task(task, timeout)
        result["fixture_slug"] = task.get("fixture_slug")
        result["fixture"] = copy.deepcopy(task.get("fixture") or {})
        rows.append(result)
        used_tasks.append(copy.deepcopy(task))
        evaluation = evaluate_provider(provider["provider_id"], model, rows, minimum)
        http_counts = Counter(int(fetch.get("status") or 0) for fetch in result.get("fetches") or [])
        http_summary = ",".join(f"{status}:{count}" for status, count in sorted(http_counts.items())) or "none"
        print(
            "FIELD_PROVIDER_SEQUENTIAL_PROBE "
            f"provider={provider['provider_id']} fixture={task.get('fixture_slug')} "
            f"step={task_index}/{len(provider['tasks'])} task_status={result.get('status')} "
            f"http_statuses={http_summary} "
            f"declared_types={','.join(evaluation['requiredTypes']) or 'none'} "
            f"validated_types={','.join(evaluation['validatedTypes']) or 'none'} "
            f"missing_types={','.join(evaluation['missingTypes']) or 'none'} "
            f"type_coverage={evaluation['declaredTypeCoverageRatio']:.3f} target=1.000 "
            f"requests={evaluation['providerRequestCount']} "
            f"live={evaluation['liveValidatedRouteCount']}",
            flush=True,
        )
        if is_qualified(evaluation):
            break
    return rows, evaluation, used_tasks


def prove_final_bundle(
    provider: dict[str, Any],
    model: dict[str, Any],
    used_tasks: list[dict[str, Any]],
    final_filename: str,
    minimum: float,
    timeout: int,
) -> dict[str, Any]:
    if not used_tasks:
        return {
            "verified": False,
            "reason": "no-used-fixtures",
            "providerRequestCount": 0,
            "liveValidatedRouteCount": 0,
        }

    live_model = final_model_from_live(model)
    rows: list[dict[str, Any]] = []
    evaluation = evaluate_provider(provider["provider_id"], live_model, rows, minimum)
    for task in used_tasks:
        final_task = copy.deepcopy(task)
        final_task["filename"] = final_filename
        result = run_task(final_task, timeout)
        result["fixture_slug"] = final_task.get("fixture_slug")
        result["fixture"] = copy.deepcopy(final_task.get("fixture") or {})
        rows.append(result)
        evaluation = evaluate_provider(provider["provider_id"], live_model, rows, minimum)

    wrong = any(row.get("status") == "wrong_content" for row in rows)
    runtime_error = any(row.get("status") in {"runtime_error", "invalid_probe_output", "probe_error"} for row in rows)
    verified = is_qualified(evaluation) and not wrong and not runtime_error
    return {
        "verified": verified,
        "reason": "ok" if verified else "final-bundle-declared-type-proof-failed",
        "providerRequestCount": evaluation.get("providerRequestCount", 0),
        "liveValidatedRouteCount": evaluation.get("liveValidatedRouteCount", 0),
        "declaredTypeCoverageRatio": evaluation.get("declaredTypeCoverageRatio", 0.0),
        "requiredTypes": evaluation.get("requiredTypes", []),
        "validatedTypes": evaluation.get("validatedTypes", []),
        "missingTypes": evaluation.get("missingTypes", []),
        "typeComplete": evaluation.get("typeComplete", False),
        "statuses": [row.get("status") for row in rows],
    }


def checkpoint(
    output: Path,
    provider_rows: list[dict[str, Any]],
    totals: Counter,
    completed: int,
    minimum: float,
    failed_provider: str | None = None,
) -> None:
    write(output, {
        "schemaVersion": 4,
        "method": "strict-sequential-provider-reconstruct-declared-type-final-proof",
        "minimumCoverageRatio": minimum,
        "requiredDeclaredTypeCoverageRatio": 1.0,
        "declaredTypesAreGateDenominator": True,
        "internalRequestsAreGateDenominator": False,
        "providerCount": EXPECTED,
        "completedProviderCount": completed,
        "failedProvider": failed_provider,
        "candidateRouteCount": totals["candidates"],
        "attemptedRouteCount": totals["attempted"],
        "liveValidatedRouteCount": totals["live"],
        "blockedRouteCount": totals["blocked"],
        "failedRouteCount": totals["failed"],
        "providerRequestCount": totals["requests"],
        "finalBundleVerifiedCount": totals["final_verified"],
        "completionStates": {
            key: value for key, value in totals.items()
            if key not in {"candidates", "attempted", "live", "blocked", "failed", "requests", "final_verified"}
        },
        "providers": provider_rows,
        "sequentialNoInterProviderConcurrency": True,
        "globalCandidateMaterialization": False,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--minimum-coverage", type=float, default=0.75)
    parser.add_argument("--timeout", type=int, default=50)
    parser.add_argument("--origin-timeout", type=int, default=8)
    args = parser.parse_args()

    # Kept as CLI compatibility for existing workflow callers. It no longer
    # controls provider advancement: declared semantic type coverage is fixed at 100%.
    minimum = float(args.minimum_coverage)
    if not 0.5 <= minimum <= 1.0:
        raise SystemExit("--minimum-coverage must be between 0.5 and 1.0")
    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required")
    timeout = max(20, min(int(args.timeout), 120))
    origin_timeout = max(3, min(int(args.origin_timeout), 15))

    queue, provider_count = build_provider_queue()
    if provider_count != EXPECTED or len(queue) != EXPECTED:
        raise SystemExit(f"provider queue={provider_count}/{len(queue)}, expected={EXPECTED}")

    knowledge_path = args.knowledge.resolve()
    overrides_path = args.overrides.resolve()
    output_path = args.output.resolve()
    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    report_rows: list[dict[str, Any]] = []
    totals: Counter = Counter()

    for index, provider in enumerate(queue, start=1):
        provider_id = provider["provider_id"]
        static_row = providers.get(provider_id)
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        if not isinstance(static_row, dict):
            raise SystemExit(f"{provider_id}: missing static knowledge")
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        model["canonicalSupportedTypes"] = list(provider.get("supported_types") or [])

        print(
            "FIELD_PROVIDER_SEQUENTIAL_BEGIN "
            f"index={index} total={EXPECTED} provider={provider_id} "
            f"types={','.join(provider['supported_types'])} fixtures={len(provider['tasks'])}",
            flush=True,
        )

        candidate_materialized = materialize_one(provider_id)
        candidate_filename = str(candidate_materialized.get("file") or "")
        if not candidate_filename:
            raise SystemExit(f"{provider_id}: candidate one-provider materialization produced no file")
        for task in provider["tasks"]:
            task["filename"] = candidate_filename
        print(
            "FIELD_PROVIDER_CANDIDATE_MATERIALIZED "
            f"index={index} provider={provider_id} file={candidate_filename} "
            f"sha256={str(candidate_materialized.get('sha256') or '')[:16]}",
            flush=True,
        )

        _rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)
        completion_state = "declared-types-qualified" if is_qualified(evaluation) else None
        origin_evidence: list[dict[str, Any]] = []
        if completion_state is None:
            completion_state, origin_evidence = terminal_state(
                evaluation, model, patch, origin_timeout
            )

        if completion_state is None:
            failure = {
                **evaluation,
                "completionState": "missing-declared-type-route-proof",
                "originEvidence": origin_evidence,
                "advancedToNextProvider": False,
                "finalBundleVerified": False,
                "candidateBundleFile": candidate_filename,
                "candidateBundleSha256": candidate_materialized.get("sha256"),
            }
            report_rows.append(failure)
            checkpoint(output_path, report_rows, totals, index - 1, minimum, provider_id)
            write(knowledge_path, knowledge)
            write(overrides_path, overrides)
            raise SystemExit(
                f"{provider_id}: missing live route proof for declared types "
                f"{','.join(evaluation.get('missingTypes') or []) or 'unknown'}; "
                f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'}; "
                f"refusing to materialize or advance to provider {index + 1}"
            )

        finalize_provider(
            provider_id,
            provider,
            knowledge,
            overrides,
            evaluation,
            completion_state,
            origin_evidence,
        )
        write(knowledge_path, knowledge)
        write(overrides_path, overrides)

        materialized = materialize_one(provider_id)
        final_filename = str(materialized.get("file") or "")
        if not final_filename:
            raise SystemExit(f"{provider_id}: final one-provider materialization produced no file")

        final_proof: dict[str, Any]
        if completion_state in {"declared-types-qualified", "direct-output-verified"}:
            final_proof = prove_final_bundle(
                provider,
                model,
                used_tasks,
                final_filename,
                minimum,
                timeout,
            )
            if not final_proof.get("verified"):
                failure = {
                    **evaluation,
                    "completionState": completion_state,
                    "originEvidence": origin_evidence,
                    "advancedToNextProvider": False,
                    "finalBundleVerified": False,
                    "finalBundleProof": final_proof,
                    "candidateBundleFile": candidate_filename,
                    "candidateBundleSha256": candidate_materialized.get("sha256"),
                    "finalBundleFile": final_filename,
                    "finalBundleSha256": materialized.get("sha256"),
                }
                report_rows.append(failure)
                checkpoint(output_path, report_rows, totals, index - 1, minimum, provider_id)
                raise SystemExit(
                    f"{provider_id}: candidate DATA proved all declared types but final bundle did not; "
                    f"missing={','.join(final_proof.get('missingTypes') or []) or 'unknown'}; "
                    f"refusing to materialize or advance to provider {index + 1}"
                )
        else:
            final_proof = {
                "verified": False,
                "reason": completion_state,
                "providerRequestCount": evaluation.get("providerRequestCount", 0),
                "liveValidatedRouteCount": evaluation.get("liveValidatedRouteCount", 0),
            }

        row = {
            **evaluation,
            "completionState": completion_state,
            "originEvidence": origin_evidence,
            "advancedToNextProvider": True,
            "finalBundleVerified": bool(final_proof.get("verified")),
            "finalBundleProof": final_proof,
            "candidateBundleFile": candidate_filename,
            "candidateBundleSha256": candidate_materialized.get("sha256"),
            "finalBundleFile": final_filename,
            "finalBundleSha256": materialized.get("sha256"),
        }
        report_rows.append(row)
        totals["candidates"] += int(evaluation.get("candidateRouteCount") or 0)
        totals["attempted"] += int(evaluation.get("attemptedRouteCount") or 0)
        totals["live"] += int(evaluation.get("liveValidatedRouteCount") or 0)
        totals["blocked"] += int(evaluation.get("blockedRouteCount") or 0)
        totals["failed"] += int(evaluation.get("failedRouteCount") or 0)
        totals["requests"] += int(evaluation.get("providerRequestCount") or 0)
        totals[completion_state] += 1
        if final_proof.get("verified"):
            totals["final_verified"] += 1

        checkpoint(output_path, report_rows, totals, index, minimum)
        print(
            "FIELD_PROVIDER_SEQUENTIAL_PASS "
            f"index={index} provider={provider_id} state={completion_state} "
            f"validated_types={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
            f"type_coverage={evaluation.get('declaredTypeCoverageRatio', 0.0):.3f} "
            f"live={evaluation['liveValidatedRouteCount']} "
            f"requests={evaluation['providerRequestCount']} "
            f"final_bundle_verified={str(bool(final_proof.get('verified'))).lower()}",
            flush=True,
        )

    final_report = load(output_path)
    final_report["allProvidersAdvancedSequentially"] = True
    final_report["globalCandidateMaterialization"] = False
    final_report["declaredTypesAreGateDenominator"] = True
    final_report["requiredDeclaredTypeCoverageRatio"] = 1.0
    write(output_path, final_report)
    knowledge["liveRouteValidation"] = {
        "schemaVersion": 4,
        "method": "strict-sequential-provider-reconstruct-declared-type-final-proof",
        "providerCount": EXPECTED,
        "completedProviderCount": EXPECTED,
        "allProvidersAdvancedSequentially": True,
        "sequentialNoInterProviderConcurrency": True,
        "globalCandidateMaterialization": False,
        "declaredTypesAreGateDenominator": True,
        "requiredDeclaredTypeCoverageRatio": 1.0,
        "internalRequestsAreGateDenominator": False,
        "staticEvidenceIsHttpProof": False,
        "candidateRoutesAreExecutableAuthority": False,
    }
    write(knowledge_path, knowledge)

    saved_argv = sys.argv[:]
    try:
        sys.argv = [
            "assert_active_provider_live_coverage.py",
            "--manifest", str(ROOT / "manifest.json"),
            "--report", str(output_path),
        ]
        active_coverage_main()
    finally:
        sys.argv = saved_argv

    print(
        "FIELD_PROVIDER_ROUTE_SEQUENTIAL_COMPLETE "
        f"providers={EXPECTED} declared_type_coverage=1.00 "
        f"live={final_report.get('liveValidatedRouteCount', 0)} "
        f"requests={final_report.get('providerRequestCount', 0)} "
        f"final_verified={final_report.get('finalBundleVerifiedCount', 0)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
