#!/usr/bin/env python3
import hashlib
import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from persist_brain_native_candidate_experiments import canonical_fingerprint, persist

brain_sha = "b" * 40
base = {
    "schemaVersion": 1,
    "experimentType": "native-blocking-player-origin-priority",
    "providerId": "french-manga",
    "fixture": "jujutsu-kaisen-s01e01",
    "requestType": "anime",
    "sourceNiakvioSha": "a" * 40,
    "sourceRunId": "44610510286",
    "providerArtifactSha256": "c" * 64,
    "officialClientSha": "d" * 40,
    "runtimeScope": "native-blocking-fetch",
    "preferredHosts": ["lplaygo.com"],
    "deprioritizedHosts": ["vidzy.live"],
    "evidencePattern": "player-5xx-then-alternate-2xx-then-hls-2xx-near-budget-zero",
    "candidateOnly": True,
    "generatedByBrain": True,
    "proofAuthority": False,
    "publicationAuthority": False,
    "nativePlaybackAuthority": False,
    "providerMutationAuthority": False,
}
base["experimentFingerprint"] = canonical_fingerprint(base)
doc = {
    "routes": [{
        "provider": "french-manga",
        "mode": "deterministic_advisor",
        "targetLayer": "core",
        "strategy": "prioritize_native_blocking_player_origin_from_observed_outcome",
        "candidateExperiment": {**base, "privateUrl": "https://signed.invalid/x?token=SECRET"},
    }]
}
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    route, ledger = root / "route.json", root / "ledger.json"
    route.write_text(json.dumps(doc), encoding="utf-8")
    out = persist(route, ledger, brain_sha)
    assert len(out["rows"]) == 1
    row = out["rows"][0]
    assert row["preferredHosts"] == ["lplaygo.com"]
    assert row["deprioritizedHosts"] == ["vidzy.live"]
    assert row["brainSha"] == brain_sha
    assert row["experimentFingerprint"] == base["experimentFingerprint"]
    wire = ledger.read_text(encoding="utf-8")
    for forbidden in ("https://", "token=", "SECRET", "privateUrl"):
        assert forbidden not in wire

    bad = json.loads(json.dumps(doc))
    bad["routes"][0]["candidateExperiment"]["publicationAuthority"] = True
    route.write_text(json.dumps(bad), encoding="utf-8")
    try:
        persist(route, ledger, brain_sha)
        raise AssertionError("publication authority must be rejected")
    except ValueError:
        pass

    bad = json.loads(json.dumps(doc))
    bad["routes"][0]["candidateExperiment"]["preferredHosts"] = ["evil.invalid/path"]
    route.write_text(json.dumps(bad), encoding="utf-8")
    try:
        persist(route, ledger, brain_sha)
        raise AssertionError("non-host value must be rejected")
    except ValueError:
        pass

print("brain native candidate experiment persistence contract passed")
