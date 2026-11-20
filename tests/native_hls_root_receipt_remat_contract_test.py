#!/usr/bin/env python3
"""V30 must compile only with a byte-pinned V29-negative Brain experiment."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_candidate_remat as native
from provider_base_store import build_provider_data_model

ledger = json.loads((ROOT / "automation/brain-native-candidate-experiments.json").read_text())
assert ledger["authority"] == "candidate-only"
rows = [
    row for row in ledger["rows"]
    if row.get("providerId") == "french-manga"
    and any(a.get("candidateRunId") == "44671941015"
            and a.get("candidateVerdict") == "candidate_zero_stream"
            for a in row.get("candidateAttempts") or [])
]
assert len(rows) == 1, "historical exact-byte V29 negative must be retained"
original = rows[0]
attempt = next(a for a in original["candidateAttempts"] if a["candidateRunId"] == "44671941015")
assert attempt["candidateExecutionObserved"] and attempt["candidateRestoredObserved"]
assert not attempt["candidateDecodedVideoObserved"]

payload = {
    "schemaVersion": 1,
    "experimentType": "native-hls-master-receipt-v30",
    "providerId": original["providerId"],
    "fixture": original["fixture"],
    "requestType": original["requestType"],
    "sourceNiakvioSha": original["sourceNiakvioSha"],
    "sourceRunId": original["sourceRunId"],
    "providerArtifactSha256": original["providerArtifactSha256"],
    "officialClientSha": original["officialClientSha"],
    "runtimeScope": "native-blocking-fetch",
    "evidencePattern": "same-hls-root-2xx-then-403-pre-player",
    "priorCandidateRunId": attempt["candidateRunId"],
    "priorCandidateSourceSha": attempt["candidateSourceSha"],
    "priorCandidateJsSha256": attempt["candidateJsSha256"],
    "candidateOnly": True, "generatedByBrain": True, "modelExecuted": False,
    "proofAuthority": False, "publicationAuthority": False,
    "nativePlaybackAuthority": False, "providerMutationAuthority": False,
}
payload["experimentFingerprint"] = hashlib.sha256(
    json.dumps({k: payload[k] for k in native.V30_FINGERPRINT_KEYS},
               sort_keys=True, separators=(",", ":")).encode("ascii")
).hexdigest()

validated = native._validate_brain_hls_receipt_experiment(
    json.dumps(payload), "french-manga", original["providerArtifactSha256"]
)
assert validated["experimentType"] == "native-hls-master-receipt-v30"
assert validated["experimentFingerprint"] == payload["experimentFingerprint"]
assert native.V30_MARKER in native.REQUIRED_MARKERS

# Catch the source->DATA serialization gap, not merely a compiled marker.
# The exact candidate fingerprint must survive ProviderBase normalization;
# production publication rejects this candidate-only field.
prev_context = os.environ.get("NUVIO_PROVIDER_V3_CONTEXT")
try:
    os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "workspace"
    model = build_provider_data_model(
        "french-manga", {"name": "French Manga", "supportedTypes": ["anime"]},
        provider_model={"nativeHlsRootReceiptV30": {
            "experimentFingerprint": payload["experimentFingerprint"],
        }},
    )
    assert model["nativeHlsRootReceiptV30"] == {
        "experimentFingerprint": payload["experimentFingerprint"]
    }
    ordinary = build_provider_data_model("french-manga", {"supportedTypes": ["anime"]})
    assert "nativeHlsRootReceiptV30" not in ordinary
    for bad in (
        {"experimentFingerprint": "not-a-sha"},
        {"experimentFingerprint": payload["experimentFingerprint"], "url": "https://secret.example"},
        {"experimentFingerprint": payload["experimentFingerprint"].upper()},
    ):
        try:
            build_provider_data_model(
                "french-manga", provider_model={"nativeHlsRootReceiptV30": bad},
            )
        except ValueError:
            pass
        else:
            raise AssertionError("invalid/private V30 DATA was accepted")
    os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "release"
    try:
        build_provider_data_model(
            "french-manga", provider_model={"nativeHlsRootReceiptV30": {
                "experimentFingerprint": payload["experimentFingerprint"]
            }},
        )
    except ValueError:
        pass
    else:
        raise AssertionError("V30 must not be allowed in production release DATA")
finally:
    if prev_context is None:
        os.environ.pop("NUVIO_PROVIDER_V3_CONTEXT", None)
    else:
        os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = prev_context

for key, replacement in [
    ("providerArtifactSha256", "f" * 64),
    ("sourceNiakvioSha", "c" * 40),
    ("priorCandidateRunId", "44671941016"),
    ("priorCandidateJsSha256", "0" * 64),
    ("publicationAuthority", True),
    ("modelExecuted", True),
    ("experimentFingerprint", "0" * 64),
]:
    tampered = dict(payload)
    tampered[key] = replacement
    try:
        native._validate_brain_hls_receipt_experiment(
            json.dumps(tampered), "french-manga", original["providerArtifactSha256"]
        )
    except ValueError:
        pass
    else:
        raise AssertionError("tampered V30 experiment accepted: " + key)

with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "ledger.json"
    cloned = copy.deepcopy(ledger)
    chosen = next(row for row in cloned["rows"] if row.get("providerId") == "french-manga")
    chosen["candidateFollowUpExperiments"] = [{**payload, "brainSha": "f" * 40}]
    path.write_text(json.dumps(cloned), encoding="utf-8")
    original_path = native.BRAIN_LEDGER
    try:
        native.BRAIN_LEDGER = path
        selected = native._select_persisted_brain_hls_receipt_experiment(
            "french-manga", original["providerArtifactSha256"]
        )
        assert selected["experimentFingerprint"] == payload["experimentFingerprint"]
        assert selected["brainSha"] == "f" * 40
        chosen["candidateAttempts"][0]["candidateRestoredObserved"] = False
        path.write_text(json.dumps(cloned), encoding="utf-8")
        try:
            native._select_persisted_brain_hls_receipt_experiment(
                "french-manga", original["providerArtifactSha256"]
            )
        except ValueError:
            pass
        else:
            raise AssertionError("unrestored historical candidate accepted")
    finally:
        native.BRAIN_LEDGER = original_path

materializer = (ROOT / "scripts/materialize_provider_v3_one.py").read_text()
assert "NIAKVIO_NATIVE_BRAIN_HLS_ROOT_RECEIPT" in materializer
assert "apply_native_hls_receipt(base)" in materializer
assert "brainCandidateHlsRootReceipt" in materializer
print("native V30 Brain experiment validation, historical-restored witness and workspace wiring passed")
