#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_brain_harness_differential.py"
spec = importlib.util.spec_from_file_location("harness_diff", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    stage = Path(tmp)
    (stage / "providers").mkdir()
    provider = stage / "providers" / "demo.js"
    provider.write_text("module.exports={getStreams:async()=>[]};\n", encoding="utf-8")
    sha = hashlib.sha256(provider.read_bytes()).hexdigest()
    registry = {
        "candidates": [{
            "key": "aio:demo",
            "canonical_id": "demo",
            "upstream_id": "demo",
            "local_path": "providers/demo.js",
            "sha256": sha,
        }]
    }
    health = {
        "results": [{
            "key": "aio:demo",
            "canonical_id": "demo",
            "tests": [{
                "fixture": {
                    "tmdbId": "157336",
                    "mediaType": "movie",
                    "title": "Interstellar",
                    "year": 2014,
                },
                "failure_class": "no_provider_request_observed",
                "network_observations": [],
                "invocation_diagnostics": [{
                    "name": "object",
                    "inferred_mode": "object",
                    "result": "empty",
                    "stream_count": 0,
                    "provider_observations": 0,
                }],
            }],
        }]
    }

    original = mod.run_nuvio_probe
    mod.run_nuvio_probe = lambda *_args, **_kwargs: {
        "available": True,
        "providerRequestCount": 2,
        "fetchCount": 3,
        "debugStage": "provider_network_zero_result",
        "rawStreams": 0,
        "playableStreams": 0,
        "identityContradictions": 0,
        "exitCode": 0,
    }
    try:
        result = mod.audit(stage=stage, registry=registry, health=health)
        assert result["providers"] == ["demo"], result
        assert result["rows"][0]["classification"] == "harness-differential-worker-zero-nuvio-provider-request"
        assert result["rows"][0]["providerSha256"] == sha
        serialized = json.dumps(result)
        assert "https://" not in serialized
        assert "TMDB_API_KEY" not in serialized

        mod.run_nuvio_probe = lambda *_args, **_kwargs: {
            "available": True,
            "providerRequestCount": 0,
            "fetchCount": 1,
            "debugStage": "provider_zero_before_provider_network",
            "rawStreams": 0,
            "playableStreams": 0,
            "identityContradictions": 0,
            "exitCode": 0,
        }
        no_diff = mod.audit(stage=stage, registry=registry, health=health)
        assert no_diff["providers"] == [], no_diff

        bad = json.loads(json.dumps(registry))
        bad["candidates"][0]["sha256"] = "0" * 64
        mod.run_nuvio_probe = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("mismatched staged bytes must not be replayed")
        )
        mismatch = mod.audit(stage=stage, registry=bad, health=health)
        assert mismatch["providers"] == [], mismatch
    finally:
        mod.run_nuvio_probe = original

print("Brain same-byte harness differential tests passed")
