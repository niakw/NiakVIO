#!/usr/bin/env python3
"""Persist one candidate-only V31 Core dedupe program after exact V30 zero.

The candidate is a Brain-selected *experiment*, not a decoded-media proof.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import prepare_native_candidate_remat as native

SHA40 = re.compile(r"[a-f0-9]{40}")
RUN = re.compile(r"[0-9]{8,20}")


def persist(
    route_path: Path, ledger_path: Path, brain_sha: str,
    v30_run: str, v30_source: str,
) -> dict[str, Any]:
    if not SHA40.fullmatch(brain_sha) or not SHA40.fullmatch(v30_source) or not RUN.fullmatch(v30_run):
        raise ValueError("V31 persistence requires exact Brain SHA and V30 run/source")
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
        raise ValueError("V31 plan or history has forbidden authority")
    routes = plan.get("routes") or []
    if len(routes) != 1 or not isinstance(routes[0], dict):
        raise ValueError("V31 accepts exactly one source-pinned provider route")
    row = routes[0]
    follow = row.get("followupCoreDedupeExperiment")
    if not follow:
        return {"status": "no_new_core_experiment"}
    if (
        row.get("strategy") != "preserve_hls_receipt_across_playback_key_dedupe"
        or row.get("targetLayer") != "core"
        or row.get("mode") != "deterministic_advisor"
        or row.get("provider") != follow.get("providerId")
        or row.get("fixture") != follow.get("fixture")
        or follow.get("sourceNiakvioSha") != plan.get("sourceNiakvioSha")
        or str(follow.get("sourceRunId") or "") != str(plan.get("nativeRunId") or "")
        or str(follow.get("priorCandidateRunId") or "") != v30_run
        or follow.get("priorCandidateSourceSha") != v30_source
    ):
        raise ValueError("V31 route is not the same executed V30 negative")
    matches = []
    for parent in (ledger.get("rows") or [])[:512]:
        if not isinstance(parent, dict) or any(
            str(parent.get(key) or "") != str(follow.get(key) or "")
            for key in ("providerId", "providerArtifactSha256", "sourceNiakvioSha",
                        "sourceRunId", "officialClientSha", "fixture", "requestType")
        ):
            continue
        for child in (parent.get("candidateFollowUpExperiments") or [])[:8]:
            if not isinstance(child, dict) or (
                child.get("experimentType") != "native-hls-master-receipt-v30"
                or child.get("experimentFingerprint") != follow.get("parentExperimentFingerprint")
            ):
                continue
            for a in child.get("candidateAttempts") or []:
                if (isinstance(a, dict)
                    and a.get("candidateExperimentType") == "native-hls-master-receipt-v30"
                    and str(a.get("candidateRunId") or "") == v30_run
                    and a.get("candidateSourceSha") == v30_source
                    and a.get("candidateJsSha256") == follow.get("priorCandidateJsSha256")
                    and a.get("candidateVerdict") == "candidate_zero_stream"
                    and a.get("candidateExecutionObserved") is True
                    and a.get("candidateRestoredObserved") is True
                    and a.get("candidateDecodedVideoObserved") is False
                    and a.get("validatedRepair") is False
                    and a.get("publicationAllowed") is False):
                    matches.append(parent)
    if len(matches) != 1:
        raise ValueError("V31 follow-up has no unique executed/restored V30 negative")
    parent = matches[0]
    original = native.BRAIN_LEDGER
    try:
        native.BRAIN_LEDGER = ledger_path
        selected = native._validate_brain_hls_dedupe_experiment(
            json.dumps(follow, sort_keys=True),
            follow["providerId"], parent["providerArtifactSha256"],
        )
    finally:
        native.BRAIN_LEDGER = original
    selected["brainSha"] = brain_sha
    existing = parent.get("candidateFollowUpExperiments") or []
    same = [x for x in existing if isinstance(x, dict)
            and x.get("experimentFingerprint") == selected["experimentFingerprint"]]
    if same:
        if any(x.get("candidateAttempts") for x in same):
            return {"status": "already_executed", "fingerprint": selected["experimentFingerprint"]}
        return {"status": "already_persisted", "fingerprint": selected["experimentFingerprint"]}
    if any(isinstance(x, dict) and x.get("experimentType") == native.V31_EXPERIMENT_TYPE
           for x in existing):
        raise ValueError("a distinct V31 plan already exists on these provider bytes")
    parent["candidateFollowUpExperiments"] = [*[
        x for x in existing[-3:] if isinstance(x, dict)
    ], selected][-4:]
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "persisted", "fingerprint": selected["experimentFingerprint"]}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--route", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--brain-sha", required=True)
    p.add_argument("--candidate-run-id", required=True)
    p.add_argument("--candidate-source-sha", required=True)
    a = p.parse_args()
    result = persist(
        a.route.resolve(), a.ledger.resolve(), a.brain_sha,
        a.candidate_run_id, a.candidate_source_sha,
    )
    print(f"FIELD_BRAIN_V31_FOLLOWUP status={result['status']} publication=false model_executed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
