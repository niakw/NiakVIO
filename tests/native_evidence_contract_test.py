#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


request_contract = text("scripts/augment_native_corpus_request_contract.py")
completeness = text("scripts/native_evidence_completeness.cjs")
diagnosis = text("engine_v2/scripts/diagnose-native-reader.mjs")
tv_suite = text("scripts/run_native_corpus_tv_suite.sh")
mobile_suite = text("scripts/run_native_corpus_mobile_suite.sh")
desktop_suite = text("scripts/run_native_corpus_desktop_suite.sh")
android_workflow = text(".github/workflows/native-android-route-reader.yml")
desktop_workflow = text(".github/workflows/native-desktop-reader-acceptance.yml")

# Every staged provider remains in traversal scope; unsupported routes are an
# explicit observation rather than an execution failure.
for required in (
    "duplicate provider id in canonical manifest",
    'CANONICAL = {"movie", "tv", "anime"}',
    'listOf("anime", "tv").filter',
    "FIELD_NATIVE_PROVIDER_SKIPPED",
    "reason=unsupported_type",
    "FIELD_NATIVE_PROVIDER_BEGIN",
    "request_type=$requestMediaType",
    "FIELD_NATIVE_PLAYER_BEGIN",
):
    assert required in request_contract, required

# Backend + frontend evidence is part of the validity contract, not optional debug.
for required in (
    "missing_runtime_instrumentation",
    "provider_traversal:",
    "provider_route_terminal:",
    "player_terminal:",
    "http_terminal:",
    "missing_frontend_phase:",
    "frontend_capture_errors:",
    "ui-launched",
    "provider-loading",
    "provider-http-request",
    "provider-http-response",
    "provider-result",
    "player-start",
    "player-result",
    "corpus-end",
):
    assert required in completeness, required

# Brain must be fail-closed when any evidence link is missing.
for required in (
    "assessNativeEvidence",
    "evidenceComplete",
    "evidenceProblems",
    "learningAllowed: evidence.complete",
    "repairPlanningAllowed: evidence.complete",
    "const plans = evidence.complete ?",
    "if (readerRows.length === 0 || !evidence.complete) process.exitCode = 2",
):
    assert required in diagnosis, required

# Android suites must instrument the official client, collect multi-tag backend
# logs, run visual capture, and preserve evidence into the corpus log.
for suite, client in ((tv_suite, "tv"), (mobile_suite, "mobile")):
    for required in (
        "instrument_native_client_evidence.py",
        "augment_native_corpus_request_contract.py",
        "watch_native_device_frontend.sh",
        "capture_native_device_frontend.sh",
        "NiakvioCorpus:I NiakvioEvidence:I PluginRuntime:I",
        f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client={client}",
        "gate_native_reader_coverage.cjs",
        "gate_native_reader_result.cjs",
    ):
        assert required in suite, (client, required)

# Route workflows are exhaustive by logical media route, with all manifest rows
# (including disabled entries) and every returned stream.
for fixture in ("sinners-2025", "breaking-bad-s01e01", "jujutsu-kaisen-s01e01"):
    assert fixture in android_workflow, fixture
for required in (
    "NIAKVIO_TARGET_PROVIDER: all",
    "NIAKVIO_PRIMARY_STREAM_SCOPE: all",
    "--provider all --streams all",
    "native-evidence/tv/${{ matrix.fixture }}/**",
    "native-evidence/mobile/${{ matrix.fixture }}/**",
    "diagnose-native-reader.mjs",
):
    assert required in android_workflow, required

# Desktop Linux is explicitly not native-reader proof. macOS/Windows must build
# Nuvio's own bridges and run NativePlayerController evidence on all streams.
for required in (
    "official_nuvio_desktop_player_is_stub",
    "instrument_native_desktop_evidence.py",
    "augment_native_desktop_player.py",
    "complete_native_desktop_frontend_phases.py",
    "NIAKVIO_PRIMARY_STREAM_SCOPE",
    "gate_native_reader_coverage.cjs",
    "gate_native_reader_result.cjs",
):
    assert required in desktop_suite, required
for required in (
    "macos-15",
    "windows-2022",
    ":composeApp:buildMacosPlayerBridge",
    ":composeApp:buildWindowsPlayerBridge",
    "Microsoft.Web.WebView2",
    "NIAKVIO_TARGET_PROVIDER: all",
    "NIAKVIO_PRIMARY_STREAM_SCOPE: all",
    "native-evidence/desktop/**",
):
    assert required in desktop_workflow, required

print("full native evidence contract tests passed")
