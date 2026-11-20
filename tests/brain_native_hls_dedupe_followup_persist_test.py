#!/usr/bin/env python3
"""V31 Learning persists only one uniquely evidenced nested negative successor."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_native_candidate_remat import V31_FINGERPRINT_KEYS
from persist_brain_native_hls_dedupe_followup import persist

with tempfile.TemporaryDirectory() as d:
    p = Path(d)
    ledger_path, route_path = p / "ledger.json", p / "route.json"
    run = "44710894643"
    source = "f"*40
    provider, baseline = "french-manga", "b"*64
    original_sha, original_run = "a"*40, "44669003629"
    previous = "c"*64
    parent_fp = "d"*64
    plan = {
        "schemaVersion": 1,
        "experimentType": "native-hls-master-receipt-dedupe-v31",
        "providerId": provider, "fixture": "jujutsu-kaisen-s01e01",
        "requestType": "anime", "sourceNiakvioSha": original_sha,
        "sourceRunId": original_run, "providerArtifactSha256": baseline,
        "officialClientSha": "1"*40, "runtimeScope": "native-blocking-fetch",
        "evidencePattern": "v30-zero-after-same-hls-root-2xx-403-first-wins-dedupe",
        "parentExperimentFingerprint": parent_fp,
        "priorCandidateRunId": run, "priorCandidateSourceSha": source,
        "priorCandidateJsSha256": previous,
        "candidateOnly": True, "generatedByBrain": True, "modelExecuted": False,
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False,
    }
    plan["experimentFingerprint"] = hashlib.sha256(json.dumps({
        key: plan[key] for key in V31_FINGERPRINT_KEYS
    }, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    parent = {
        "providerId": provider, "providerArtifactSha256": baseline,
        "sourceNiakvioSha": original_sha, "sourceRunId": original_run,
        "officialClientSha": "1"*40, "fixture": plan["fixture"],
        "requestType": plan["requestType"],
        "candidateOnly": True, "generatedByBrain": True,
        "proofAuthority": False, "publicationAuthority": False,
        "nativePlaybackAuthority": False, "providerMutationAuthority": False,
        "candidateFollowUpExperiments": [{
            "experimentType": "native-hls-master-receipt-v30",
            "experimentFingerprint": parent_fp,
            "candidateOnly": True, "generatedByBrain": True,
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerMutationAuthority": False,
            "candidateAttempts": [{
                "candidateExperimentType": "native-hls-master-receipt-v30",
                "candidateRunId": run, "candidateSourceSha": source,
                "candidateJsSha256": previous, "candidateVerdict": "candidate_zero_stream",
                "candidateExecutionObserved": True, "candidateRestoredObserved": True,
                "candidateDecodedVideoObserved": False, "validatedRepair": False,
                "publicationAllowed": False,
            }],
        }],
    }
    ledger = {
        "authority": "candidate-only", "schemaVersion": 1,
        "publicationAuthority": False, "providerMutationAuthority": False,
        "rows": [parent],
    }
    route = {
        "schemaVersion": 1, "authority": "android-tv-brain-route-plan-only",
        "modelExecuted": False, "publicationAuthority": False,
        "providerMutationAuthority": False,
        "sourceNiakvioSha": original_sha, "nativeRunId": original_run,
        "routes": [{
            "provider": provider, "fixture": plan["fixture"],
            "mode": "deterministic_advisor", "targetLayer": "core",
            "strategy": "preserve_hls_receipt_across_playback_key_dedupe",
            "followupCoreDedupeExperiment": plan,
        }],
    }
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    route_path.write_text(json.dumps(route), encoding="utf-8")
    def call():
        return persist(route_path, ledger_path, "2"*40, run, source)
    assert call()["status"] == "persisted"
    result = json.loads(ledger_path.read_text(encoding="utf-8"))
    children = result["rows"][0]["candidateFollowUpExperiments"]
    assert len(children) == 2
    assert children[1]["brainSha"] == "2"*40
    assert children[0] == parent["candidateFollowUpExperiments"][0]
    snapshot = ledger_path.read_bytes()
    assert call()["status"] == "already_persisted"
    assert ledger_path.read_bytes() == snapshot
    result["rows"][0]["candidateFollowUpExperiments"][-1]["candidateAttempts"] = [
        {"candidateRunId": "44710000000", "candidateVerdict": "candidate_zero_stream"}
    ]
    ledger_path.write_text(json.dumps(result), encoding="utf-8")
    assert call()["status"] == "already_executed"
    for bad_key, bad_value in (
        ("providerMutationAuthority", True),
        ("experimentFingerprint", "e"*64),
        ("priorCandidateRunId", "44710894644"),
    ):
        malicious = dict(route)
        malicious["routes"] = [{**route["routes"][0],
            "followupCoreDedupeExperiment": {**plan, bad_key: bad_value}}]
        route_path.write_text(json.dumps(malicious), encoding="utf-8")
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("forged V31 plan accepted: " + bad_key)
    assert "https://" not in ledger_path.read_text(encoding="utf-8")
print("V31 follow-up nested Learning persistence and strict source SHA/fingerprint tests passed")
