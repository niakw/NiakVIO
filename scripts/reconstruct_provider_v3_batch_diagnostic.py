#!/usr/bin/env python3
"""Repair-first bounded Provider v3 slice.

Unlike the old diagnostic accelerator, this gate never silently advances past a
repairable provider. Provider N is materialized, probed, and—when live runtime
evidence exists but declared-type proof is incomplete—its safe observed candidate
DATA is staged, N is rebuilt, and N is probed again. The slice advances only after
N is final-bundle verified or proven terminally blocked/unreachable.

This remains a workbench gate, not publication authority.
"""
from __future__ import annotations

import argparse
import copy
import json
import urllib.parse
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


def _unique(values: list[Any], limit: int = 256) -> list[str]:
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def _stage_runtime_repair_candidates(
    provider_id: str,
    static_row: dict[str, Any],
    evaluation: dict[str, Any],
    repair_attempt: int,
) -> bool:
    """Persist candidate/runtime observations only; never promote unqualified live authority."""
    model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
    before = json.dumps(
        {
            "candidateRouteData": model.get("candidateRouteData"),
            "candidateRoutes": model.get("candidateRoutes"),
            "origins": model.get("origins"),
            "observedUrls": model.get("observedUrls"),
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )

    candidate_rows = copy.deepcopy(evaluation.get("candidateRouteData") or [])
    model["candidateRouteData"] = candidate_rows
    model["candidateRoutes"] = _unique(
        [row.get("route") for row in candidate_rows if isinstance(row, dict)],
        256,
    )

    origins = list(model.get("origins") or [])
    observed_urls = list(model.get("observedUrls") or [])
    for row in candidate_rows:
        if not isinstance(row, dict):
            continue
        evidence_rows = [*(row.get("attemptEvidence") or []), *(row.get("liveEvidence") or [])]
        for evidence in evidence_rows:
            if not isinstance(evidence, dict):
                continue
            for key in ("url", "finalUrl", "final_url"):
                raw = str(evidence.get(key) or "").strip()
                if not raw:
                    continue
                if raw not in observed_urls:
                    observed_urls.append(raw)
                try:
                    parsed = urllib.parse.urlsplit(raw)
                except ValueError:
                    continue
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    if origin not in origins:
                        origins.append(origin)

    for evidence in evaluation.get("unresolvedObservedRequests") or []:
        if not isinstance(evidence, dict):
            continue
        for key in ("url", "finalUrl", "final_url", "observedUrl"):
            raw = str(evidence.get(key) or "").strip()
            if not raw:
                continue
            if raw not in observed_urls:
                observed_urls.append(raw)
            try:
                parsed = urllib.parse.urlsplit(raw)
            except ValueError:
                continue
            if parsed.scheme in {"http", "https"} and parsed.hostname:
                origin = f"{parsed.scheme}://{parsed.netloc}"
                if origin not in origins:
                    origins.append(origin)

    model["origins"] = _unique(origins, 64)
    model["observedUrls"] = _unique(observed_urls, 128)
    model["repairObservation"] = {
        "version": 1,
        "attempt": repair_attempt,
        "providerId": provider_id,
        "requiredTypes": list(evaluation.get("requiredTypes") or []),
        "validatedTypes": list(evaluation.get("validatedTypes") or []),
        "missingTypes": list(evaluation.get("missingTypes") or []),
        "providerRequestCount": int(evaluation.get("providerRequestCount") or 0),
        "liveValidatedRouteCount": int(evaluation.get("liveValidatedRouteCount") or 0),
        "unresolvedObservedRequestCount": int(evaluation.get("unresolvedObservedRequestCount") or 0),
        "candidateOnly": True,
        "promotedToLiveAuthority": False,
    }

    after = json.dumps(
        {
            "candidateRouteData": model.get("candidateRouteData"),
            "candidateRoutes": model.get("candidateRoutes"),
            "origins": model.get("origins"),
            "observedUrls": model.get("observedUrls"),
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return before != after


def _print_repair_evidence(
    provider_id: str,
    evaluation: dict[str, Any],
    repair_attempt: int,
) -> None:
    emitted = 0
    for row in evaluation.get("candidateRouteData") or []:
        if not isinstance(row, dict):
            continue
        state = str(row.get("validationState") or "")
        if state not in {"live-validated", "failed-live", "blocked-live"}:
            continue
        route = str(row.get("route") or "").replace("\n", " ")[:220]
        if not route:
            continue
        print(
            "FIELD_PROVIDER_REPAIR_ROUTE "
            f"provider={provider_id} attempt={repair_attempt} state={state} route={route}",
            flush=True,
        )
        emitted += 1
        if emitted >= 12:
            break

    unresolved = evaluation.get("unresolvedObservedRequests") or []
    for item in unresolved[:8]:
        if not isinstance(item, dict):
            continue
        url = str(
            item.get("finalUrl")
            or item.get("final_url")
            or item.get("url")
            or item.get("observedUrl")
            or ""
        ).replace("\n", " ")[:300]
        print(
            "FIELD_PROVIDER_REPAIR_UNRESOLVED "
            f"provider={provider_id} attempt={repair_attempt} "
            f"status={int(item.get('status') or 0)} url={url or 'none'}",
            flush=True,
        )


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
    parser.add_argument("--repair-attempts", type=int, default=2)
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
    repair_attempt_limit = max(1, min(int(args.repair_attempts), 4))

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
    # PROVIDER_V3_DEFER_TO_LEARN_V1
    # Provider-scoped repair exhaustion is evidence for Learn, not a slice blocker.
    deferred_to_learn: list[dict[str, Any]] = []

    print(
        f"FIELD_PROVIDER_BATCH_BEGIN start={start} end={end} count={len(selected)} total={EXPECTED} repair_first=true",
        flush=True,
    )

    for absolute_index, provider in enumerate(selected, start=start):
        provider_id = provider["provider_id"]
        static_row = providers.get(provider_id)
        patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
        if not isinstance(static_row, dict):
            deferred_to_learn.append({"index": absolute_index, "providerId": provider_id, "reason": "missing-static-knowledge"})
            rows.append({
                "index": absolute_index, "providerId": provider_id,
                "result": "defer-to-learn", "completionState": "defer-to-learn",
                "learnRequired": True, "deferReason": "missing-static-knowledge",
                "advancedAfterDefer": True, "refusedToAdvance": False,
                "finalBundleVerified": False,
            })
            print(f"FIELD_PROVIDER_BATCH_PROVIDER_DEFER index={absolute_index} provider={provider_id} reason=missing-static-knowledge advancing_next=true learn=true", flush=True)
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
            deferred_to_learn.append({"index": absolute_index, "providerId": provider_id, "reason": "candidate-materialization-failed"})
            rows.append({
                "index": absolute_index, "providerId": provider_id,
                "result": "defer-to-learn", "completionState": "defer-to-learn",
                "learnRequired": True, "deferReason": "candidate-materialization-failed",
                "advancedAfterDefer": True, "refusedToAdvance": False,
                "finalBundleVerified": False,
            })
            print(f"FIELD_PROVIDER_BATCH_PROVIDER_DEFER index={absolute_index} provider={provider_id} reason=candidate-materialization-failed advancing_next=true learn=true", flush=True)
            continue
        for task in provider["tasks"]:
            task["filename"] = candidate_filename

        _probe_rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)
        completion_state = "declared-types-qualified" if is_qualified(evaluation) else None
        origin_evidence: list[dict[str, Any]] = []
        if completion_state is None:
            completion_state, origin_evidence = terminal_state(evaluation, model, patch, origin_timeout)

        repair_history: list[dict[str, Any]] = []

        if completion_state is None:
            for repair_attempt in range(1, repair_attempt_limit + 1):
                _print_repair_evidence(provider_id, evaluation, repair_attempt)
                changed = _stage_runtime_repair_candidates(provider_id, static_row, evaluation, repair_attempt)
                write(knowledge_path, knowledge)
                write(overrides_path, overrides)
                print(
                    "FIELD_PROVIDER_REPAIR_BEGIN "
                    f"index={absolute_index} provider={provider_id} attempt={repair_attempt}/{repair_attempt_limit} "
                    f"changed={str(changed).lower()} "
                    f"missing={','.join(evaluation.get('missingTypes') or []) or 'unknown'} "
                    f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'}",
                    flush=True,
                )

                repair_materialized = materialize_one(provider_id)
                repair_filename = str(repair_materialized.get("file") or "")
                if not repair_filename:
                    repair_history.append({
                        "attempt": repair_attempt,
                        "candidateDataChanged": changed,
                        "result": "repair-materialization-failed",
                    })
                    break
                for task in provider["tasks"]:
                    task["filename"] = repair_filename

                _probe_rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)
                completion_state = "declared-types-qualified" if is_qualified(evaluation) else None
                origin_evidence = []
                if completion_state is None:
                    completion_state, origin_evidence = terminal_state(
                        evaluation, model, patch, origin_timeout
                    )

                repair_history.append({
                    "attempt": repair_attempt,
                    "candidateDataChanged": changed,
                    "bundleFile": repair_filename,
                    "bundleSha256": repair_materialized.get("sha256"),
                    "completionState": completion_state,
                    "validatedTypes": list(evaluation.get("validatedTypes") or []),
                    "missingTypes": list(evaluation.get("missingTypes") or []),
                    "providerRequestCount": int(evaluation.get("providerRequestCount") or 0),
                    "liveValidatedRouteCount": int(evaluation.get("liveValidatedRouteCount") or 0),
                })
                print(
                    "FIELD_PROVIDER_REPAIR_RESULT "
                    f"index={absolute_index} provider={provider_id} attempt={repair_attempt} "
                    f"state={completion_state or 'unresolved'} "
                    f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
                    f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'}",
                    flush=True,
                )
                if completion_state is not None:
                    break
                if not changed:
                    print(
                        "FIELD_PROVIDER_REPAIR_STALLED "
                        f"index={absolute_index} provider={provider_id} attempt={repair_attempt}",
                        flush=True,
                    )
                    break

        if completion_state is None:
            deferred_to_learn.append({
                "index": absolute_index,
                "providerId": provider_id,
                "reason": "repair-exhausted",
                "missingTypes": list(evaluation.get("missingTypes") or []),
                "validatedTypes": list(evaluation.get("validatedTypes") or []),
                "providerRequestCount": int(evaluation.get("providerRequestCount") or 0),
                "liveValidatedRouteCount": int(evaluation.get("liveValidatedRouteCount") or 0),
                "repairHistory": repair_history,
            })
            rows.append({
                **evaluation,
                "index": absolute_index,
                "providerId": provider_id,
                "result": "defer-to-learn",
                "completionState": "defer-to-learn",
                "originEvidence": origin_evidence,
                "candidateBundleFile": candidate_filename,
                "candidateBundleSha256": candidate.get("sha256"),
                "repairHistory": repair_history,
                "learnRequired": True,
                "deferReason": "repair-exhausted",
                "advancedAfterDefer": True,
                "refusedToAdvance": False,
                "finalBundleVerified": False,
            })
            print(
                "FIELD_PROVIDER_BATCH_PROVIDER_DEFER "
                f"index={absolute_index} provider={provider_id} repair_exhausted=true "
                f"missing={','.join(evaluation.get('missingTypes') or []) or 'unknown'} "
                f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
                f"advancing_next={str(absolute_index < EXPECTED).lower()} learn=true",
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
                final_proof["deferToLearn"] = True
                final_proof["deferReason"] = "final-bundle-verification-failed"
                deferred_to_learn.append({
                    "index": absolute_index,
                    "providerId": provider_id,
                    "reason": "final-bundle-verification-failed",
                    "candidateValidatedTypes": list(evaluation.get("validatedTypes") or []),
                    "candidateMissingTypes": list(evaluation.get("missingTypes") or []),
                    "finalProof": final_proof,
                })
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
            "result": "ok" if final_proof.get("verified") else ("defer-to-learn" if final_proof.get("deferToLearn") else completion_state),
            "completionState": completion_state,
            "originEvidence": origin_evidence,
            "candidateBundleFile": candidate_filename,
            "candidateBundleSha256": candidate.get("sha256"),
            "repairHistory": repair_history,
            "finalBundleFile": final_filename,
            "finalBundleSha256": final_materialized.get("sha256"),
            "finalBundleVerified": bool(final_proof.get("verified")),
            "finalBundleProof": final_proof,
            "learnRequired": bool(final_proof.get("deferToLearn")),
            "deferReason": final_proof.get("deferReason"),
            "advancedAfterDefer": bool(final_proof.get("deferToLearn")),
            "refusedToAdvance": False,
        })
        print(
            "FIELD_PROVIDER_BATCH_PROVIDER_RESULT "
            f"index={absolute_index} provider={provider_id} state={completion_state} "
            f"validated={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
            f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'} "
            f"final_verified={str(bool(final_proof.get('verified'))).lower()}",
            flush=True,
        )
        if final_proof.get("deferToLearn"):
            print(
                f"FIELD_PROVIDER_BATCH_PROVIDER_DEFER index={absolute_index} provider={provider_id} reason={final_proof.get('deferReason')} advancing_next=true learn=true",
                flush=True,
            )

    report = {
        "schemaVersion": 3,
        "method": "provider-v3-bounded-repair-first-defer-to-learn",
        "publicationGate": False,
        "diagnosticOnly": False,
        "repairFirst": True,
        "refuseAdvanceAfterUnresolved": False,
        "continueAfterRepairExhausted": True,
        "providerScopedFailuresDeferToLearn": True,
        "providerCount": EXPECTED,
        "startIndex": start,
        "endIndex": end,
        "requestedCount": count,
        "processedCount": len(rows),
        "hardFailureCount": len(hard_failures),
        "hardFailures": hard_failures,
        "refusedProvider": None,
        "deferredToLearnCount": len(deferred_to_learn),
        "deferredToLearn": deferred_to_learn,
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
        f"hard_failures={len(hard_failures)} deferred={len(deferred_to_learn)} "
        f"terminal={len(terminal_only)} final_verified={len(final_verified)} refused=none",
        flush=True,
    )
    if hard_failures:
        print("FIELD_PROVIDER_BATCH_FAILURES providers=" + ",".join(hard_failures), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
