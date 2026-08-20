#!/usr/bin/env python3
"""Architecture contract for native human-UX playback evidence.

This test intentionally focuses on invariants that must never regress: official Nuvio
repository/provider loading, production player entry points, observational evidence,
ordinary OS privileges and fail-closed Brain learning. Detailed codegen behavior has
its own dedicated tests.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


request_contract = text("scripts/augment_native_corpus_request_contract.py")
provider_loading = text("scripts/augment_native_provider_loading.py")
repository_http = text("scripts/instrument_native_repository_http_evidence.py")
resolver = text("scripts/resolve_native_repository.sh")
android_player = text("scripts/native_player_diagnostics_codegen.py")
desktop_player = text("scripts/augment_native_desktop_player.py")
android_transport = text("scripts/configure_native_android_lab_transport.py")
tv_suite = text("scripts/run_native_corpus_tv_suite.sh")
mobile_suite = text("scripts/run_native_corpus_mobile_suite.sh")
desktop_suite = text("scripts/run_native_corpus_desktop_suite.sh")
completeness = text("scripts/native_evidence_completeness.cjs")
diagnosis = text("engine_v2/scripts/diagnose-native-reader.mjs")
reader_gate = text("scripts/gate_native_reader_result.cjs")
coverage_gate = text("scripts/gate_native_reader_coverage.cjs")
android_workflow = text(".github/workflows/native-android-route-reader.yml")
desktop_workflow = text(".github/workflows/native-desktop-reader-acceptance.yml")

# Canonical media route traversal remains explicit; capability probes are evidence,
# never permission for a Lab-side provider/player rewrite.
for required in (
    'CANONICAL = {"movie", "tv", "anime"}',
    "ProviderRequestRoute",
    'listOf("anime", "tv").map',
    '"capability_probe"',
    "FIELD_NATIVE_PROVIDER_BEGIN",
    "FIELD_NATIVE_PLAYER_BEGIN",
    "request_type=$requestMediaType route_mode=$routeMode",
):
    assert required in request_contract, required

# Real Nuvio repository/provider APIs are used. Profile/plugin state is warm and not
# reset to manufacture another environment.
for required in (
    "manager.addRepository(repositoryManifestUrl)",
    "officialPluginManager.executeScraper(loadedScraper",
    "PluginRepository.initialize()",
    "PluginRepository.addRepository(repositoryManifestUrl)",
    "PluginRepository.executeScraper(loadedScraper",
    "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN",
    "FIELD_NATIVE_PROVIDER_LOAD_RESULT",
):
    assert required in provider_loading, required
assert "PluginRepository.clearLocalState()" not in provider_loading
assert "PluginRuntime.executePlugin(" not in provider_loading

# Repository instrumentation is passive: request semantics are preserved and only
# sanitized metadata is emitted.
for required in (
    "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST",
    "FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE",
    "FIELD_NATIVE_REPOSITORY_HTTP_ERROR",
    "response_header_names=$responseHeaderNames",
    "source=$cacheSource",
):
    assert required in repository_http, required
for forbidden in ("newBuilder().url(", "header(\"Referer\"", "header(\"Origin\""):
    assert forbidden not in repository_http, forbidden

# Staging may expose a generated content-addressed NiakVIO repository, but may never
# elevate Nuvio or bypass the OS to reach it.
for required in (
    "content-addressed",
    "candidate-${content_key}",
    "manifest + every provider",
    "local_server_not_ready_unprivileged",
    "observational=true privileged=false",
):
    assert required in resolver, required
for forbidden in ("sudo -n", "sudo ", "--add-opens", "ALL-UNNAMED"):
    assert forbidden not in resolver, forbidden
    assert forbidden not in desktop_suite, forbidden
assert "root_execution_forbidden" in desktop_suite

# Android may not gain a test-only transport capability.
assert "validate_manifest" in android_transport
assert "mode=production-policy" in android_transport
assert "modified=false" in android_transport
assert 'usesCleartextTraffic", "true"' not in android_transport
assert "android.permission.INTERNET" not in android_transport

# Human UX playback uses Nuvio production entries, not a parallel lab player.
for required in (
    "Screen.Player.createRoute",
    "NuvioNavHost",
    "LastPlaybackDiagnostics",
    "PlatformPlayerSurface",
    "nuvio-tv-production",
    "nuvio-mobile-production",
):
    assert required in android_player, required
for forbidden in (
    "ExoPlayer.Builder",
    "PlayerPlaybackNetworking.createDataSourceFactory",
    "PlatformPlaybackDataSourceFactory.create",
):
    assert forbidden not in android_player, forbidden

assert "PlatformPlayerSurface(" in desktop_player
assert "probeDesktopProductionPlayer" in desktop_player
assert "sourceHeaders = headers.orEmpty()" in desktop_player
assert "DEFAULT_PR_STREAM_LIMIT = 2" in desktop_player
assert "NIAKVIO_PR_STREAM_LIMIT" in desktop_player
for forbidden in (
    "NativePlayerController(",
    "NativePlayerHost(",
    "controller.attach(",
    "decoderPriority = 1",
    "nvidiaRtxSuperResolutionEnabled = false",
):
    assert forbidden not in desktop_player, forbidden

# The production player is always the first media consumer. Transport diagnostics
# are post-observation only and cannot consume/expire a signed URL before playback.
assert android_player.index("val reader = probeNativePlayer(row.url, row.headers, row.type") < android_player.index("val transport = probeTransport(row.url, row.headers)")
assert desktop_player.index("val reader = probeDesktopProductionPlayer(row.url, row.headers, row.type") < desktop_player.index("val transport = probeTransport(row.url, row.headers)")

# Every suite still collects repository -> provider -> player -> frontend evidence.
for suite, client in ((tv_suite, "tv"), (mobile_suite, "mobile")):
    for required in (
        "instrument_native_client_evidence.py",
        "instrument_native_repository_http_evidence.py",
        "augment_native_provider_loading.py",
        "gate_native_reader_coverage.cjs",
        "gate_native_reader_result.cjs",
        "official_repository_loading=true",
        f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client={client}",
    ):
        assert required in suite, (client, required)
for required in (
    "instrument_native_desktop_evidence.py",
    "instrument_native_repository_http_evidence.py",
    "augment_native_desktop_player.py",
    "gate_native_reader_coverage.cjs",
    "gate_native_reader_result.cjs",
    "official_repository_loading=true",
    "privilege=ordinary-user",
):
    assert required in desktop_suite, required

# Coverage is fail-closed and PR proof checks two returned streams; deep/manual paths
# remain exhaustive.
assert "NIAKVIO_PR_STREAM_LIMIT" in coverage_gate
assert "DEFAULT_PR_STREAM_LIMIT" in coverage_gate
assert "observed !== expected" in coverage_gate
for workflow in (android_workflow, desktop_workflow):
    assert "NIAKVIO_PRIMARY_STREAM_SCOPE: all" in workflow
assert "NIAKVIO_TARGET_PROVIDER: all" in android_workflow
assert "NIAKVIO_TARGET_PROVIDER: all" in desktop_workflow

# Evidence completeness and Brain learning remain fail-closed. A broken player is a
# valid observed failure, not a reason for the Lab to mutate Nuvio or the OS.
for required in (
    "missing_repository_load:",
    "missing_repository_http:",
    "provider_route_terminal:",
    "player_terminal:",
    "http_terminal:",
    "missing_frontend_phase:",
):
    assert required in completeness, required
for required in (
    "evidenceComplete",
    "learningAllowed: evidence.complete",
    "repairPlanningAllowed: evidence.complete",
    "providerLoadJsMutationAllowed: false",
    "if (!evidence.complete) process.exitCode = 2",
):
    assert required in diagnosis, required
assert "FIELD_NATIVE_CAPABILITY_PROBE_REJECTED" in reader_gate

print("full native human UX evidence contract tests passed")
