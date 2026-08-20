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

# Android helper is a validator only: no cleartext/network-security/permission grant.
assert "validate_manifest" in android_transport
assert "modified=false" in android_transport
assert '.set(f"{ANDROID}usesCleartextTraffic"' not in android_transport
assert "android.permission.INTERNET" not in android_transport
assert "configure_manifest" not in mobile_hardener
assert "validate_manifest(test_manifest)" in mobile_hardener

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
