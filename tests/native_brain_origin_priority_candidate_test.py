#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_candidate_remat as candidate
from provider_base_store import build_clean_provider_seed, build_provider_data_model
from materialize_provider_v3_one import _apply_native_brain_origin_priority_candidate

provider = "demo-provider"
source_sha = "a" * 40
payload = {
    "schemaVersion": 1,
    "experimentType": "native-blocking-player-origin-priority",
    "providerId": provider,
    "fixture": "interstellar",
    "requestType": "movie",
    "sourceNiakvioSha": source_sha,
    "sourceRunId": "12345",
    "providerArtifactSha256": "b" * 64,
    "officialClientSha": "c" * 40,
    "runtimeScope": "native-blocking-fetch",
    "preferredHosts": ["fast.example"],
    "deprioritizedHosts": ["slow.example"],
    "evidencePattern": "player-5xx-then-alternate-2xx-then-hls-2xx-near-budget-zero",
    "candidateOnly": True,
    "generatedByBrain": True,
    "proofAuthority": False,
    "publicationAuthority": False,
    "nativePlaybackAuthority": False,
    "providerMutationAuthority": False,
}
keys = (
    "experimentType", "providerId", "fixture", "requestType",
    "sourceNiakvioSha", "sourceRunId", "providerArtifactSha256",
    "officialClientSha", "runtimeScope", "preferredHosts",
    "deprioritizedHosts", "evidencePattern",
)
payload["experimentFingerprint"] = hashlib.sha256(
    json.dumps({key: payload[key] for key in keys},
               sort_keys=True, separators=(",", ":")).encode("ascii")
).hexdigest()
validated = candidate._validate_brain_experiment(json.dumps(payload), provider, source_sha)
assert validated["preferredHosts"] == ["fast.example"]
assert validated["deprioritizedHosts"] == ["slow.example"]

# Persisted candidate authority follows exact observed bundle bytes, not the
# necessarily newer V29 source checkout SHA.
persisted = {**payload, "brainSha": "e" * 40}
persisted["sourceNiakvioSha"] = "d" * 40
persisted["experimentFingerprint"] = hashlib.sha256(
    json.dumps({key: persisted[key] for key in keys},
               sort_keys=True, separators=(",", ":")).encode("ascii")
).hexdigest()
validated_persisted = candidate._validate_brain_experiment(
    json.dumps(persisted), provider, None
)
assert validated_persisted["sourceNiakvioSha"] == "d" * 40
assert validated_persisted["brainSha"] == "e" * 40

model = build_provider_data_model(
    provider,
    {"name": "Demo", "supportedTypes": ["movie"]},
    provider_model={
        "knownSite": "https://catalog.example",
        "nativeBlockingOriginPriority": {
            "preferredHosts": validated["preferredHosts"],
            "deprioritizedHosts": validated["deprioritizedHosts"],
            "experimentFingerprint": validated["experimentFingerprint"],
        },
    },
)
assert model["nativeBlockingOriginPriority"]["preferredHosts"] == ["fast.example"]
base = build_clean_provider_seed(provider)
production_text = base.decode("utf-8")
assert "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29" not in production_text
candidate_text = _apply_native_brain_origin_priority_candidate(base).decode("utf-8")
assert "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29" in candidate_text
assert "_spv29NativeBlockingQueueScore" in candidate_text
assert "fast.example" not in candidate_text and "slow.example" not in candidate_text

for mutation in (
    {**payload, "sourceNiakvioSha": "d" * 40},
    {**payload, "publicationAuthority": True},
    {**payload, "experimentFingerprint": "0" * 64},
):
    try:
        candidate._validate_brain_experiment(json.dumps(mutation), provider, source_sha)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid Brain candidate experiment accepted")

print("native Brain origin-priority candidate contract passed")
