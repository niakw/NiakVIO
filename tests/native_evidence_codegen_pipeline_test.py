#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
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
    # remain as the primary provider path. Existing repository/profile state is
    # reused on subsequent fixtures rather than downloaded again.
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
    assert "FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=tv" in tv_out
    assert "FIELD_NATIVE_REPOSITORY_CACHE_HIT client=tv" in tv_out
    assert "FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv" in tv_out
    assert "reason=repository_install_failed" in tv_out
    assert "return manager to emptyMap()" in tv_out
    assert "manager.repositories.first()" in tv_out
    assert "PluginManager.addRepository" not in tv_out  # instance call below is intentional
    assert "manager.addRepository(repositoryManifestUrl)" in tv_out
    assert "officialPluginManager.executeScraper(loadedScraper" in tv_out
    assert "runtime.executePlugin(" not in tv_out
    assert "request_type=$requestMediaType route_mode=$routeMode" in tv_out
    assert "mediaType = requestMediaType" not in tv_out  # direct runtime call was replaced
    assert "FIELD_NATIVE_PLAYER_BEGIN client=tv" in tv_out
    assert "PlayerPlaybackNetworking.createDataSourceFactory" in tv_out

    # Mobile / anime: the route contract keeps declared + capability_probe anime/tv
    # routes, then the official PluginRepository supplies the loaded scraper while
    # preserving active profile/settings and the installed repository cache.
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
    assert "FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=mobile" in mobile_out
    assert "FIELD_NATIVE_REPOSITORY_CACHE_HIT client=mobile" in mobile_out
    assert "reason=repository_install_failed" in mobile_out
    assert "return emptyMap()" in mobile_out
    assert "PluginRepository.initialize()" in mobile_out
    assert "PluginRepository.uiState.value.repositories.firstOrNull" in mobile_out
    assert "PluginRepository.clearLocalState()" not in mobile_out
    assert "PluginRepository.addRepository(repositoryManifestUrl)" in mobile_out
    assert "PluginRepository.executeScraper(loadedScraper" in mobile_out
    assert "PluginRuntime.executePlugin(" not in mobile_out
    assert "PlatformPlaybackDataSourceFactory.create" in mobile_out
    assert "FIELD_NATIVE_PLAYER client=mobile" in mobile_out
    assert "route_mode=$routeMode" in mobile_out

    # Desktop deep mode: explicit all-stream proof must stay exhaustive regardless
    # of the outer CI event. PR budget behavior is validated separately below.
    original_event = os.environ.pop("GITHUB_EVENT_NAME", None)
    try:
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
                "PluginRepository.initialize()",
                "PluginRepository.uiState.value.repositories.firstOrNull",
                "PluginRepository.addRepository(repositoryManifestUrl)",
                "PluginRepository.executeScraper(loadedScraper",
                "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=desktop",
                "FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=desktop",
                "FIELD_NATIVE_REPOSITORY_CACHE_HIT client=desktop",
                "reason=repository_install_failed",
                "return emptyMap()",
                "NativePlayerController",
                "NativePlayerHost",
                "probeDesktopNativePlayer",
                "FIELD_NATIVE_PLAYER_BEGIN client=desktop",
                "route_mode=$routeMode",
                "engine=native-desktop",
                'captureDesktopPhase("ui-launched"',
                'captureDesktopPhase("repository-load"',
                'captureDesktopPhase("repository-loaded", fixtureSlugForLoad)',
                'captureDesktopPhase("repository-load-error", fixtureSlugForLoad)',
                'captureDesktopPhase("repository-http-request", fixtureSlugForLoad)',
                'captureDesktopPhase("repository-http-response", fixtureSlugForLoad)',
                'captureDesktopPhase("provider-load-state"',
                'captureDesktopPhase("provider-http-request"',
                'captureDesktopPhase("provider-http-response"',
                'captureDesktopPhase("player-start"',
                'captureDesktopPhase("player-result"',
            ):
                assert required in desktop_out, f"{platform}:{required}"
            assert "PluginRepository.clearLocalState()" not in desktop_out
            assert "PluginRuntime.executePlugin(" not in desktop_out
            assert "rows.take(" not in desktop_out, "all-stream Desktop proof must not sample rows"
            assert "25000L" in desktop_out, "deep Desktop reader timeout must remain 25s"
    finally:
        if original_event is not None:
            os.environ["GITHUB_EVENT_NAME"] = original_event

    # Pull requests intentionally cap Desktop to one stream and a 12s reader budget.
    original_event = os.environ.get("GITHUB_EVENT_NAME")
    os.environ["GITHUB_EVENT_NAME"] = "pull_request"
    try:
        pr_source = corpus.desktop_test(anime, selected)
        pr_path = tmp / "Desktop-pr.kt"
        pr_path.write_text(pr_source, encoding="utf-8")
        contract.augment(pr_path, "desktop", "jujutsu-kaisen-s01e01", manifest)
        provider_loading.augment(pr_path, "desktop", manifest, PINNED_MANIFEST_URL, "windows")
        desktop_player.augment(pr_path, int(anime.get("expectedDurationMinutes") or 0), "all")
        pr_out = pr_path.read_text(encoding="utf-8")
        assert "rows.take(1).forEachIndexed" in pr_out
        assert "12000L" in pr_out
    finally:
        if original_event is None:
            os.environ.pop("GITHUB_EVENT_NAME", None)
        else:
            os.environ["GITHUB_EVENT_NAME"] = original_event

print("native evidence Kotlin codegen pipeline tests passed")
