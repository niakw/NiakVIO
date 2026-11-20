#!/usr/bin/env python3
"""Architecture contract for native human-UX playback evidence.

This test intentionally focuses on invariants that must never regress: official Nuvio
repository/provider loading, production player entry points, observational evidence,
ordinary OS privileges and fail-closed Brain learning. Detailed codegen behavior has
its own dedicated tests.
"""
import re
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
ios_player = text("scripts/prepare_native_ios_reader_acceptance.py")
native_corpus = text("scripts/prepare_native_corpus_validation.py")
android_transport = text("scripts/configure_native_android_lab_transport.py")
tv_suite = text("scripts/run_native_corpus_tv_suite.sh")
mobile_suite = text("scripts/run_native_corpus_mobile_suite.sh")
desktop_suite = text("scripts/run_native_corpus_desktop_suite.sh")
completeness = text("scripts/native_evidence_completeness.cjs")
diagnosis = text("engine_v2/scripts/diagnose-native-reader.mjs")
reader_gate = text("scripts/gate_native_reader_result.cjs")
coverage_gate = text("scripts/gate_native_reader_coverage.cjs")
player_reach_gate = text("scripts/gate_native_player_reached.cjs")
mobile_android_workflow = text(".github/workflows/native-mobile-android-reader.yml")
tv_workflow = mobile_android_workflow
mobile_ios_workflow = text(".github/workflows/native-mobile-ios-reader.yml")
desktop_workflow = text(".github/workflows/native-desktop-reader-acceptance.yml")
learning_sync = text(".github/workflows/native-reader-learning-sync.yml")

# Canonical media route traversal remains explicit. Native acceptance runs only
# the declared fixture route; cross-type capability discovery belongs to Learning/Deep.
for required in (
    'CANONICAL = {"movie", "tv", "anime"}',
    "ProviderRequestRoute",
    'listOf<String>(fixtureMediaType).filter {{ it in declared }}',
    'ProviderRequestRoute(type)',
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
for workflow in (tv_workflow, mobile_android_workflow, mobile_ios_workflow, desktop_workflow):
    assert "check_nuvio_client_upstreams.py" in workflow
    assert "resolve_nuvio_lab_heads.py" in workflow
    assert "workflow_dispatch:" in workflow
    assert "\n  push:" in workflow
    assert "\n  pull_request:" not in workflow
    assert "get('accepted_ref') or '')" not in workflow
assert "Checkout latest official NuvioTV HEAD" in tv_workflow
assert "Checkout latest official NuvioMobile HEAD" in mobile_android_workflow
assert "Checkout exact official NuvioMobile HEAD" in mobile_ios_workflow
assert "Checkout latest official NuvioDesktop HEAD" in desktop_workflow

# Reader repair memory is historical but only influences the exact client revision
# fingerprint that produced it. Legacy/unscoped memory is never recycled after drift.
for required in (
    "exact-runtime-fingerprint-only",
    "legacyUnscopedExcluded",
    "runtimeFingerprint",
    "entry_fingerprint(row) == fingerprint",
):
    assert required in reader_runtime_scope, required
# Native Labs are independent evidence producers. They do not run Brain repair,
# merge cross-client state, or mutate provider code. Sanitized diagnoses may be
# imported automatically only from the trusted same-repository main Device Corpus
# workflow, or manually by exact run id. The Learning branch stays fail-closed.
for workflow in (tv_workflow, mobile_android_workflow, mobile_ios_workflow, desktop_workflow):
    assert "brain-reader-repair" not in workflow
    assert "build_native_reader_brain_repair.py" not in workflow
    assert "compare_native_reader_brain_repair.py" not in workflow
assert "workflow_run:" in learning_sync
assert 'workflows: ["NATIVE - Device Corpus Tests"]' in learning_sync
assert "github.event.workflow_run.head_repository.full_name == github.repository" in learning_sync
assert "github.event.workflow_run.head_branch == 'main'" in learning_sync
assert "github.event.workflow_run.conclusion != 'cancelled'" in learning_sync
assert "github.event.workflow_run.conclusion != 'skipped'" in learning_sync
assert "permissions: {}" in learning_sync
assert "productionWritesAllowed===true||x.publicationAllowed===true" in learning_sync
assert "workflow_dispatch:" in learning_sync
assert "Exact completed native reader run ID to import manually" in learning_sync
assert '"native-tv-full-$RUN_ID"' in learning_sync
assert '"native-mobile-android-full-$RUN_ID"' in learning_sync
assert '"native-mobile-ios-full-$RUN_ID"' in learning_sync
assert '"native-desktop-full-*-$RUN_ID"' in learning_sync

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
    "forcedEngine: AndroidPlaybackEngine? = null",
    "playbackEngine = forcedEngine",
    "FIELD_NATIVE_ENGINE_COMPARE client=mobile",
    "AndroidPlaybackEngine.ExoPlayer",
    "AndroidPlaybackEngine.Libmpv",
):
    assert required in android_player, required
