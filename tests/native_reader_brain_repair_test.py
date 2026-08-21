#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_native_reader_brain_repair.py"
COMPARE = ROOT / "scripts/compare_native_reader_brain_repair.py"
DIAGNOSE = ROOT / "engine_v2/scripts/diagnose-native-reader.mjs"


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


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


def write_result_log(
    path: Path,
    *,
    client: str,
    provider: str = "MOVIESDRIVE",
    count: int = 0,
    enabled: bool = True,
    route_mode: str = "declared",
) -> None:
    provider64 = b64(provider)
    lines = [
        f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client={client}",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=ui-launched screenshot=a.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=repository-load screenshot=b.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=repository-loaded screenshot=c.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=provider-load-state screenshot=d.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=corpus-begin screenshot=e.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=provider-loading screenshot=f.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=provider-result screenshot=g.png bytes=100",
        f"FIELD_NATIVE_FRONTEND_CAPTURE client={client} fixture=sinners-2025 phase=corpus-end screenshot=h.png bytes=100",
        f"FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client={client} fixture=sinners-2025 expected=1 manifest_host=raw.githubusercontent.com",
        f"FIELD_NATIVE_REPOSITORY_LOAD_RESULT client={client} fixture=sinners-2025 expected=1 loaded=1",
        (
            f"FIELD_NATIVE_PROVIDER_LOAD_RESULT client={client} fixture=sinners-2025 provider64={provider64} "
            f"manifest_enabled={'true' if enabled else 'false'} runtime_enabled={'true' if enabled else 'false'} metadata_match=true"
        ),
        f"FIELD_NATIVE_CORPUS_BEGIN client={client} fixture=sinners-2025 providers=1",
        (
            f"FIELD_NATIVE_PROVIDER_BEGIN client={client} fixture=sinners-2025 provider64={provider64} "
            f"enabled={'true' if enabled else 'false'} request_type=movie route_mode={route_mode}"
        ),
        (
            f"FIELD_NATIVE_RESULT client={client} fixture=sinners-2025 provider64={provider64} "
            f"request_type=movie route_mode={route_mode} enabled={'true' if enabled else 'false'} duration_ms=1 count={count}"
        ),
        f"FIELD_NATIVE_CORPUS_END client={client} fixture=sinners-2025 errors=0",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_diagnose(logs: list[Path], output: Path) -> dict:
    run = subprocess.run(
        ["node", str(DIAGNOSE), "--output", str(output), *map(str, logs)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    return json.loads(output.read_text(encoding="utf-8"))


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
    # fixture prevents the Brain from condemning the whole provider globally.
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

    # Different causes on two clients are NOT consensus. One playback 403 and one
    # zero-stream extraction on the same provider/route remain two single-client
    # observations and cannot be merged merely because their provider id matches.
    mixed_causes = tmp / "mixed-causes.json"
    mixed_causes.write_text(json.dumps({
        "schemaVersion": 5,
        "brainVersion": 4,
        "readerFailures": 1,
        "extractionFailures": 1,
        "plans": [
            {
                "provider": "moviesdrive", "client": "tv", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": 0,
                "failureClass": "playback_http_access", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "replay-native-request-context"}],
            },
            {
                "provider": "moviesdrive", "client": "mobile", "fixture": "sinners-2025",
                "requestType": "movie", "routeMode": "declared", "index": -1,
                "failureClass": "media_extraction_gap", "action": "probe-targeted-repair",
                "hypotheses": [{"id": "capture-media-network"}],
            },
        ],
        "observations": [],
        "extractionHealthyObservations": [],
    }), encoding="utf-8")
    mixed_causes_report = run_builder(mixed_causes, tmp / "mixed-causes-repair")
    assert mixed_causes_report["proposalCount"] == 0, mixed_causes_report
    assert mixed_causes_report["compatibilityOnlyCount"] == 2, mixed_causes_report
    assert all(row["reason"] == "insufficient_cross_client_confirmation" for row in mixed_causes_report["skipped"]), mixed_causes_report
    assert mixed_causes_report["policy"]["sameFailureClassCrossClientConsensusRequired"] is True

    # Enabled provider + declared route + count=0 is genuine extraction evidence.
    # One client can classify it but cannot mutate the provider globally.
    zero_tv_log = tmp / "zero-tv.log"
    write_result_log(zero_tv_log, client="tv", count=0, enabled=True)
    zero_single_json = tmp / "zero-single.json"
    zero_single = run_diagnose([zero_tv_log], zero_single_json)
    assert zero_single["evidenceComplete"] is True, zero_single
    assert zero_single["readerObserved"] == 0, zero_single
    assert zero_single["extractionFailures"] == 1, zero_single
    assert zero_single["plans"][0]["failureClass"] == "media_extraction_gap", zero_single
    assert zero_single["plans"][0]["hypotheses"][0]["id"] == "capture-media-network", zero_single
    assert zero_single["policy"]["learningAllowed"] is False, zero_single
    zero_single_report = run_builder(zero_single_json, tmp / "zero-single-repair")
    assert zero_single_report["proposalCount"] == 0, zero_single_report
    assert zero_single_report["skipped"][0]["reason"] == "insufficient_cross_client_confirmation", zero_single_report

    # The same count=0 on two independent client families is real cross-client
    # extraction consensus and may enter the bounded generic repair sandbox.
    zero_mobile_log = tmp / "zero-mobile.log"
    write_result_log(zero_mobile_log, client="mobile", count=0, enabled=True)
    zero_cross_json = tmp / "zero-cross.json"
    zero_cross = run_diagnose([zero_tv_log, zero_mobile_log], zero_cross_json)
    assert zero_cross["evidenceComplete"] is True, zero_cross
    assert zero_cross["extractionFailures"] == 2, zero_cross
    assert zero_cross["crossClientProviderFailureGroups"] == 1, zero_cross
    assert zero_cross["policy"]["learningAllowed"] is True, zero_cross
    zero_cross_report = run_builder(zero_cross_json, tmp / "zero-cross-repair")
    assert zero_cross_report["proposalCount"] == 1, zero_cross_report
    zero_proposal = zero_cross_report["proposals"][0]
    assert zero_proposal["failureClasses"] == ["media_extraction_gap"], zero_proposal
    assert zero_proposal["failingClients"] == ["mobile", "tv"], zero_proposal
    assert zero_proposal["skills"] == ["global_media_enrichment_v1"], zero_proposal
    assert zero_cross_report["diagnosedExtractionFailures"] == 2, zero_cross_report

    # A third client proving extraction (count>0) vetoes the extraction mutation even
    # if two other clients returned zero. Playback may still be diagnosed separately.
    nonempty_desktop_log = tmp / "nonempty-desktop.log"
    write_result_log(nonempty_desktop_log, client="desktop", count=2, enabled=True)
    zero_with_peer_json = tmp / "zero-with-peer.json"
    zero_with_peer = run_diagnose([zero_tv_log, zero_mobile_log, nonempty_desktop_log], zero_with_peer_json)
    assert zero_with_peer["extractionFailures"] == 2, zero_with_peer
    assert zero_with_peer["extractionHealthy"] == 1, zero_with_peer
    assert zero_with_peer["crossClientProviderFailureGroups"] == 0, zero_with_peer
    assert zero_with_peer["policy"]["learningAllowed"] is False, zero_with_peer
    zero_peer_report = run_builder(zero_with_peer_json, tmp / "zero-peer-repair")
    assert zero_peer_report["proposalCount"] == 0, zero_peer_report
    assert zero_peer_report["skipped"][0]["reason"] == "client_specific_failure_has_healthy_peer", zero_peer_report
    assert zero_peer_report["skipped"][0]["healthyClients"] == ["desktop"], zero_peer_report

    # Disabled providers and undeclared capability probes are observational only and
    # cannot contribute to count=0 repair consensus.
    disabled_log = tmp / "zero-disabled.log"
    write_result_log(disabled_log, client="tv", count=0, enabled=False)
    disabled_json = tmp / "zero-disabled.json"
    disabled = run_diagnose([disabled_log], disabled_json)
    assert disabled["extractionFailures"] == 0, disabled
    assert disabled["ignoredDisabledExtractionFailures"] == 1, disabled
    assert disabled["plans"] == [], disabled

    capability_log = tmp / "zero-capability.log"
    write_result_log(capability_log, client="tv", count=0, enabled=True, route_mode="capability_probe")
    capability_json = tmp / "zero-capability.json"
    capability = run_diagnose([capability_log], capability_json)
    assert capability["extractionFailures"] == 0, capability
    assert capability["capabilityResultObserved"] == 1, capability
    assert capability["plans"] == [], capability

    # A provider mutation sandbox becomes eligible only after independent client
    # families corroborate the same player failure and no healthy peer/alternate
    # stream contradicts it.
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

print("native reader Brain repair cross-client, zero-stream and multi-stream safety tests passed")
