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
client_instrumenter = text("scripts/instrument_native_client_evidence.py")
desktop_instrumenter = text("scripts/instrument_native_desktop_evidence.py")
resolver = text("scripts/resolve_native_repository.sh")
client_head_resolver = text("scripts/resolve_nuvio_lab_heads.py")
reader_runtime_scope = text("scripts/scope_native_reader_learning_runtime.py")
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
player_reach_gate = text("scripts/gate_native_player_reached.cjs")
android_workflow = text(".github/workflows/native-android-route-reader.yml")
desktop_workflow = text(".github/workflows/native-desktop-reader-acceptance.yml")
learning_sync = text(".github/workflows/native-reader-learning-sync.yml")

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

# Production Nuvio source must not be patched merely to gain richer HTTP evidence.
# Historical instrumentation entry points remain as audited no-op shims so stale
# workflow references cannot silently reintroduce runtime mutation.
for shim in (repository_http, client_instrumenter, desktop_instrumenter):
    assert "disabled_by_human_ux_policy" in shim
    assert "runtime_mutation=false" in shim
    assert "audit_checkout" in shim
    for forbidden in (
        "write_text(",
        "write_bytes(",
        "addInterceptor",
        "FIELD_NATIVE_HTTP_REQUEST client=",
        "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=",
    ):
        assert forbidden not in shim, forbidden

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

# Labs resolve the latest official client branch HEAD. Accepted/contract refs remain
# audit context only; an unresolved HEAD may never silently fall back to stale code.
for required in (
    "latest official HEAD is unresolved",
    "refusing stale fallback",
    "current_head",
    "accepted_ref",
    "contract_ref",
    "latest-official-head-for-labs",
):
    assert required in client_head_resolver, required
for workflow in (android_workflow, desktop_workflow):
    assert "check_nuvio_client_upstreams.py" in workflow
    assert "resolve_nuvio_lab_heads.py" in workflow
    assert "Checkout latest official" in workflow
assert "get('accepted_ref') or '')" not in android_workflow
assert "get('accepted_ref') or '')" not in desktop_workflow

# Reader repair memory is historical but only influences the exact client revision
# fingerprint that produced it. Legacy/unscoped memory is never recycled after drift.
for required in (
    "exact-runtime-fingerprint-only",
    "legacyUnscopedExcluded",
    "runtimeFingerprint",
    "entry_fingerprint(row) == fingerprint",
):
    assert required in reader_runtime_scope, required
assert "scope_native_reader_learning_runtime.py filter" in android_workflow
assert "representative-cross-client-brain.json" in android_workflow
assert "tv-reader-repair-comparison-${fixture}.json" in android_workflow
assert 'NIAKVIO_TARGET_FIXTURES: "sinners-2025 breaking-bad-s01e01 jujutsu-kaisen-s01e01"' in android_workflow
assert 'needs: [resolve, tv-route-reader, mobile-route-reader]' in android_workflow
assert "scope_native_reader_learning_runtime.py merge" in learning_sync

# Android may not gain a test-only transport capability.
assert "validate_manifest" in android_transport
assert "mode=production-policy" in android_transport
assert "modified=false" in android_transport
assert 'usesCleartextTraffic\", \"true\"' not in android_transport
assert "android.permission.INTERNET" not in android_transport

# Component diagnostics invoke production player entry points and may supplement
# diagnosis, but the policy prevents them from being counted as human-UX acceptance.
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

# The production player is always the first media consumer in component diagnostics.
# Transport diagnostics are post-observation only and cannot consume/expire a signed
# URL before the production player attempts it.
assert android_player.index("val reader = probeNativePlayer(row.url, row.headers, row.type") < android_player.index("val transport = probeTransport(row.url, row.headers)")
assert desktop_player.index("val reader = probeDesktopProductionPlayer(row.url, row.headers, row.type") < desktop_player.index("val transport = probeTransport(row.url, row.headers)")

# Suites may retain historical shim calls, but those calls are now explicit audited
# no-ops. Repository/provider/player/frontend evidence comes from test-owned code,
# official Nuvio behavior and external capture rather than runtime source patching.
for suite, client in ((tv_suite, "tv"), (mobile_suite, "mobile")):
    for required in (
        "instrument_native_client_evidence.py",
        "instrument_native_repository_http_evidence.py",
        "augment_native_provider_loading_compat.py",
        "gate_native_reader_coverage.cjs",
        "gate_native_reader_result.cjs",
        "gate_native_player_reached.cjs",
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
    "gate_native_player_reached.cjs",
    "official_repository_loading=true",
    "privilege=ordinary-user",
):
    assert required in desktop_suite, required

# Smoke acceptance is allowed to keep ordinary provider/evidence/player outcomes as
# diagnostics, but it must never claim success from an entry/setup attempt. Only a
# terminal FIELD_NATIVE_PLAYER row from a *-production engine can satisfy reach.
for required in (
    "FIELD_NATIVE_PLAYER ",
    "-production$",
    "player_setup",
    "NO_LAUNCH_INTENT",
    "production_player_never_reached",
    "FIELD_NATIVE_PLAYER_REACH_GATE",
):
    assert required in player_reach_gate, required
assert "FIELD_NATIVE_PLAYER_BEGIN" not in player_reach_gate
for suite in (tv_suite, mobile_suite, desktop_suite):
    assert "soft_failures=" in suite
    assert "gate=production_player_reached" in suite
    assert "NIAKVIO_BRAIN_NONBLOCKING=1" in suite

# Coverage is fail-closed and PR component proof checks two returned streams; deep/
# manual diagnostic paths remain exhaustive. This is not human-UX acceptance by itself.
assert "NIAKVIO_PR_STREAM_LIMIT" in coverage_gate
assert "DEFAULT_PR_STREAM_LIMIT = 2" in coverage_gate
assert "streamCoverageSatisfied" in coverage_gate
assert "return observed >= expected && observed <= returned;" in coverage_gate
assert "return observed === expected;" in coverage_gate
for workflow in (android_workflow, desktop_workflow):
    assert "NIAKVIO_PRIMARY_STREAM_SCOPE: all" in workflow
assert "NIAKVIO_TARGET_PROVIDER: all" in android_workflow
assert "NIAKVIO_TARGET_PROVIDER: all" in desktop_workflow

# Evidence completeness and Brain learning remain fail-closed outside the smoke. The
# native-reader smoke may suppress the diagnostic process exit only; it does not turn
# incomplete evidence into usable learning or permit provider mutation.
for required in (
    "missing_repository_load:",
    "provider_route_terminal:",
    "player_terminal:",
    "http_terminal:",
    "missing_frontend_phase:",
):
    assert required in completeness, required
for required in (
    "evidenceComplete",
    "evidenceUsable: evidence.complete",
    "learningAllowed: providerLearningAllowed",
    "repairPlanningAllowed: providerLearningAllowed",
    "providerMutationRequiresCrossClientConsensus: true",
    "clientRuntimeFailureLearningAllowed: false",
    "providerLoadJsMutationAllowed: false",
    "const nonblockingSmoke = process.env.NIAKVIO_BRAIN_NONBLOCKING === '1'",
    "if (!evidence.complete && !nonblockingSmoke) process.exitCode = 2",
    "nonblockingSmoke,",
):
    assert required in diagnosis, required
assert "FIELD_NATIVE_CAPABILITY_PROBE_REJECTED" in reader_gate

print("full native human UX evidence contract tests passed")
