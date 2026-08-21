#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_native_reader_brain_repair.py"
COMPARE = ROOT / "scripts/compare_native_reader_brain_repair.py"


def run_builder(diagnosis: Path, repair_dir: Path) -> dict:
    built = subprocess.run([
        "python3", str(BUILDER),
        "--diagnosis", str(diagnosis),
        "--manifest", str(ROOT / "manifest.json"),
        "--output-dir", str(repair_dir),
        "--fixture", "sinners-2025",
        "--max-providers", "2",
    ], cwd=ROOT, text=True, capture_output=True)
    assert built.returncode == 0, built.stdout + built.stderr
    return json.loads((repair_dir / "repair-report.json").read_text(encoding="utf-8"))


with tempfile.TemporaryDirectory(dir=ROOT) as tmp_raw:
    tmp = Path(tmp_raw)

    # A single native client failure is compatibility evidence only. It must not
    # become a global provider mutation candidate.
    single = tmp / "single-client.json"
    single.write_text(json.dumps({
        "schemaVersion": 5,
        "brainVersion": 4,
        "readerFailures": 1,
        "plans": [{
            "provider": "moviesdrive",
            "client": "tv",
            "fixture": "sinners-2025",
            "requestType": "movie",
            "routeMode": "declared",
            "index": 0,
            "failureClass": "playback_http_access",
            "action": "probe-targeted-repair",
            "hypotheses": [{"id": "replay-native-request-context"}],
        }],
        "observations": [{
            "provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025",
            "requestType": "movie", "routeMode": "declared", "index": 0,
            "failureClass": "playback_http_access", "state": "error",
        }],
    }), encoding="utf-8")
    single_report = run_builder(single, tmp / "single-repair")
    assert single_report["proposalCount"] == 0, single_report
    assert single_report["compatibilityOnlyCount"] == 1, single_report
    assert single_report["skipped"][0]["reason"] == "insufficient_cross_client_confirmation"
    assert single_report["policy"]["singleClientFailureIsCompatibilityEvidenceOnly"] is True

    # Even two failing clients cannot justify a global mutation when a peer client
    # already proves the same provider/route/fixture playable.
    healthy_peer = tmp / "healthy-peer.json"
    healthy_peer.write_text(json.dumps({
        "schemaVersion": 5,
        "brainVersion": 4,
        "readerFailures": 2,
        "plans": [
            {
                "provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 0,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
            {
                "provider": "moviesdrive", "client": "desktop", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 0,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
        ],
        "observations": [
            {"provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "playback_http_access", "state": "error"},
            {"provider": "moviesdrive", "client": "desktop", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "playback_http_access", "state": "error"},
            {"provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "healthy", "state": "ready"},
        ],
    }), encoding="utf-8")
    peer_report = run_builder(healthy_peer, tmp / "peer-repair")
    assert peer_report["proposalCount"] == 0, peer_report
    assert peer_report["skipped"][0]["reason"] == "client_specific_failure_has_healthy_peer"
    assert peer_report["skipped"][0]["healthyClients"] == ["tv"]

    # One provider may expose several independent streams. Failures stay indexed
    # stream-by-stream, but any healthy alternate stream for the same provider/route/
    # fixture prevents the Brain from condemning the whole provider globally. This
    # also covers the case where two client families fail one candidate while another
    # candidate from the same provider remains playable.
    mixed_streams = tmp / "mixed-streams.json"
    mixed_streams.write_text(json.dumps({
        "schemaVersion": 5,
        "brainVersion": 4,
        "readerFailures": 2,
        "plans": [
            {
                "provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 1,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
            {
                "provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 1,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
        ],
        "observations": [
            {"provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "healthy", "state": "ready"},
            {"provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 1, "failureClass": "playback_http_access", "state": "error"},
            {"provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "healthy", "state": "ready"},
            {"provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 1, "failureClass": "playback_http_access", "state": "error"},
        ],
    }), encoding="utf-8")
    mixed_report = run_builder(mixed_streams, tmp / "mixed-streams-repair")
    assert mixed_report["proposalCount"] == 0, mixed_report
    assert mixed_report["compatibilityOnlyCount"] == 1, mixed_report
    assert mixed_report["skipped"][0]["reason"] == "client_specific_failure_has_healthy_peer"
    assert mixed_report["skipped"][0]["failingClients"] == ["mobile", "tv"]
    assert mixed_report["skipped"][0]["healthyClients"] == ["mobile", "tv"]
    assert mixed_report["skipped"][0]["occurrences"] == 2

    # A provider mutation sandbox becomes eligible only after independent client
    # families corroborate the same failure and no healthy peer/alternate stream
    # contradicts it.
    diagnosis = tmp / "cross-client.json"
    diagnosis.write_text(json.dumps({
        "schemaVersion": 5,
        "brainVersion": 4,
        "readerFailures": 2,
        "plans": [
            {
                "provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 0,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [
                    {"id": "replay-native-request-context"},
                    {"id": "refresh-access-bound-media"},
                ],
            },
            {
                "provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 0,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
        ],
        "observations": [
            {"provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "playback_http_access", "state": "error"},
            {"provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025", "requestType": "movie", "routeMode": "declared", "index": 0, "failureClass": "playback_http_access", "state": "error"},
        ],
    }), encoding="utf-8")
    repair_dir = tmp / "repair"
    report = run_builder(diagnosis, repair_dir)
    assert report["proposalCount"] == 1, report
    proposal = report["proposals"][0]
    assert proposal["provider"] == "moviesdrive"
    assert proposal["failingClients"] == ["mobile", "tv"]
    assert proposal["crossClientConfirmed"] is True
    assert proposal["skills"] == ["global_media_enrichment_v1"]
    assert proposal["requiresFreshNativeReaderProof"] is True
    candidate = ROOT / proposal["candidateFile"]
    assert candidate.is_file(), proposal
    text = candidate.read_text(encoding="utf-8")
    assert "scoped-playback-context-v6-direct-safe-opaque-media" in text
    serialized_report = json.dumps(report).lower()
    assert "http://" not in serialized_report and "https://" not in serialized_report, report

    after = tmp / "after.json"
    after.write_text(json.dumps({
        "schemaVersion": 5,
        "brainVersion": 4,
        "readerFailures": 0,
        "observations": [
            {"provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025", "requestType": "movie", "index": 0, "failureClass": "healthy", "state": "ready"},
            {"provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025", "requestType": "movie", "index": 0, "failureClass": "healthy", "state": "ready"},
        ],
    }), encoding="utf-8")
    compared = tmp / "compare.json"
    comparison = subprocess.run([
        "python3", str(COMPARE),
        "--before", str(diagnosis),
        "--after", str(after),
        "--repair-report", str(repair_dir / "repair-report.json"),
        "--fixture", "sinners-2025",
        "--output", str(compared),
    ], cwd=ROOT, text=True, capture_output=True)
    assert comparison.returncode == 0, comparison.stdout + comparison.stderr
    result = json.loads(compared.read_text(encoding="utf-8"))
    assert result["acceptedCount"] == 1, result
    assert result["acceptedProviders"] == ["moviesdrive"], result
    assert result["policy"]["freshNativeReaderProofRequired"] is True

print("native reader Brain repair cross-client and multi-stream safety tests passed")