for forbidden in (
    "ExoPlayer.Builder",
    "PlayerPlaybackNetworking.createDataSourceFactory",
    "PlatformPlaybackDataSourceFactory.create",
):
    assert forbidden not in android_player, forbidden

# Multi-audio proof is test-owned and consumes only production player APIs/UI.
# It never patches Nuvio production code: Mobile/Desktop use PlayerEngineController,
# iOS uses the official bridge and TV observes the actual Audio Tracks overlay.
for required in (
    "PlayerEngineController",
    "getAudioTracks()",
    "audio_track_count=",
    "audio_track_languages64=",
    "UiDevice.getInstance(instrumentation)",
    "R.string.cd_audio_tracks",
    'By.clazz("android.widget.RadioButton")',
    "track.contentDescription",
):
    assert required in android_player, required
for required in (
    "PlayerEngineController",
    "getAudioTracks()",
    "audio_track_count=",
    "audio_track_languages64=",
):
    assert required in desktop_player, required
for required in (
    "getAudioTrackCount()",
    "getAudioTrackLang(index)",
    "audioTrackCount",
    "audioTrackLanguages",
    "masterAudioTrackLanguages",
    "FIELD_NATIVE_IOS_ROW",
    "logicalProvider",
    "is StreamRowObservation -> json.encodeToString(payload)",
    "host = hostOnly(row.url)",
):
    assert required in ios_player, required
assert "logical_provider64=" in native_corpus
assert "hlsTrackTopology" in native_corpus
assert "audioVariantMatrix" in native_corpus
assert "subtitleVariantMatrix" in native_corpus
assert "subtitleTrackCount" in native_corpus
assert "subtitleTrackLanguages" in native_corpus
assert "LANGUAGE" in native_corpus
assert 'startsWith("#EXT-X-MEDIA", ignoreCase = true)' in native_corpus
assert "TYPE" in native_corpus and "AUDIO" in native_corpus
assert 'androidx.test.uiautomator:uiautomator:2.3.0' in native_corpus

