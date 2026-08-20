#!/usr/bin/env python3
"""Fail closed if native reader labs start repairing playback on the client's behalf.

Labs may stage the current NiakVIO provider output, invoke the official client path and
record sanitized evidence. They must not rewrite a returned stream, drop/synthesize
playback headers, reorder candidates for the player, or consume a one-shot URL before
the official reader does.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

android = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
desktop = (ROOT / "scripts/augment_native_desktop_player.py").read_text(encoding="utf-8")
corpus = (ROOT / "scripts/prepare_native_corpus_validation.py").read_text(encoding="utf-8")
request_contract = (ROOT / "scripts/augment_native_corpus_request_contract.py").read_text(encoding="utf-8")
provider_loading = (ROOT / "scripts/augment_native_provider_loading.py").read_text(encoding="utf-8")

# Android: exact provider playback headers and URL are handed to Media3.
assert "val playbackHeaders = headers.orEmpty()" in android
assert "nativeReaderDataSource(context, playbackHeaders)" in android
assert "player.setMediaItem(MediaItem.fromUri(url))" in android
assert ".filterKeys" not in android
for forbidden in (
    'playbackHeaders["Range"]',
    'playbackHeaders["Referer"]',
    'playbackHeaders["Origin"]',
    'playbackHeaders["Cookie"]',
    'playbackHeaders["Authorization"]',
    'playbackHeaders["User-Agent"]',
    "playbackHeaders +",
    "playbackHeaders.toMutableMap",
):
    assert forbidden not in android, forbidden

# The player must consume the stream before the diagnostic transport probe. A
# preflight GET can consume/expire signed one-shot links and manufacture false reds.
android_reader = android.index("val reader = probeNativePlayer(row.url, row.headers")
android_transport = android.index("val transport = probeTransport(row.url, row.headers)")
assert android_reader < android_transport

# Desktop: same exact source URL/header contract into the official controller.
assert "sourceUrl = url" in desktop
assert "sourceHeaders = headers.orEmpty()" in desktop
assert ".filterKeys" not in desktop
for forbidden in (
    'sourceHeaders = headers.orEmpty() +',
    'sourceHeaders = headers.orEmpty().toMutableMap',
    'sourceHeaders = mapOf(',
):
    assert forbidden not in desktop, forbidden

desktop_reader = desktop.index("val reader = probeDesktopNativePlayer(row.url, row.headers")
desktop_transport = desktop.index("val transport = probeTransport(row.url, row.headers)")
assert desktop_reader < desktop_transport

# The base corpus contains a transport probe, but augmentation replaces it after the
# player. It must not contain stream-repair helpers or candidate ranking logic.
for forbidden in (
    "repairStream",
    "normalizeStream",
    "rewriteStream",
    "rows.sorted",
    "rows.sortBy",
    "rows.sortWith",
    "row.headers =",
    "row.url =",
    "copy(url =",
    "copy(headers =",
):
    assert forbidden not in corpus, forbidden

# Request-contract and official repository-loading augmentation may select valid
# media routes/providers, but must not mutate returned playback rows.
for text, label in ((request_contract, "request-contract"), (provider_loading, "provider-loading")):
    for forbidden in (
        "row.headers =",
        "row.url =",
        "rows.sorted",
        "rows.sortBy",
        "rows.sortWith",
        "copy(url =",
        "copy(headers =",
    ):
        assert forbidden not in text, f"{label}:{forbidden}"

# Platform exclusions affect whether the official client can load a provider; they
# are not allowed to filter or rewrite a provider's returned streams.
assert "platformExcludedProviders" in provider_loading
assert "officialPluginManager.executeScraper(loadedScraper" in provider_loading
assert "PluginRepository.executeScraper(loadedScraper" in provider_loading

print("native lab observational purity tests passed")
