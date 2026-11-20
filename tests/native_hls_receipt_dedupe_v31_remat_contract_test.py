#!/usr/bin/env python3
"""V31 must be a new source-pinned Brain experiment after restored V30 zero."""
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
from provider_base_store import build_clean_provider_seed, build_provider_data_model
from provider_patches.native_hls_root_receipt_dedupe_v31 import MARKER, apply, validate

ledger = json.loads((ROOT / "automation/brain-native-candidate-experiments.json").read_text())
parents = [
    x for x in ledger.get("rows") or []
    if x.get("providerId") == "french-manga"
    and x.get("providerArtifactSha256")
    and any(y.get("experimentType") == "native-hls-master-receipt-v30"
            and any(a.get("candidateRunId") == "44710894643"
                    and a.get("candidateVerdict") == "candidate_zero_stream"
                    for a in y.get("candidateAttempts") or [])
            for y in x.get("candidateFollowUpExperiments") or [])
]
assert len(parents) == 1, "source-pinned V30 negative witness must remain persisted"
parent = parents[0]
v30 = next(x for x in parent["candidateFollowUpExperiments"]
           if x.get("experimentType") == "native-hls-master-receipt-v30")
attempt = next(x for x in v30["candidateAttempts"]
               if x.get("candidateRunId") == "44710894643")
assert attempt["candidateExecutionObserved"] is True
assert attempt["candidateRestoredObserved"] is True
assert attempt["candidateDecodedVideoObserved"] is False
assert attempt["validatedRepair"] is False

plan = {
    "schemaVersion": 1,
    "experimentType": "native-hls-master-receipt-dedupe-v31",
    "providerId": parent["providerId"], "fixture": parent["fixture"],
    "requestType": parent["requestType"],
    "sourceNiakvioSha": parent["sourceNiakvioSha"],
    "sourceRunId": str(parent["sourceRunId"]),
    "providerArtifactSha256": parent["providerArtifactSha256"],
    "officialClientSha": parent["officialClientSha"],
    "runtimeScope": "native-blocking-fetch",
    "evidencePattern": native.V31_EVIDENCE_PATTERN,
    "parentExperimentFingerprint": v30["experimentFingerprint"],
    "priorCandidateRunId": attempt["candidateRunId"],
    "priorCandidateSourceSha": attempt["candidateSourceSha"],
    "priorCandidateJsSha256": attempt["candidateJsSha256"],
    "candidateOnly": True, "generatedByBrain": True,
    "modelExecuted": False, "proofAuthority": False,
    "publicationAuthority": False, "nativePlaybackAuthority": False,
    "providerMutationAuthority": False,
}
plan["experimentFingerprint"] = hashlib.sha256(json.dumps(
    {key: plan[key] for key in native.V31_FINGERPRINT_KEYS},
    sort_keys=True, separators=(",", ":"),
).encode("ascii")).hexdigest()

def validate_plan(value: dict) -> dict:
    return native._validate_brain_hls_dedupe_experiment(
        json.dumps(value), parent["providerId"], parent["providerArtifactSha256"]
    )

checked = validate_plan(plan)
assert checked["experimentFingerprint"] == plan["experimentFingerprint"]
assert native.V31_MARKER == MARKER
assert MARKER in native.REQUIRED_MARKERS
assert "native-hls-master-receipt-dedupe-v31" == checked["experimentType"]

for key, replacement in (
    ("parentExperimentFingerprint", "a"*64),
    ("priorCandidateRunId", "44710894644"),
    ("priorCandidateJsSha256", "a"*64),
    ("priorCandidateSourceSha", "f"*40),
    ("sourceNiakvioSha", "f"*40),
    ("officialClientSha", "f"*40),
    ("providerArtifactSha256", "f"*64),
    ("modelExecuted", True),
    ("publicationAuthority", True),
    ("experimentFingerprint", "a"*64),
):
    changed = {**plan, key: replacement}
    try:
        validate_plan(changed)
    except ValueError:
        pass
    else:
        raise AssertionError("forged V31 witness accepted: " + key)
try:
    validate_plan({**plan, "privateSignedHls": "https://invalid.test?token=secret"})
except ValueError:
    pass
else:
    raise AssertionError("V31 accepted private signed HLS URL")

with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "ledger.json"
    copy_ledger = copy.deepcopy(ledger)
    copy_parent = next(x for x in copy_ledger["rows"] if x["providerId"] == parent["providerId"])
    copy_parent["candidateFollowUpExperiments"].append({**plan, "brainSha": "1"*40})
    path.write_text(json.dumps(copy_ledger), encoding="utf-8")
    original_ledger = native.BRAIN_LEDGER
    try:
        native.BRAIN_LEDGER = path
        chosen = native._select_persisted_brain_hls_dedupe_experiment(
            parent["providerId"], parent["providerArtifactSha256"]
        )
        assert chosen["experimentFingerprint"] == plan["experimentFingerprint"]
        copy_parent["candidateFollowUpExperiments"][-1]["candidateAttempts"] = [{
            "candidateRunId": "44710000001",
            "candidateVerdict": "candidate_zero_stream",
        }]
        path.write_text(json.dumps(copy_ledger), encoding="utf-8")
        try:
            native._select_persisted_brain_hls_dedupe_experiment(
                parent["providerId"], parent["providerArtifactSha256"]
            )
        except ValueError:
            pass
        else:
            raise AssertionError("V31 attempted to rerun an already executed candidate")
    finally:
        native.BRAIN_LEDGER = original_ledger

base = build_clean_provider_seed("v31-source-pinned")
candidate = apply(base)
validate(candidate)
assert base != candidate
assert candidate.decode().count(MARKER) == 1

original_context = os.environ.get("NUVIO_PROVIDER_V3_CONTEXT")
try:
    os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "workspace"
    model = build_provider_data_model("french-manga",
        provider_model={"nativeHlsReceiptDedupeV31": {
            "experimentFingerprint": plan["experimentFingerprint"]
        }})
    assert model["nativeHlsReceiptDedupeV31"]["experimentFingerprint"] == plan["experimentFingerprint"]
    os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = "release"
    try:
        build_provider_data_model("french-manga", provider_model={
            "nativeHlsReceiptDedupeV31": {"experimentFingerprint": plan["experimentFingerprint"]}
        })
    except ValueError:
        pass
    else:
        raise AssertionError("candidate V31 fingerprint can leak into production DATA")
finally:
    if original_context is None:
        os.environ.pop("NUVIO_PROVIDER_V3_CONTEXT", None)
    else:
        os.environ["NUVIO_PROVIDER_V3_CONTEXT"] = original_context

materializer = (ROOT / "scripts/materialize_provider_v3_one.py").read_text()
assert "NIAKVIO_NATIVE_BRAIN_HLS_RECEIPT_DEDUPE" in materializer
assert "apply_native_hls_dedupe(base)" in materializer
assert "nativeHlsReceiptDedupeV31" in materializer
print("V31 Brain source-pinned V30 negative, ProviderBase candidate-only materialization and no-repeat contract passed")
