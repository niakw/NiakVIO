#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


request_contract = text("scripts/augment_native_corpus_request_contract.py")
provider_loading = text("scripts/augment_native_provider_loading.py")
repository_http = text("scripts/instrument_native_repository_http_evidence.py")
repository_resolver = text("scripts/resolve_native_repository.sh")
completeness = text("scripts/native_evidence_completeness.cjs")
collection_analyzer = text("scripts/analyze_native_corpus_collection.cjs")
diagnosis = text("engine_v2/scripts/diagnose-native-reader.mjs")
capability_brain = text("engine_v2/scripts/diagnose-native-media-capabilities.mjs")
reader_gate = text("scripts/gate_native_reader_result.cjs")
capability_analyzer = text("scripts/analyze_native_media_type_capabilities.cjs")
tv_suite = text("scripts/run_native_corpus_tv_suite.sh")
mobile_suite = text("scripts/run_native_corpus_mobile_suite.sh")
desktop_suite = text("scripts/run_native_corpus_desktop_suite.sh")
desktop_frontend = text("scripts/complete_native_desktop_frontend_phases.py")
android_workflow = text(".github/workflows/native-android-route-reader.yml")
desktop_workflow = text(".github/workflows/native-desktop-reader-acceptance.yml")
reader_acceptance = text("scripts/prepare_native_reader_acceptance.py")
restage = text("scripts/restage_native_corpus_client.py")
desktop_player = text("scripts/augment_native_desktop_player.py")

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
# Generated empty collections are explicitly typed: native Kotlin compilers must
# never be asked to infer T from an empty literal in code emitted by this harness.
for required in (
    "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN",
    "FIELD_NATIVE_REPOSITORY_LOAD_RESULT",
    "FIELD_NATIVE_REPOSITORY_LOAD_ERROR",
    "FIELD_NATIVE_REPOSITORY_CACHE_HIT",
    "FIELD_NATIVE_PROVIDER_LOAD_RESULT",
    "FIELD_NATIVE_PROVIDER_LOAD_ERROR",
    "FIELD_NATIVE_PROVIDER_LOAD_SKIPPED",
    "reason=repository_install_failed",
    "return manager to emptyMap<String, com.nuvio.tv.domain.model.ScraperInfo>()",
    "return emptyMap<String, PluginScraper>()",
    "private val platformExcludedProviders: Set<String>",
    'return "emptySet<String>()"',
    'return "setOf<String>("',
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
assert "return manager to emptyMap()" not in provider_loading
assert "return emptyMap()" not in provider_loading
assert "PluginRepository.clearLocalState()" not in provider_loading, "native lab must preserve Nuvio profile/plugin state"

# Repository network evidence is passive and sanitized, and applies to the exact
# pinned GitHub candidate or a content-addressed loopback repair candidate only.
# The Python source is an f-string, hence doubled braces are required to emit the
# runtime Kotlin regex /candidate-[0-9a-f]{32}/.
for required in (
    "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST",
    "FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE",
    "FIELD_NATIVE_REPOSITORY_HTTP_ERROR",
    'rawUrl.host.equals("raw.githubusercontent.com"',
    'setOf("127.0.0.1", "localhost", "10.0.2.2")',
    'Regex("/candidate-[0-9a-f]{{32}}/")',
    "response_header_names=$responseHeaderNames",
    "source=$cacheSource",
):
    assert required in repository_http, required
for required in (
    "content-addressed",
    "candidate-${content_key}",
    "manifest + every provider",
    "NIAKVIO_LOCAL_REPOSITORY_KEY",
):
    assert required in repository_resolver, required

# Backend + frontend evidence is part of the validity contract, not optional debug.
for required in (
    "missing_runtime_instrumentation",
    "missing_repository_load:",
    "missing_repository_http:",
    "repository_http_terminal:",
    "repository_http_pair:",
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
    "repository-load-error",
    "repository-http-request",
    "repository-http-terminal",
    "provider-load-state",
    "provider-loading",
    "provider-http-request",
    "provider-http-terminal",
    "provider-result",
    "player-start",
    "player-result",
    "corpus-end",
):
    assert required in completeness, required
# Legacy *-response screenshots remain accepted only as migration aliases; the
# canonical requirement itself is terminal because either HTTP response or error
# closes the request pair.
for required in (
    "phase === 'repository-http-terminal'",
    "? 'repository-http-response'",
    "phase === 'provider-http-terminal'",
    "? 'provider-http-response'",
):
    assert required in completeness, required
assert "repository_load_failed:" not in completeness

# Brain must be fail-closed when any evidence link is missing, and capability
# probes must never become provider-repair plans. Complete repository/provider-load
# evidence is learnable even when no player row exists.
for required in (
    "assessNativeEvidence",
    "evidenceComplete",
    "evidenceProblems",
    "learningAllowed: evidence.complete",
    "repairPlanningAllowed: evidence.complete",
    "repositoryLearningAllowed: evidence.complete",
    "providerLoadJsMutationAllowed: false",
    "coreOrManifestLoadProposalAllowed: evidence.complete",
    "capabilityLearningAllowed: evidence.complete",
    "capabilityPromotionRequiresIdentityProof: true",
    "const declaredRows = readerRows.filter",
    "const capabilityRows = readerRows.filter",
    "const plans = evidence.complete ? failures.map",
    "providerLoadIssues",
    "providerLoadPriorities",
    "if (!evidence.complete) process.exitCode = 2",
):
    assert required in diagnosis, required
assert "readerRows.length === 0 || !evidence.complete" not in diagnosis
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

# Android suites instrument the official client AND its repository HTTP stack,
# install through Nuvio, run visual capture, and persist only sanitized evidence.
for suite, client in ((tv_suite, "tv"), (mobile_suite, "mobile")):
    for required in (
        "instrument_native_client_evidence.py",
        "instrument_native_repository_http_evidence.py",
        "augment_native_corpus_request_contract.py",
        "augment_native_provider_loading.py",
        "watch_native_device_frontend.sh",
        "capture_native_device_frontend.sh",
        "NiakvioCorpus:I NiakvioEvidence:I",
        f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client={client}",
        "gate_native_reader_coverage.cjs",
        "gate_native_reader_result.cjs",
        "official_repository_loading=true",
        "repository_http_evidence=true",
    ):
        assert required in suite, (client, required)
    assert "PluginManager:D" not in suite, (client, "raw PluginManager log persisted")
    assert "PluginRepository:D" not in suite, (client, "raw PluginRepository log persisted")
    assert "PluginRuntime:I" not in suite, (client, "raw PluginRuntime log persisted")

# Route workflows share one boot/profile per client. Exhaustive all-provider/all-
# stream intent remains declared by the workflow, while PR staging is bounded by
# event-aware preparation so every push no longer spends an hour in native readers.
for fixture in ("sinners-2025", "breaking-bad-s01e01", "jujutsu-kaisen-s01e01"):
    assert fixture in android_workflow, fixture
for required in (
    "NIAKVIO_TARGET_PROVIDER: all",
    "NIAKVIO_PRIMARY_STREAM_SCOPE: all",
    "--provider all --streams all",
    "native-evidence/tv/**",
    "native-evidence/mobile/**",
    "Execute representative routes in one TV boot",
    "Execute representative routes in one Mobile boot",
    "diagnose-native-reader.mjs",
):
    assert required in android_workflow, required
assert "matrix.fixture" not in android_workflow, "Android route fixtures must share one launched emulator profile per client"
for source, label in ((reader_acceptance, "android"), (restage, "desktop")):
    assert "GITHUB_EVENT_NAME" in source, label
    assert "NIAKVIO_PR_PROVIDER_LIMIT" in source, label
    assert "pr-bounded" in source, label
assert "DEFAULT_PR_PROVIDER_LIMIT = 4" in reader_acceptance
assert "DEFAULT_PR_PROVIDER_LIMIT = 4" in restage

# Desktop Linux is explicitly not native-reader proof. macOS/Windows build the
# official bridge once per OS, then reuse that process/Gradle profile for all three
# representative routes. PR playback is one stream per bounded fixture provider;
# trusted main/manual execution keeps the exhaustive stream path.
for required in (
    "official_nuvio_desktop_player_is_stub",
    "instrument_native_desktop_evidence.py",
    "instrument_native_repository_http_evidence.py",
    "augment_native_provider_loading.py",
    "augment_native_desktop_player.py",
    "complete_native_desktop_frontend_phases.py",
    "NIAKVIO_PRIMARY_STREAM_SCOPE",
    "gate_native_reader_coverage.cjs",
    "gate_native_reader_result.cjs",
    "official_repository_loading=true",
    "repository_http_evidence=true",
    "GRADLE_LOG=",
    'rm -f "$HTTP_LOG" "$GRADLE_LOG"',
):
    assert required in desktop_suite, required
assert "PROVIDER_ARGS[@]" not in desktop_suite, "macOS Bash 3.2 + set -u must not expand an empty provider array"
assert "PROVIDER_LOADING_URL_ARGS[@]" not in desktop_suite, "macOS Bash 3.2 + set -u must not expand an empty loading array"
for required in (
    'captureDesktopPhase("repository-loaded", fixtureSlugForLoad)',
    'captureDesktopPhase("repository-load-error", fixtureSlugForLoad)',
    'captureDesktopPhase("repository-http-request", fixtureSlugForLoad)',
    'captureDesktopPhase("repository-http-terminal", fixtureSlugForLoad)',
):
    assert required in desktop_frontend or required in provider_loading, required
for required in (
    "macos-15",
    "windows-2022",
    ":composeApp:buildMacosPlayerBridge",
    ":composeApp:buildWindowsPlayerBridge",
    "Microsoft.Web.WebView2",
    "NIAKVIO_TARGET_PROVIDER: all",
    "NIAKVIO_PRIMARY_STREAM_SCOPE: all",
    "native-evidence/desktop/**",
    "Build official macOS native player bridge once",
    "Build official Windows native player bridge once",
    "Execute all representative routes in one Desktop profile",
):
    assert required in desktop_workflow, required
assert "matrix.fixture" not in desktop_workflow, "Desktop route fixtures must share one runner per OS"
assert desktop_workflow.count("- runner: macos-15") == 1, "macOS must be launched once"
assert desktop_workflow.count("- runner: windows-2022") == 1, "Windows must be launched once"
assert "__READER_TIMEOUT_MS__" in desktop_player
assert "12_000 if pr_bounded else 25_000" in desktop_player
assert 'stream_scope = "1"' in desktop_player

print("full native evidence contract tests passed")
