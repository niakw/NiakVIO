#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINNED_MANIFEST_URL = (
    "https://raw.githubusercontent.com/niakw/NiakVIO/"
    "0123456789abcdef0123456789abcdef01234567/manifest.json"
)


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


corpus = load("native_corpus_validation", "scripts/prepare_native_corpus_validation.py")
reader = load("native_player_diag_codegen", "scripts/native_player_diagnostics_codegen.py")
contract = load("native_request_contract", "scripts/augment_native_corpus_request_contract.py")
provider_loading = load("native_provider_loading", "scripts/augment_native_provider_loading.py")
desktop_player = load("native_desktop_player", "scripts/augment_native_desktop_player.py")

manifest = ROOT / "manifest.json"
providers = corpus.manifest_providers()
assert len(providers) >= 80
# Keep generation compact while deliberately covering movie-only, tv-capable and
# anime-capable declarations if available.
selected = []
for wanted in ("movieshunt", "purstream", "anime-sama"):
    row = next((p for p in providers if str(p["id"]).casefold() == wanted), None)
    if row is not None:
        selected.append({**row, "asset": f"p{len(selected):03d}.js"})
assert len(selected) >= 2

with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)

    # TV / movie: generated corpus -> official Media3 reader -> route contract ->
    # real PluginManager repository loading. No direct PluginRuntime execution may
    # remain as the primary provider path.
    movie = corpus.fixture_by_slug("sinners-2025")
    tv_source = corpus.android_test(movie, selected, "tv")
    tv_source = reader.augment_android_test(
        tv_source,
        client="tv",
        expected_duration_minutes=movie.get("expectedDurationMinutes"),
        max_player_probes=4,
    )
    tv_path = tmp / "Tv.kt"
    tv_path.write_text(tv_source, encoding="utf-8")
    contract.augment(tv_path, "tv", "sinners-2025", manifest)
    provider_loading.augment(tv_path, "tv", manifest, PINNED_MANIFEST_URL, "")
    tv_out = tv_path.read_text(encoding="utf-8")
    assert "FIELD_NATIVE_UI_LAUNCHED client=tv" in tv_out
    assert "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv" in tv_out
    assert "FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv" in tv_out
    assert "PluginManager.addRepository" not in tv_out  # instance call below is intentional
    assert "manager.addRepository(repositoryManifestUrl)" in tv_out
    assert "officialPluginManager.executeScraper(loadedScraper" in tv_out
    assert "runtime.executePlugin(" not in tv_out
    assert "request_type=$requestMediaType route_mode=$routeMode" in tv_out
    assert "mediaType = requestMediaType" not in tv_out  # direct runtime call was replaced
    assert "FIELD_NATIVE_PLAYER_BEGIN client=tv" in tv_out
    assert "PlayerPlaybackNetworking.createDataSourceFactory" in tv_out

    # Mobile / anime: the route contract keeps declared + capability_probe anime/tv
    # routes, then the official PluginRepository supplies the loaded scraper.
    anime = corpus.fixture_by_slug("jujutsu-kaisen-s01e01")
    mobile_source = corpus.android_test(anime, selected, "mobile")
    mobile_source = reader.augment_android_test(
        mobile_source,
        client="mobile",
        expected_duration_minutes=anime.get("expectedDurationMinutes"),
        max_player_probes=4,
    )
    mobile_path = tmp / "Mobile.kt"
    mobile_path.write_text(mobile_source, encoding="utf-8")
    contract.augment(mobile_path, "mobile", "jujutsu-kaisen-s01e01", manifest)
    provider_loading.augment(mobile_path, "mobile", manifest, PINNED_MANIFEST_URL, "")
    mobile_out = mobile_path.read_text(encoding="utf-8")
    assert 'listOf("anime", "tv").map' in mobile_out
    assert '"capability_probe"' in mobile_out
    assert "requestRoute.declared" in mobile_out
    assert "FIELD_NATIVE_UI_LAUNCHED client=mobile" in mobile_out
    assert "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=mobile" in mobile_out
    assert "PluginRepository.addRepository(repositoryManifestUrl)" in mobile_out
    assert "PluginRepository.executeScraper(loadedScraper" in mobile_out
    assert "PluginRuntime.executePlugin(" not in mobile_out
    assert "PlatformPlaybackDataSourceFactory.create" in mobile_out
    assert "FIELD_NATIVE_PLAYER client=mobile" in mobile_out
    assert "route_mode=$routeMode" in mobile_out

    # Desktop: route contract -> official PluginRepository loading -> official native
    # Desktop player -> visual phase augmentation. Prove both macOS and Windows
    # platform filtering source generation without touching the network.
    for platform in ("macos", "windows"):
        desktop_source = corpus.desktop_test(anime, selected)
        desktop_path = tmp / f"Desktop-{platform}.kt"
        desktop_path.write_text(desktop_source, encoding="utf-8")
        contract.augment(desktop_path, "desktop", "jujutsu-kaisen-s01e01", manifest)
        provider_loading.augment(desktop_path, "desktop", manifest, PINNED_MANIFEST_URL, platform)
        desktop_player.augment(desktop_path, int(anime.get("expectedDurationMinutes") or 0), "all")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/complete_native_desktop_frontend_phases.py"), str(desktop_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        desktop_out = desktop_path.read_text(encoding="utf-8")
        for required in (
            "PluginRepository.addRepository(repositoryManifestUrl)",
            "PluginRepository.executeScraper(loadedScraper",
            "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=desktop",
            "NativePlayerController",
            "NativePlayerHost",
            "probeDesktopNativePlayer",
            "FIELD_NATIVE_PLAYER_BEGIN client=desktop",
            "route_mode=$routeMode",
            "engine=native-desktop",
            'captureDesktopPhase("ui-launched"',
            'captureDesktopPhase("repository-load"',
            'captureDesktopPhase("repository-loaded"',
            'captureDesktopPhase("provider-load-state"',
            'captureDesktopPhase("provider-http-request"',
            'captureDesktopPhase("provider-http-response"',
            'captureDesktopPhase("player-start"',
            'captureDesktopPhase("player-result"',
        ):
            assert required in desktop_out, f"{platform}:{required}"
        assert "PluginRuntime.executePlugin(" not in desktop_out
        assert "rows.take(" not in desktop_out, "all-stream Desktop proof must not sample rows"

print("native evidence Kotlin codegen pipeline tests passed")
