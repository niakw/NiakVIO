#!/usr/bin/env python3
"""Persist one Brain-owned, source-pinned Core V30 follow-up after V29 failure.

No model execution, provider mutation, media fetch or production authority.
The ledger remains the durable owner of negative and future candidate attempts.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from prepare_native_candidate_remat import _validate_brain_hls_receipt_experiment

SHA40 = re.compile(r"[a-f0-9]{40}")
RUN = re.compile(r"[0-9]{8,20}")


def persist(
    route_path: Path, ledger_path: Path, brain_sha: str,
    native_candidate_run: str, native_candidate_source: str,
) -> dict[str, Any]:
    if not SHA40.fullmatch(brain_sha) or not SHA40.fullmatch(native_candidate_source):
        raise ValueError("follow-up requires SHA-pinned Brain and native source")
    if not RUN.fullmatch(native_candidate_run):
        raise ValueError("follow-up requires numeric native candidate run")
    plan = json.loads(route_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if (
        plan.get("schemaVersion") != 1
        or plan.get("authority") != "android-tv-brain-route-plan-only"
        or plan.get("modelExecuted") is not False
        or plan.get("providerMutationAuthority") is not False
        or plan.get("publicationAuthority") is not False
        or ledger.get("authority") != "candidate-only"
        or ledger.get("providerMutationAuthority") is not False
        or ledger.get("publicationAuthority") is not False
    ):
        raise ValueError("follow-up plan/ledger authority mismatch")
    routes = plan.get("routes") or []
    if len(routes) != 1 or not isinstance(routes[0], dict):
        raise ValueError("follow-up accepts exactly one routed provider")
    row = routes[0]
    followup = row.get("followupCoreExperiment")
    if not followup:
        return {"status": "no_new_core_experiment"}
    if (
        row.get("strategy") != "reuse_successful_hls_root_across_core_validation"
        or row.get("mode") != "llm_diagnose"
        or row.get("targetLayer") != "core"
        or row.get("provider") != followup.get("providerId")
        or row.get("fixture") != followup.get("fixture")
        or str(followup.get("priorCandidateRunId")) != native_candidate_run
        or followup.get("priorCandidateSourceSha") != native_candidate_source
        or followup.get("sourceNiakvioSha") != plan.get("sourceNiakvioSha")
        or str(followup.get("sourceRunId")) != str(plan.get("nativeRunId"))
    ):
        raise ValueError("follow-up is not the same V29 negative Core route")
    matches = [
        experiment for experiment in (ledger.get("rows") or [])
        if isinstance(experiment, dict)
        and experiment.get("providerId") == followup["providerId"]
        and experiment.get("providerArtifactSha256") == followup.get("providerArtifactSha256")
        and experiment.get("sourceNiakvioSha") == followup["sourceNiakvioSha"]
        and str(experiment.get("sourceRunId")) == str(followup.get("sourceRunId"))
        and any(
            isinstance(attempt, dict)
            and str(attempt.get("candidateRunId")) == native_candidate_run
            and attempt.get("candidateSourceSha") == native_candidate_source
            and attempt.get("candidateVerdict") == "candidate_zero_stream"
            and attempt.get("candidateExecutionObserved") is True
            and attempt.get("candidateRestoredObserved") is True
            and attempt.get("validatedRepair") is False
            and attempt.get("publicationAllowed") is False
            for attempt in experiment.get("candidateAttempts") or []
        )
    ]
    if len(matches) != 1:
        raise ValueError("follow-up has no unique executed/restored V29 negative")
    experiment = matches[0]
    # The validator checks exact experiment fingerprint and the actual ledger
    # witness. Temporarily scope it to the supplied isolated ledger.
    import prepare_native_candidate_remat as native
    previous = native.BRAIN_LEDGER
    try:
        native.BRAIN_LEDGER = ledger_path
        selected = _validate_brain_hls_receipt_experiment(
            json.dumps(followup, sort_keys=True), followup["providerId"],
            experiment["providerArtifactSha256"],
        )
    finally:
        native.BRAIN_LEDGER = previous
    selected["brainSha"] = brain_sha
    existing = experiment.get("candidateFollowUpExperiments") or []
    prior = [
        x for x in existing if isinstance(x, dict)
        and x.get("experimentFingerprint") == selected["experimentFingerprint"]
    ]
    if prior:
        if any((x.get("candidateAttempts") or []) for x in prior):
            return {"status": "already_executed", "fingerprint": selected["experimentFingerprint"]}
        return {"status": "already_persisted", "fingerprint": selected["experimentFingerprint"]}
    experiment["candidateFollowUpExperiments"] = [
        *[x for x in existing[-3:] if isinstance(x, dict)], selected,
    ][-4:]
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "persisted", "fingerprint": selected["experimentFingerprint"]}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--route", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--brain-sha", required=True)
    p.add_argument("--candidate-run-id", required=True)
    p.add_argument("--candidate-source-sha", required=True)
    args = p.parse_args()
    result = persist(
        args.route.resolve(), args.ledger.resolve(),
        args.brain_sha, args.candidate_run_id, args.candidate_source_sha,
    )
    print(f"FIELD_BRAIN_V30_FOLLOWUP status={result['status']} publication=false model_executed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
