#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_provider_non_regression_v1 as gate


def valid_doc() -> dict:
    return {
        "schemaVersion": 1,
        "authority": "provider-upstream-drift-v1",
        "providers": {
            "movieshunt": {
                "active": True,
                "lanes": ["movie"],
                "baselineRef": "20bbb1143da0cb591f18c58ecc1d791b39345778",
                "baselineAsset": "providers/movieshunt--nuvio--5ffc0f6282266f66.js",
                "candidateRef": "0f60b209d6ced4057346f0fcedd867e0b0846306",
                "baselineAttempts": 3,
                "candidateAttempts": 3,
                "baselineVerified": False,
                "candidateVerified": False,
                "baselineFailureStage": "provider_network_http_error",
                "candidateFailureStage": "provider_network_http_error",
                "verdict": "external_drift_both_fail",
                "observedAt": "2026-09-17T21:01:04Z",
                "evidenceRefs": [
                    "github-actions:35274174393",
                    "github-actions:35274174393/artifacts/10518619656",
                ],
                "artifactDigest": "sha256:c2bb42e5aded3b2dfd72e9edd9ca9d74c798aeb51306c62ea53ee9832dcbf158",
            }
        },
    }


with tempfile.TemporaryDirectory(prefix="niakvio-upstream-drift-") as tmp:
    path = Path(tmp) / "drift.json"
    path.write_text(json.dumps(valid_doc()), encoding="utf-8")
    rows = gate.load_upstream_drift(path)
    assert set(rows) == {"movieshunt"}
    assert gate.active_upstream_drift_lanes(rows, "movieshunt", "20bbb1143da0cb591f18c58ecc1d791b39345778") == {"movie"}
    assert gate.active_upstream_drift_lanes(rows, "movieshunt", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") == set()

    bad = valid_doc()
    bad["providers"]["movieshunt"]["baselineAttempts"] = 1
    path.write_text(json.dumps(bad), encoding="utf-8")
    try:
        gate.load_upstream_drift(path)
    except ValueError:
        pass
    else:
        raise AssertionError("single-attempt upstream drift evidence must be rejected")

    bad = valid_doc()
    bad["providers"]["movieshunt"]["baselineVerified"] = True
    path.write_text(json.dumps(bad), encoding="utf-8")
    try:
        gate.load_upstream_drift(path)
    except ValueError:
        pass
    else:
        raise AssertionError("a verified baseline cannot be classified as current upstream drift")

source = (ROOT / "scripts" / "check_provider_non_regression_v1.py").read_text(encoding="utf-8")
assert "upstreamDriftApplied" in source
assert "external_drift_both_fail" in source
assert "semantic_capability_regression" in source
assert "historical_hls_m3u8_regression" in source
print("provider upstream drift evidence contract passed")
