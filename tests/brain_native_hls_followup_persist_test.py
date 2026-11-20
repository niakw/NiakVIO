#!/usr/bin/env python3
"""Brain V30 follow-up storage is exact, idempotent, bounded and non-authoritative."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_native_candidate_remat import V30_FINGERPRINT_KEYS
from persist_brain_native_hls_followup import persist

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    ledger_path = root / "ledger.json"
    route_path = root / "route.json"
    provider = "french-manga"
    baseline = "b" * 64
    source = "a" * 40
    run_id = "44669003629"
    native_candidate_run = "44671941015"
    native_candidate_source = "c" * 40
    previous_js = "d" * 64
    candidate = {
        "schemaVersion": 1,
        "experimentType": "native-hls-master-receipt-v30",
        "providerId": provider,
        "fixture": "jujutsu-kaisen-s01e01",
        "requestType": "anime",
        "sourceNiakvioSha": source,
        "sourceRunId": run_id,
        "providerArtifactSha256": baseline,
        "officialClientSha": "e" * 40,
        "runtimeScope": "native-blocking-fetch",
        "evidencePattern": "same-hls-root-2xx-then-403-pre-player",
        "priorCandidateRunId": native_candidate_run,
        "priorCandidateSourceSha": native_candidate_source,
        "priorCandidateJsSha256": previous_js,
        "candidateOnly": True, "generatedByBrain": True, "modelExecuted": False,
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False,
    }
    candidate["experimentFingerprint"] = hashlib.sha256(
        json.dumps({k: candidate[k] for k in V30_FINGERPRINT_KEYS},
                   separators=(",", ":"), sort_keys=True).encode("ascii")
    ).hexdigest()
    parent = {
        "providerId": provider, "fixture": candidate["fixture"],
        "sourceNiakvioSha": source, "sourceRunId": run_id,
        "providerArtifactSha256": baseline, "officialClientSha": candidate["officialClientSha"],
        "experimentFingerprint": "f" * 64,
        "candidateAttempts": [{
            "candidateRunId": native_candidate_run,
            "candidateSourceSha": native_candidate_source,
            "candidateJsSha256": previous_js,
            "candidateExecutionObserved": True,
            "candidateRestoredObserved": True,
            "candidateDecodedVideoObserved": False,
            "candidateVerdict": "candidate_zero_stream",
            "validatedRepair": False, "publicationAllowed": False,
        }],
        "candidateOnly": True, "generatedByBrain": True,
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False,
    }
    ledger = {
        "authority": "candidate-only", "schemaVersion": 1,
        "publicationAuthority": False, "providerMutationAuthority": False,
        "rows": [parent],
    }
    plan = {
        "schemaVersion": 1, "authority": "android-tv-brain-route-plan-only",
        "modelExecuted": False, "publicationAuthority": False,
        "providerMutationAuthority": False,
        "sourceNiakvioSha": source, "nativeRunId": run_id,
        "routes": [{
            "provider": provider, "fixture": candidate["fixture"],
            "mode": "llm_diagnose", "targetLayer": "core",
            "strategy": "reuse_successful_hls_root_across_core_validation",
            "followupCoreExperiment": candidate,
        }],
    }
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    route_path.write_text(json.dumps(plan), encoding="utf-8")
    brain_sha = "1" * 40
    def call():
        return persist(route_path, ledger_path, brain_sha,
                       native_candidate_run, native_candidate_source)
    first = call()
    assert first["status"] == "persisted"
    updated = json.loads(ledger_path.read_text(encoding="utf-8"))["rows"][0]
    assert updated["candidateAttempts"] == parent["candidateAttempts"]
    assert updated["candidateFollowUpExperiments"][0]["brainSha"] == brain_sha
    saved = ledger_path.read_bytes()
    assert call()["status"] == "already_persisted"
    assert ledger_path.read_bytes() == saved
    updated["candidateFollowUpExperiments"][0]["candidateAttempts"] = [
        {"candidateRunId": "44710000000", "candidateVerdict": "candidate_zero_stream"}
    ]
    ledger_path.write_text(json.dumps({"authority": "candidate-only", "schemaVersion": 1,
        "publicationAuthority": False, "providerMutationAuthority": False, "rows": [updated]}), encoding="utf-8")
    assert call()["status"] == "already_executed"
    malicious = dict(plan)
    malicious["routes"] = [{**plan["routes"][0], "followupCoreExperiment": {**candidate, "providerMutationAuthority": True}}]
    route_path.write_text(json.dumps(malicious), encoding="utf-8")
    try:
        call()
    except ValueError:
        pass
    else:
        raise AssertionError("forged follow-up authority accepted")
print("Brain V30 source-pinned follow-up persistence, deduplication and security tests passed")
