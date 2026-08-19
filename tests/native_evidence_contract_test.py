#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


request_contract = text("scripts/augment_native_corpus_request_contract.py")
provider_loading = text("scripts/augment_native_provider_loading.py")
completeness = text("scripts/native_evidence_completeness.cjs")
collection_analyzer = text("scripts/analyze_native_corpus_collection.cjs")
diagnosis = text("engine_v2/scripts/diagnose-native-reader.mjs")
capability_brain = text("engine_v2/scripts/diagnose-native-media-capabilities.mjs")
reader_gate = text("scripts/gate_native_reader_result.cjs")
capability_analyzer = text("scripts/analyze_native_media_type_capabilities.cjs")
tv_suite = text("scripts/run_native_corpus_tv_suite.sh")
mobile_suite = text("scripts/run_native_corpus_mobile_suite.sh")
desktop_suite = text("scripts/run_native_corpus_desktop_suite.sh")
android_workflow = text(".github/workflows/native-android-route-reader.yml")
desktop_workflow = text(".github/workflows/native-desktop-reader-acceptance.yml")

# Every staged provider remains in traversal scope; unsupported routes are an
# explicit observation rather than an execution failure. Anime-capable providers
# get both tv and anime routes; an undeclared side is discovery evidence only.
for required in (
    "duplicate provider id in canonical manifest",
    'CANONICAL = {"movie", "tv", "anime"}',
    "ProviderRequestRoute",
    'listOf("anime", "tv").map',
    '"capability_probe"',
    "FIELD_NATIVE_PROVIDER_SKIPPED",
    "reason=unsupported_type",
    "FIELD_NATIVE_PROVIDER_BEGIN",
    "request_type=$requestMediaType route_mode=$routeMode",
    "FIELD_NATIVE_PLAYER_BEGIN",
):
    assert required in request_contract, required

# Provider proof must pass through the real Nuvio repository/manager layer first.
# Repeated fixtures keep the user's/app profile warm and reuse the exact repository
# installation/provider cache instead of resetting plugin state on every launch.
for required in (
    "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN",
    "FIELD_NATIVE_REPOSITORY_LOAD_RESULT",
    "FIELD_NATIVE_REPOSITORY_CACHE_HIT",
    "FIELD_NATIVE_PROVIDER_LOAD_RESULT",
    "FIELD_NATIVE_PROVIDER_LOAD_ERROR",
    "FIELD_NATIVE_PROVIDER_LOAD_SKIPPED",
    "manager.repositories.first()",
    "manager.addRepository(repositoryManifestUrl)",
    "officialPluginManager.executeScraper(loadedScraper",
    "PluginRepository.initialize()",
    "PluginRepository.uiState.value.repositories.firstOrNull",
    "PluginRepository.addRepository(repositoryManifestUrl)",
    "PluginRepository.executeScraper(loadedScraper",
    "requestRoutesFor(provider.id, mediaType)",
    "reason=disabled_platform",
    "reason=load_failure",
):
    assert required in provider_loading, required
assert "PluginRepository.clearLocalState()" not in provider_loading, "native lab must preserve Nuvio profile/plugin state"

# Backend + frontend evidence is part of the validity contract, not optional debug.
for required in (
    "missing_runtime_instrumentation",
    "missing_repository_load:",
    "provider_load_coverage:",
    "provider_traversal:",
    "provider_route_terminal:",
    "player_terminal:",
    "http_terminal:",
    "missing_frontend_phase:",
    "frontend_capture_errors:",
    "ui-launched",
    "repository-load",
    "repository-loaded",
    "provider-load-state",
    "provider-loading",
    "provider-http-request",
    "provider-http-response",
    "provider-result",
    "player-start",
    "player-result",
    "corpus-end",
):
    assert required in completeness, required

# Brain must be fail-closed when any evidence link is missing, and capability
# probes must never become provider-repair plans.
for required in (
    "assessNativeEvidence",
    "evidenceComplete",
    "evidenceProblems",
    "learningAllowed: evidence.complete",
    "repairPlanningAllowed: evidence.complete",
    "capabilityLearningAllowed: evidence.complete",
    "capabilityPromotionRequiresIdentityProof: true",
    "const declaredRows = readerRows.filter",
    "const capabilityRows = readerRows.filter",
    "const plans = evidence.complete ? failures.map",
    "if (readerRows.length === 0 || !evidence.complete) process.exitCode = 2",
):
    assert required in diagnosis, required
for required in (
    "routeMode",
    "const declared = rows.filter",
    "const probes = rows.filter",
    "FIELD_NATIVE_CAPABILITY_PROBE_REJECTED",
    "process.exit(failures.length ? 1 : 0)",
):
    assert required in reader_gate, required

# A new manifest type is only provable when every returned stream is reader-healthy
# AND identity/duration matched under complete native evidence.
for required in (
    "assessNativeEvidence",
    "routeMode !== 'capability_probe'",
    "healthyPlayers === route.returned",
    "identityMatches === route.returned",
    "identityUnknown === 0",
    "identityContradictions === 0",
    "requireCrossDeviceConfirmationBeforeManifestMutation: true",
    "manifestMutationAllowed: false",
    "FIELD_NATIVE_MEDIA_CAPABILITY_PROVEN",
    "module.exports = { analyzeMediaTypeCapabilities }",
):
    assert required in capability_analyzer, required
for required in (
    "analyzeMediaTypeCapabilities",
    "learningAllowed: evidence.complete",
    "productionManifestMutationAllowed: false",
    "requireCrossDeviceConfirmation: true",
    "FIELD_NATIVE_MEDIA_CAPABILITY_BRAIN_PROPOSAL",
):
    assert required in capability_brain, required
for required in (
    "route_mode=capability_probe",
    "diagnose-native-media-capabilities.mjs",
    "native-media-capabilities-brain.json",
    "capability_evidence_incomplete",
    "FIELD_NATIVE_MEDIA_CAPABILITY_ARTIFACT",
):
    assert required in collection_analyzer, required

# Android suites instrument the official client, install the repository through
# Nuvio, run visual capture, and persist ONLY structured sanitized evidence.
for suite, client in ((tv_suite, "tv"), (mobile_suite, "mobile")):
    for required in (
        "instrument_native_client_evidence.py",
        "augment_native_corpus_request_contract.py",
        "augment_native_provider_loading.py",
        "watch_native_device_frontend.sh",
        "capture_native_device_frontend.sh",
        "NiakvioCorpus:I NiakvioEvidence:I",
        f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client={client}",
        "gate_native_reader_coverage.cjs",
        "gate_native_reader_result.cjs",
        "official_repository_loading=true",
    ):
        assert required in suite, (client, required)
    assert "PluginManager:D" not in suite, (client, "raw PluginManager log persisted")
    assert "PluginRepository:D" not in suite, (client, "raw PluginRepository log persisted")
    assert "PluginRuntime:I" not in suite, (client, "raw PluginRuntime log persisted")

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
    "augment_native_provider_loading.py",
    "augment_native_desktop_player.py",
    "complete_native_desktop_frontend_phases.py",
    "NIAKVIO_PRIMARY_STREAM_SCOPE",
    "gate_native_reader_coverage.cjs",
    "gate_native_reader_result.cjs",
    "official_repository_loading=true",
    'rm -f "$GRADLE_LOG"',
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
