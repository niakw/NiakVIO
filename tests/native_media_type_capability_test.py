#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def player(provider: str, route: str, mode: str, state: str, *, status: int = 0, stage: str = "none") -> str:
    return (
        f"FIELD_NATIVE_PLAYER client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} "
        f"request_type={route} route_mode={mode} index=0 state={state} engine=media3 "
        f"http_status={status} failure_stage={stage} duration_seconds={1440 if state == 'ready' else 0} "
        f"host64={b64('media.example')} error_class64={b64('PlaybackException' if state == 'error' else '')} "
        f"error_code64={b64('ERROR_CODE_IO_BAD_HTTP_STATUS' if state == 'error' else '')} "
        f"exception_chain64={b64('InvalidResponseCodeException' if state == 'error' else '')} "
        f"response_header_names64={b64('content-type')} load_bytes=0 load_duration_ms=0 media_data_type=-1 track_type=-1"
    )


def evidence_lines(*, probe_state: str) -> list[str]:
    provider = "anime-sama"  # manifest: movie + anime, intentionally no tv
    phases = [
        "ui-launched", "corpus-begin", "provider-loading", "provider-result",
        "player-start", "player-result", "corpus-end",
    ]
    lines = ["FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv"]
    lines.extend(
        f"FIELD_NATIVE_FRONTEND_CAPTURE client=tv phase={phase} screenshot=x.png bytes=100"
        for phase in phases
    )
    lines.extend([
        "FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=jujutsu-kaisen-s01e01 providers=1",
        f"FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} enabled=true request_type=anime route_mode=declared",
        f"FIELD_NATIVE_RESULT client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} request_type=anime route_mode=declared enabled=true duration_ms=10 count=1",
        f"FIELD_NATIVE_ROW client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} request_type=anime route_mode=declared index=0 title64={b64('Jujutsu Kaisen')} name64={b64('Episode 1')} quality64={b64('1080p')} language64={b64('ja')} type64={b64('hls')} host64={b64('media.example')} media_hint64={b64('Jujutsu Kaisen Episode 1')}",
        f"FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} request_type=anime route_mode=declared index=0",
        player(provider, "anime", "declared", "ready"),
        f"FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} enabled=true request_type=tv route_mode=capability_probe",
        f"FIELD_NATIVE_RESULT client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} request_type=tv route_mode=capability_probe enabled=true duration_ms=10 count=1",
        f"FIELD_NATIVE_ROW client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} request_type=tv route_mode=capability_probe index=0 title64={b64('Jujutsu Kaisen')} name64={b64('Episode 1')} quality64={b64('1080p')} language64={b64('ja')} type64={b64('hls')} host64={b64('media.example')} media_hint64={b64('Jujutsu Kaisen Episode 1')}",
        f"FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=jujutsu-kaisen-s01e01 provider64={b64(provider)} request_type=tv route_mode=capability_probe index=0",
        player(provider, "tv", "capability_probe", probe_state, status=403 if probe_state == "error" else 0, stage="http_access" if probe_state == "error" else "none"),
        "FIELD_NATIVE_CORPUS_END client=tv fixture=jujutsu-kaisen-s01e01 errors=0",
    ])
    return lines


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)

    healthy_log = tmp / "healthy.log"
    healthy_log.write_text("\n".join(evidence_lines(probe_state="ready")) + "\n", encoding="utf-8")

    gate = run("node", "scripts/gate_native_reader_result.cjs", str(healthy_log))
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "capability_probe_healthy=1" in gate.stdout

    cap_out = tmp / "capability.json"
    cap = run(
        "node", "scripts/analyze_native_media_type_capabilities.cjs",
        "jujutsu-kaisen-s01e01", "--output", str(cap_out), str(healthy_log),
    )
    assert cap.returncode == 0, cap.stdout + cap.stderr
    data = json.loads(cap_out.read_text(encoding="utf-8"))
    assert data["evidenceComplete"] is True
    assert data["provenCapabilities"] == 1, data
    proposal = data["proposals"][0]
    assert proposal["provider"] == "anime-sama", proposal
    assert proposal["addType"] == "tv", proposal
    assert proposal["requiresCrossDeviceConfirmation"] is True

    brain_cap_out = tmp / "brain-capability.json"
    brain_cap = run(
        "node", "engine_v2/scripts/diagnose-native-media-capabilities.mjs",
        "--output", str(brain_cap_out), str(healthy_log),
    )
    assert brain_cap.returncode == 0, brain_cap.stdout + brain_cap.stderr
    brain_cap_data = json.loads(brain_cap_out.read_text(encoding="utf-8"))
    assert len(brain_cap_data["proposals"]) == 1
    assert brain_cap_data["policy"]["productionManifestMutationAllowed"] is False

    failed_log = tmp / "failed.log"
    failed_log.write_text("\n".join(evidence_lines(probe_state="error")) + "\n", encoding="utf-8")

    # The undeclared tv probe fails, but the provider's declared anime contract is healthy.
    # Strict reader validation must therefore stay green.
    failed_gate = run("node", "scripts/gate_native_reader_result.cjs", str(failed_log))
    assert failed_gate.returncode == 0, failed_gate.stdout + failed_gate.stderr
    assert "failures=0" in failed_gate.stdout
    assert "capability_probe_failures=1" in failed_gate.stdout
    assert "FIELD_NATIVE_CAPABILITY_PROBE_REJECTED" in failed_gate.stdout

    failed_cap_out = tmp / "failed-capability.json"
    failed_cap = run(
        "node", "scripts/analyze_native_media_type_capabilities.cjs",
        "jujutsu-kaisen-s01e01", "--output", str(failed_cap_out), str(failed_log),
    )
    assert failed_cap.returncode == 0, failed_cap.stdout + failed_cap.stderr
    failed_data = json.loads(failed_cap_out.read_text(encoding="utf-8"))
    assert failed_data["provenCapabilities"] == 0
    assert failed_data["proposals"] == []
    assert any("reader_failure" in reason for reason in failed_data["outcomes"][0]["reasons"])

    # Repair Brain sees the probe failure as discovery evidence only: no provider repair.
    repair_out = tmp / "repair-brain.json"
    repair = run(
        "node", "engine_v2/scripts/diagnose-native-reader.mjs",
        "--output", str(repair_out), str(failed_log),
    )
    assert repair.returncode == 0, repair.stdout + repair.stderr
    repair_data = json.loads(repair_out.read_text(encoding="utf-8"))
    assert repair_data["readerFailures"] == 0, repair_data
    assert repair_data["capabilityProbeFailures"] == 1, repair_data
    assert repair_data["plans"] == [], repair_data

print("native media type capability tests passed")
