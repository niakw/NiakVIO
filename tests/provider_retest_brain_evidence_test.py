#!/usr/bin/env python3
"""Strict Retest-to-Brain evidence: source+run+bytes, no URLs or fake playback."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/export_retest_brain_evidence.py"
spec = importlib.util.spec_from_file_location("retest_brain_evidence", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "providers").mkdir()
    (root / "vf").mkdir()
    (root / "providers/demo.js").write_bytes(b"valid-exact-runtime-JS-v1")
    global_manifest = {
        "scrapers": [{"id": "DEMO", "enabled": True,
                      "filename": "providers/demo.js"}],
    }
    (root / "manifest.json").write_text(json.dumps(global_manifest))
    (root / "vf/manifest.json").write_text('{"scrapers":[]}')
    sha = "a" * 40
    report = {
        "resolved_scope": "explicit",
        "selected_providers": ["demo"],
        "rows": [{
            "provider_id": "demo", "semantic_type": "anime",
            "status": "playable_unverified", "debug_stage": "provider_returned_streams",
            "raw": 2, "playable": 2, "verified": 0,
            "fixture": {"mediaType": "anime", "tmdbId": "95479", "season": 1, "episode": 1},
            "debug_fetches": [{
                "url": "https://private.example/stream?token=DO_NOT_PERSIST",
                "request_headers": {"cookie": "SECRET_VALUE"},
            }],
            "debug_identity_reasons": [
                {"host": "private.example", "title": "secret title",
                 "identity_reason": "insufficient_identity_metadata",
                 "duration_reason": "duration_incomplete_hls",
                 "media_status": 200},
            ],
        }],
    }
    census = {
        "runId": "12345-retest", "triggerSha": sha,
        "providers": [{"provider": "demo", "status": "CANDIDATE OK",
                       "testedThisRun": True}],
    }
    observed = mod.export(report, census, root=root, sha=sha, run="12345")
    assert observed["providerCount"] == 1
    record = observed["rows"][0]
    assert record["providerArtifactSha256"] == mod.current_sha256(root, "demo")
    assert record["identityReasons"] == [
        "duration_incomplete_hls", "insufficient_identity_metadata",
    ]
    assert record["playable"] == 2 and record["verified"] == 0
    assert record["proofAuthority"] is False
    assert record["nativePlaybackAuthority"] is False
    wire = json.dumps(observed)
    for forbidden in ("private.example", "DO_NOT_PERSIST", "SECRET_VALUE",
                      "secret title", "cookie", "http", "sourceTitle"):
        assert forbidden not in wire, forbidden

    for altered, source, run in (
        ({**census, "runId": "old-retest"}, sha, "12345"),
        ({**census, "triggerSha": "b" * 40}, sha, "12345"),
        (census, "", "12345"),
        (census, sha, "invalid"),
    ):
        try:
            mod.export(report, altered, root=root, sha=source, run=run)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid source or run admitted")

    wrong = {**census, "providers": [
        {"provider": "demo", "status": "DISABLED", "testedThisRun": True},
    ]}
    assert mod.export(report, wrong, root=root, sha=sha, run="12345")["rows"] == []
    old = {**census, "providers": [
        {"provider": "demo", "status": "CANDIDATE OK", "testedThisRun": False},
    ]}
    assert mod.export(report, old, root=root, sha=sha, run="12345")["rows"] == []
    raw_malicious = {**report, "rows": [
        {**report["rows"][0],
         "debug_identity_reasons": [{"identity_reason": "token=some-secret-url"}]},
    ]}
    assert mod.export(raw_malicious, census, root=root, sha=sha, run="12345")["rows"][0]["identityReasons"] == []
    (root / "providers/demo.js").write_bytes(b"changed-runtime-JS-v2")
    assert mod.export(report, census, root=root, sha=sha, run="12345")["rows"][0]["providerArtifactSha256"] != record["providerArtifactSha256"]

workflow = (ROOT / ".github/workflows/provider-retest.yml").read_text()
runner = (ROOT / "scripts/run_provider_retest.py").read_text()
assert "provider_retest_brain_evidence_test.py" in workflow
assert "provider-retest-brain-evidence-latest.json" in workflow
assert "export_retest_brain_evidence.py" in runner
assert "automation/provider-retest-brain-evidence-latest.json" in runner
print("Retest Brain exact-bundle sanitized evidence contract passed")