assert "PlatformPlayerSurface(" in desktop_player
assert "production_surface=true" in desktop_player
for player_source in (android_player, desktop_player):
    assert "(snapshot.videoWidth > 0 && snapshot.videoHeight > 0)" in player_source
    assert "snapshot.positionMs > 0L || snapshot.durationMs > 0L" not in player_source
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
# terminal FIELD_NATIVE_PLAYER row from the production surface can satisfy reach only
# when it proves ready/ended playback; errors/timeouts/short-media remain diagnostic.
for required in (
    "FIELD_NATIVE_PLAYER ",
    "-production$",
    "player_setup",
    "NO_LAUNCH_INTENT",
    "production_player_never_reached",
    "FIELD_NATIVE_PLAYER_REACH_GATE",
    "production_playback_never_verified",
    "playback_verified=",
    "production_surface",
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
for workflow in (tv_workflow, mobile_android_workflow, desktop_workflow):
    assert "NIAKVIO_PRIMARY_STREAM_SCOPE: all" in workflow
assert 'NIAKVIO_TARGET_PROVIDER: declared-type' in tv_workflow
assert 'NIAKVIO_TARGET_PROVIDER: declared-type' in mobile_android_workflow
assert 'NIAKVIO_TARGET_PROVIDER: declared-type' in desktop_workflow

# Evidence completeness and Brain learning remain fail-closed outside the smoke. The
# native-reader smoke may suppress the diagnostic process exit only; it does not turn
# incomplete evidence into usable learning or permit provider mutation.
for required in (
    "missing_repository_load:",
    "provider_route_terminal:",
    "player_terminal:",
    "http_terminal:",
    "missing_frontend_phase:",
    "multi_audio_player_observation_missing:",
    "multi_audio_player_ui_observation_empty:",
    "multi_audio_player_collapsed:",
    "integrated_subtitle_ui_observation_empty:",
    "multiAudioVerified",
):
    assert required in completeness, required
for required in (
    "evidenceComplete",
    "evidenceUsable: evidence.complete",
    "learningAllowed: providerLearningAllowed",
    "repairPlanningAllowed: providerLearningAllowed",
    "providerMutationRequiresCrossClientConsensus: true",
    "harnessObservationReaderFailures",
    "clientRuntimeFailureLearningAllowed: false",
    "providerLoadJsMutationAllowed: false",
    "const nonblockingSmoke = process.env.NIAKVIO_BRAIN_NONBLOCKING === '1'",
    "if (!evidence.complete && !nonblockingSmoke) process.exitCode = 2",
    "nonblockingSmoke,",
):
    assert required in diagnosis, required
assert "FIELD_NATIVE_CAPABILITY_PROBE_REJECTED" in reader_gate

# TRANSPORT_HELPERS is a Python RAW string emitting Kotlin triple-quoted
# Regex strings. Double escaping wrongly matches literal backslashes, not
# HLS audio/quality declarations. Execute the generated patterns on real shapes.
assert "TRANSPORT_HELPERS = r'''" in native_corpus
transport_source = native_corpus.split("TRANSPORT_HELPERS = r'''", 1)[1].split("\n'''", 1)[0]
attribute_regex = re.search(
    r'val match = Regex\(\s*"""(.*?)""",\s*RegexOption\.IGNORE_CASE',
    transport_source, re.DOTALL,
)
assert attribute_regex is not None
for key, value, example in (
    ("TYPE", "AUDIO", 'TYPE=AUDIO,GROUP-ID="audio",LANGUAGE="fr"'),
    ("GROUP-ID", "audio", 'TYPE=AUDIO,GROUP-ID="audio",LANGUAGE="fr"'),
    ("LANGUAGE", "fr", 'TYPE=AUDIO,GROUP-ID="audio",LANGUAGE="fr"'),
    ("LANGUAGE", "en", 'TYPE=AUDIO,GROUP-ID="audio",LANGUAGE="en"'),
    ("TYPE", "SUBTITLES", 'TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="fr"'),
):
    candidate = attribute_regex.group(1).replace("${key}", re.escape(key))
    match = re.search(candidate, example, re.IGNORECASE)
    assert match, (key, example, candidate)
    parsed = match.group(1) or match.group(2)
    assert parsed == value, (key, parsed, value)
height_regex = re.search(
    r'val height = Regex\("""(.*?)""", RegexOption\.IGNORE_CASE\)',
    transport_source,
)
assert height_regex is not None
for text, expected in (
    ('BANDWIDTH=2200000,RESOLUTION=1280x720,AUDIO="audio"', 720),
    ('BANDWIDTH=4600000,RESOLUTION = 1920x1080,AUDIO="audio"', 1080),
    ('BANDWIDTH=14000000,RESOLUTION=3840x2160,AUDIO="audio"', 2160),
):
    match = re.search(height_regex.group(1), text, re.IGNORECASE)
    assert match and int(match.group(1)) == expected, (text, height_regex.group(1))
assert r'\\s*${key}' not in attribute_regex.group(1)
assert r'RESOLUTION\\s*' not in height_regex.group(1)

print("full native human UX evidence contract tests passed")
