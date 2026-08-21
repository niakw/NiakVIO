#!/usr/bin/env python3
"""Fail closed if native reader labs make playback easier than real Nuvio.

A human-UX reader lab may stage NiakVIO, invoke production Nuvio playback entry points
and record sanitized evidence. It must never repair the OS, grant extra network
capabilities, elevate the process, construct a friendlier player, rewrite streams or
consume one-shot media before Nuvio's production player does.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

android = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
desktop = (ROOT / "scripts/augment_native_desktop_player.py").read_text(encoding="utf-8")
resolver = (ROOT / "scripts/resolve_native_repository.sh").read_text(encoding="utf-8")
desktop_suite = (ROOT / "scripts/run_native_corpus_desktop_suite.sh").read_text(encoding="utf-8")
android_transport = (ROOT / "scripts/configure_native_android_lab_transport.py").read_text(encoding="utf-8")
mobile_hardener = (ROOT / "scripts/harden_nuvio_mobile_device_test.py").read_text(encoding="utf-8")
bootstrap = (ROOT / "scripts/native_client_test_bootstrap.py").read_text(encoding="utf-8")
checkout_audit = (ROOT / "scripts/audit_native_client_checkout.py").read_text(encoding="utf-8")
reader_acceptance = (ROOT / "scripts/prepare_native_reader_acceptance.py").read_text(encoding="utf-8")
client_prepare = (ROOT / "scripts/prepare_native_corpus_client.py").read_text(encoding="utf-8")
corpus = (ROOT / "scripts/prepare_native_corpus_validation.py").read_text(encoding="utf-8")
request_contract = (ROOT / "scripts/augment_native_corpus_request_contract.py").read_text(encoding="utf-8")
provider_loading = (ROOT / "scripts/augment_native_provider_loading.py").read_text(encoding="utf-8")

# Android must use Nuvio's production entries, not a lab-created ExoPlayer.
for required in (
    "Screen.Player.createRoute",
    "NuvioNavHost",
    "LastPlaybackDiagnostics",
    "PlatformPlayerSurface",
    "nuvio-tv-production",
    "nuvio-mobile-production",
):
    assert required in android, required
for forbidden in (
    "ExoPlayer.Builder",
    "PlayerPlaybackNetworking.createDataSourceFactory",
    "PlatformPlaybackDataSourceFactory.create",
    "setDefaultRequestProperties",
    'playbackHeaders["Range"]',
    'playbackHeaders["Referer"]',
    'playbackHeaders["Origin"]',
):
    assert forbidden not in android, forbidden

# Desktop also uses the actual production player surface and lets Nuvio choose its
# own decoder/settings. Direct NativePlayerController construction is forbidden.
assert "PlatformPlayerSurface(" in desktop
assert "sourceHeaders = headers.orEmpty()" in desktop
for forbidden in (
    "NativePlayerController(",
    "NativePlayerHost(",
    "decoderPriority = 1",
    "nvidiaRtxSuperResolutionEnabled = false",
    "controller.attach(",
):
    assert forbidden not in desktop, forbidden

# Production player first, independent diagnostic network probe second.
android_reader = android.index("val reader = probeNativePlayer(row.url, row.headers, row.type")
android_transport_call = android.index("val transport = probeTransport(row.url, row.headers)")
assert android_reader < android_transport_call
desktop_reader = desktop.index("val reader = probeDesktopProductionPlayer(row.url, row.headers, row.type")
desktop_transport_call = desktop.index("val transport = probeTransport(row.url, row.headers)")
assert desktop_reader < desktop_transport_call

# OS/process policy must never be relaxed for a green result.
for text, label in ((resolver, "resolver"), (desktop_suite, "desktop-suite")):
    for forbidden in ("sudo -n", "sudo ", "--add-opens", "ALL-UNNAMED", "privileged_client=1"):
        assert forbidden not in text, f"{label}:{forbidden}"
assert "root_execution_forbidden" in desktop_suite
assert "local_server_not_ready_unprivileged" in resolver

# Android transport helper is a validator only: no cleartext/network-security/permission grant.
assert "validate_manifest" in android_transport
assert "modified=false" in android_transport
assert '.set(f"{ANDROID}usesCleartextTraffic"' not in android_transport
assert "android.permission.INTERNET" not in android_transport

# Historical Mobile hardener is a strict no-op.
assert "leaving Nuvio checkout unchanged" in mobile_hardener
for forbidden in (
    "write_text(",
    "write_bytes(",
    "configure_manifest",
    "pickFirsts",
    "libc++_shared.so",
    "sentry-android-gradle",
    "io.sentry.android.gradle",
    "tools:replace",
    "usesCleartextTraffic",
    "networkSecurityConfig",
    "android.permission.INTERNET",
):
    assert forbidden not in mobile_hardener, f"mobile-hardener:{forbidden}"

# The only supported Android checkout edits are test plumbing. The shared bootstrap
# must never manufacture a production network/player/runtime capability.
for required in (
    "enable_mobile_device_tests",
    "enable_tv_tests",
    "withDeviceTest {",
    "androidDeviceTest by getting",
    "testInstrumentationRunner",
    "androidTestImplementation",
    "runtime_mutation=false",
):
    assert required in bootstrap, required
for forbidden in (
    "AndroidManifest.xml",
    "android.permission.INTERNET",
    "usesCleartextTraffic",
    "networkSecurityConfig",
    "cleartextTrafficPermitted",
    "PlayerPlaybackNetworking",
    "PlatformPlaybackDataSourceFactory",
    "ExoPlayer.Builder",
    "setDefaultRequestProperties",
    "PluginRepository.clearLocalState",
):
    assert forbidden not in bootstrap, f"bootstrap:{forbidden}"

# Every active preparation entry point uses the shared test-only bootstrap and then
# audits the actual Nuvio checkout before Gradle/player execution.
for text, label in ((reader_acceptance, "reader-acceptance"), (client_prepare, "client-prepare")):
    assert "from native_client_test_bootstrap import" in text, label
    assert "audit_checkout(" in text, label
    assert "corpus.enable_mobile_device_tests" not in text, label
assert "enable_mobile_device_tests(repo)" in reader_acceptance
assert "enable_mobile_device_tests(mobile)" in client_prepare
assert "enable_tv_tests(repo)" in reader_acceptance
assert "enable_tv_tests(tv)" in client_prepare

# Checkout audit is fail-closed on both path scope and forbidden runtime tokens.
for required in (
    "git",
    "status",
    "--porcelain=v1",
    "runtime_mutation=false",
    "android.permission.INTERNET",
    "usesCleartextTraffic",
    "networkSecurityConfig",
    "PlayerPlaybackNetworking",
    "composeApp/src/androidDeviceTest/",
    "app/src/androidTest/",
):
    assert required in checkout_audit, required
assert "native human-UX lab mutated runtime-owned path" in checkout_audit
assert "native human-UX lab introduced forbidden runtime mutation" in checkout_audit

# No playback-row rewriting/ranking inside the Lab preparation path.
for text, label in (
    (corpus, "corpus"),
    (request_contract, "request-contract"),
    (provider_loading, "provider-loading"),
):
    for forbidden in (
        "row.headers =",
        "row.url =",
        "rows.sorted",
        "rows.sortBy",
        "rows.sortWith",
        "copy(url =",
        "copy(headers =",
        "repairStream",
        "rewriteStream",
    ):
        assert forbidden not in text, f"{label}:{forbidden}"

# Official repository/provider state remains warm; no test-only reset to manufacture
# a different user profile or hide cache-related playback behavior.
assert "PluginRepository.clearLocalState()" not in provider_loading
assert "officialPluginManager.executeScraper(loadedScraper" in provider_loading
assert "PluginRepository.executeScraper(loadedScraper" in provider_loading

print("native human UX observational-purity tests passed")
