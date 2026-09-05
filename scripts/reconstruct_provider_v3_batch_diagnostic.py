#!/usr/bin/env python3
"""Probe a bounded Provider v3 slice without stopping at the first bad provider.

This is a workbench diagnostic accelerator, not a publication gate. Each provider
is still materialized and probed independently with the same declared-type rules
as the strict N-to-N reconstruction. A provider that lacks proof is recorded and
left unfinalized, while the diagnostic continues through the configured slice so
multiple real failures can be fixed in one batch. The script exits non-zero when
hard failures are present, after writing the complete report.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from materialize_provider_v3_one import materialize_one
from reconstruct_provider_v3_sequential_live import (
    is_qualified,
    prove_final_bundle,
    run_until_qualified,
    terminal_state,
)
from validate_provider_v3_routes_live import EXPECTED, KNOWLEDGE, OVERRIDES, load, write
from validate_provider_v3_routes_sequential import build_provider_queue, finalize_provider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "provider-v3-batch-diagnostic.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-index", type=int, default=1, help="1-based manifest/provider queue index")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--minimum-coverage", type=float, default=0.75)
    parser.add_argument("--timeout", type=int, default=50)
    parser.add_argument("--origin-timeout", type=int, default=8)
    args = parser.parse_args()

    queue, provider_count = build_provider_queue()
    if provider_count != EXPECTED or len(queue) != EXPECTED:
        raise SystemExit(f"provider queue={provider_count}/{len(queue)}, expected={EXPECTED}")

    start = max(1, int(args.start_index))
    count = max(1, min(int(args.count), EXPECTED))
    if start > EXPECTED:
        raise SystemExit(f"--start-index {start} exceeds provider count {EXPECTED}")
    end = min(EXPECTED, start + count - 1)
    selected = queue[start - 1:end]

    minimum = float(args.minimum_coverage)
    timeout = max(20, min(int(args.timeout), 120))
    origin_timeout = max(3, min(int(args.origin_timeout), 15))

    knowledge_path = args.knowledge.resolve()
    overrides_path = args.overrides.resolve()
    report_path = args.report.resolve()
    knowledge = load(knowledge_path)
    overrides = load(overrides_path)
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}

    rows: list[dict[str, Any]] = []
    hard_failures: list[str] = []
    terminal_only: list[str] = []
    final_verified: list[str] = []

    print(
        f"FIELD_PROVIDER_BATCH_BEGIN start={start} end={end} count={len(selected)} total={EXPECTED}",
        flush=True,
    )

    for absolute_index, provider in enumerate(selected, start=start):
        provider_id = provider["provider_id"]
        static_row = providers.get(provider_id)
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        if not isinstance(static_row, dict):
            hard_failures.append(provider_id)
            rows.append({
                "index": absolute_index,
                "providerId": provider_id,
                "result": "missing-static-knowledge",
                "advancedForDiagnostics": True,
            })
            continue

        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        model["canonicalSupportedTypes"] = list(provider.get("supported_types") or [])

        print(
            "FIELD_PROVIDER_BATCH_PROVIDER_BEGIN "
            f"index={absolute_index} provider={provider_id} "
            f"types={','.join(provider.get('supported_types') or []) or 'none'}",
            flush=True,
        )

        candidate = materialize_one(provider_id)
        candidate_filename = str(candidate.get("file") or "")
        if not candidate_filename:
            hard_failures.append(provider_id)
            rows.append({
                "index": absolute_index,
                "providerId": provider_id,
                "result": "candidate-materialization-failed",
                "advancedForDiagnostics": True,
            })
            continue
        for task in provider["tasks"]:
            task["filename"] = candidate_filename

        _probe_rows, evaluation, used_tasks = run_until_qualified(
            provider, model, minimum, timeout
        )
        completion_state = "declared-types-qualified" if is_qualified(evaluation) else None
        origin_evidence: list[dict[str, Any]] = []
        if completion_state is None:
            completion_state, origin_evidence = terminal_state(
                evaluation, model, patch, origin_timeout
            )

        if completion_state is None:
            hard_failures.append(provider_id)
            rows.append({
                **evaluation,
                "index": absolute_index,
                "providerId": provider_id,
                "result": "missing-declared-type-route-proof",
                "completionState": "missing-declared-type-route-proof",
                "originEvidence": origin_evidence,
                "candidateBundleFile": candidate_filename,
                "candidateBundleSha256": candidate.get("sha256"),
                "advancedForDiagnostics": True,
                "finalBundleVerified": False,
            })
            print(
                "FIELD_PROVIDER_BATCH_PROVIDER_FAIL "
                f"index={absolute_index} provider={provider_id} "
                f"missing={','.join(evaluation.get('missingTypes') or []) or 'unknown'} "
                f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'}",
                flush=True,
            )
            continue

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

        final_materialized = materialize_one(provider_id)
        final_filename = str(final_materialized.get("file") or "")
        final_proof: dict[str, Any]
        if completion_state in {"declared-types-qualified", "direct-output-verified"}:
            final_proof = prove_final_bundle(
                provider,
                model,
                used_tasks,
                final_filename,
                minimum,
                timeout,
            ) if final_filename else {"verified": False, "reason": "final-materialization-failed"}
            if final_proof.get("verified"):
                final_verified.append(provider_id)
            else:
                hard_failures.append(provider_id)
        else:
            terminal_only.append(provider_id)
            final_proof = {
                "verified": False,
                "reason": completion_state,
                "providerRequestCount": evaluation.get("providerRequestCount", 0),
                "liveValidatedRouteCount": evaluation.get("liveValidatedRouteCount", 0),
            }

        rows.append({
            **evaluation,
            "index": absolute_index,
            "providerId": provider_id,
            "result": "ok" if final_proof.get("verified") else completion_state,
            "completionState": completion_state,
            "originEvidence": origin_evidence,
            "candidateBundleFile": candidate_filename,
            "candidateBundleSha256": candidate.get("sha256"),
            "finalBundleFile": final_filename,
            "finalBundleSha256": final_materialized.get("sha256"),
            "finalBundleVerified": bool(final_proof.get("verified")),
            "finalBundleProof": final_proof,
            "advancedForDiagnostics": True,
        })
        print(
            "FIELD_PROVIDER_BATCH_PROVIDER_RESULT "
            f"index={absolute_index} provider={provider_id} state={completion_state} "
            f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
            f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'} "
            f"final_verified={str(bool(final_proof.get('verified'))).lower()}",
            flush=True,
        )

    report = {
        "schemaVersion": 1,
        "method": "provider-v3-bounded-batch-diagnostic",
        "publicationGate": False,
        "diagnosticOnly": True,
        "providerCount": EXPECTED,
        "startIndex": start,
        "endIndex": end,
        "requestedCount": count,
        "processedCount": len(rows),
        "hardFailureCount": len(hard_failures),
        "hardFailures": hard_failures,
        "terminalOnlyCount": len(terminal_only),
        "terminalOnly": terminal_only,
        "finalVerifiedCount": len(final_verified),
        "finalVerified": final_verified,
        "providers": rows,
    }
    write(report_path, report)
    print(
        "FIELD_PROVIDER_BATCH_COMPLETE "
        f"start={start} end={end} processed={len(rows)} "
        f"hard_failures={len(hard_failures)} terminal={len(terminal_only)} "
        f"final_verified={len(final_verified)}",
        flush=True,
    )
    if hard_failures:
        print("FIELD_PROVIDER_BATCH_FAILURES providers=" + ",".join(hard_failures), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
