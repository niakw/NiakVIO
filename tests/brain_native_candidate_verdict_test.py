#!/usr/bin/env python3
from __future__ import annotations
import base64
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from persist_brain_native_candidate_verdict import persist_verdict

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    artifacts = root / "artifacts"
    artifacts.mkdir()
    ledger = root / "ledger.json"
    provider = "french-manga"
    fingerprint = "a" * 64
    baseline = "b" * 64
    candidate = "c" * 64
    source = "d" * 40
    run_id = "44670000001"
    provider64 = base64.b64encode(provider.encode()).decode().rstrip("=")
    ledger.write_text(json.dumps({
        "schemaVersion": 1,
        "authority": "candidate-only",
        "publicationAuthority": False,
        "providerMutationAuthority": False,
        "rows": [{
            "experimentFingerprint": fingerprint,
            "providerId": provider,
            "fixture": "jujutsu-kaisen-s01e01",
            "requestType": "anime",
            "providerArtifactSha256": baseline,
            "candidateOnly": True,
            "generatedByBrain": True,
            "proofAuthority": False,
            "publicationAuthority": False,
            "nativePlaybackAuthority": False,
            "providerMutationAuthority": False,
        }],
    }), encoding="utf-8")
    (artifacts / "native-candidate-remat-proof.json").write_text(json.dumps({
        "provider": provider,
        "sourceNiakvioSha": source,
        "publishedBaselineJsSha256": baseline,
        "candidateJsSha256": candidate,
        "candidateByteChanged": True,
        "generatedByBrain": True,
        "generatedByProviderBase": True,
        "brainExperimentFingerprint": fingerprint,
        "brainObservedBaselineJsSha256": baseline,
        "officialTvTestAssetByteMatched": True,
        "productionPlaybackVerified": False,
        "publicationAllowed": False,
    }), encoding="utf-8")
    (artifacts / "tv-native-corpus-test.log").write_text(
        f"FIELD_NATIVE_CANDIDATE_RUNTIME_BYTE_CHECK client=tv provider64={provider64} sha256={candidate} matched=true runtime=official_plugin_manager production_playback_authority=false\n"
        f"FIELD_NATIVE_CANDIDATE_RUNTIME_RESULT client=tv provider64={provider64} sha256={candidate} count=1 runtime=official_plugin_manager authority=diagnostic_only\n"
        f"FIELD_NATIVE_CANDIDATE_RESTORED client=tv provider64={provider64} exact_previous_state=true diagnostic_only=true\n",
        encoding="utf-8",
    )
    (artifacts / "tv-native-corpus-test-brain.json").write_text(json.dumps({
        "schemaVersion": 5,
        "extractionHealthyObservations": [{
            "client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
            "requestType": "anime", "returnedCount": 1,
        }],
        "observations": [{
            "client": "tv", "provider": provider, "fixture": "jujutsu-kaisen-s01e01",
            "requestType": "anime", "observationLayer": "player", "failureClass": "healthy",
            "playerVideoFormatObserved": True,
            "playerAudioTrackLanguages": "fr",
            "transportAudioTrackLanguages": "",
            "playerSubtitleTrackLanguages": "fr,en",
            "transportSubtitleTrackLanguages": "",
        }],
    }), encoding="utf-8")

    attempt = persist_verdict(artifacts, ledger, source, run_id)
    assert attempt["candidateVerdict"] == "candidate_terminal_decode_observed"
    assert attempt["candidateExecutionObserved"] is True
    assert attempt["candidateRestoredObserved"] is True
    assert attempt["candidateExtractionNonEmpty"] is True
    assert attempt["candidateTerminalReaderHealthy"] is True
    assert attempt["candidateDecodedVideoObserved"] is True
    assert attempt["candidateFrAudioObserved"] is True
    updated = json.loads(ledger.read_text(encoding="utf-8"))
    row = updated["rows"][0]
    assert row["lastCandidateValidatedRepair"] is False
    assert row["candidateAttempts"][-1]["publicationAllowed"] is False
    assert "http://" not in ledger.read_text(encoding="utf-8")
    assert "https://" not in ledger.read_text(encoding="utf-8")

print("Brain native candidate verdict persistence contract passed")
