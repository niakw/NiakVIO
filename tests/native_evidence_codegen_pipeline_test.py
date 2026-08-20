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
selected = []
for wanted in ("movieshunt", "purstream", "anime-sama"):
    row = next((p for p in providers if str(p["id"]).casefold() == wanted), None)
    if row is not None:
        selected.append({**row, "asset": f"p{len(selected):03d}.js"})
assert len(selected) >= 2

with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)

    movie = corpus.fixture_by_slug("sinners-2025")
    tv_source = reader.augment_android_test(
        corpus.android_test(movie, selected, "tv"),
        client="tv",
        expected_duration_minutes=movie.get("expectedDurationMinutes"),
        max_player_probes=4,
    )
    tv_path = tmp / "Tv.kt"
    tv_path.write_text(tv_source, encoding="utf-8")
    contract.augment(tv_path, "tv", "sinners-2025", manifest)
    provider_loading.augment(tv_path, "tv", manifest, PINNED_MANIFEST_URL, "")
    tv_out = tv_path.read_text(encoding="utf-8")
    for required in (
        "FIELD_NATIVE_UI_LAUNCHED client=tv",
        "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv",
        "FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv",
        "officialPluginManager.executeScraper(loadedScraper",
        "FIELD_NATIVE_PLAYER_BEGIN client=tv",
        "Screen.Player.createRoute",
        "NuvioNavHost",
        "LastPlaybackDiagnostics",
        "nuvio-tv-production",
    ):
        assert required in tv_out, required
    assert "ExoPlayer.Builder" not in tv_out
    assert "PluginRuntime.executePlugin(" not in tv_out

    anime = corpus.fixture_by_slug("jujutsu-kaisen-s01e01")
    mobile_source = reader.augment_android_test(
        corpus.android_test(anime, selected, "mobile"),
        client="mobile",
        expected_duration_minutes=anime.get("expectedDurationMinutes"),
        max_player_probes=4,
    )
    mobile_path = tmp / "Mobile.kt"
    mobile_path.write_text(mobile_source, encoding="utf-8")
    contract.augment(mobile_path, "mobile", "jujutsu-kaisen-s01e01", manifest)
    provider_loading.augment(mobile_path, "mobile", manifest, PINNED_MANIFEST_URL, "")
    mobile_out = mobile_path.read_text(encoding="utf-8")
    for required in (
        'listOf("anime", "tv").map',
        '"capability_probe"',
        "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=mobile",
        "PluginRepository.executeScraper(loadedScraper",
        "PlatformPlayerSurface",
        "sourceHeaders = headers.orEmpty()",
        "nuvio-mobile-production",
        "FIELD_NATIVE_PLAYER_BEGIN client=mobile",
    ):
        assert required in mobile_out, required
    assert "ExoPlayer.Builder" not in mobile_out
    assert "PluginRepository.clearLocalState()" not in mobile_out
    assert "PluginRuntime.executePlugin(" not in mobile_out

    original_event = os.environ.pop("GITHUB_EVENT_NAME", None)
    try:
        for platform in ("macos", "windows"):
            desktop_path = tmp / f"Desktop-{platform}.kt"
            desktop_path.write_text(corpus.desktop_test(anime, selected), encoding="utf-8")
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
                "PluginRepository.executeScraper(loadedScraper",
                "PlatformPlayerSurface(",
                "probeDesktopProductionPlayer",
                "engine=nuvio-production-desktop",
                "sourceHeaders = headers.orEmpty()",
                'captureDesktopPhase("player-start"',
                'captureDesktopPhase("player-result"',
            ):
                assert required in desktop_out, f"{platform}:{required}"
            assert "NativePlayerController(" not in desktop_out
            assert "controller.attach(" not in desktop_out
            assert "rows.take(" not in desktop_out
            assert "25000L" in desktop_out
    finally:
        if original_event is not None:
            os.environ["GITHUB_EVENT_NAME"] = original_event

    original_event = os.environ.get("GITHUB_EVENT_NAME")
    os.environ["GITHUB_EVENT_NAME"] = "pull_request"
    os.environ["NIAKVIO_PR_STREAM_LIMIT"] = "2"
    try:
        pr_path = tmp / "Desktop-pr.kt"
        pr_path.write_text(corpus.desktop_test(anime, selected), encoding="utf-8")
        contract.augment(pr_path, "desktop", "jujutsu-kaisen-s01e01", manifest)
        provider_loading.augment(pr_path, "desktop", manifest, PINNED_MANIFEST_URL, "windows")
        desktop_player.augment(pr_path, int(anime.get("expectedDurationMinutes") or 0), "all")
        pr_out = pr_path.read_text(encoding="utf-8")
        assert "rows.take(2).forEachIndexed" in pr_out
        assert "rows.take(1).forEachIndexed" not in pr_out
        assert "12000L" in pr_out
        assert "PlatformPlayerSurface(" in pr_out
    finally:
        os.environ.pop("NIAKVIO_PR_STREAM_LIMIT", None)
        if original_event is None:
            os.environ.pop("GITHUB_EVENT_NAME", None)
        else:
            os.environ["GITHUB_EVENT_NAME"] = original_event

print("native evidence production-player codegen pipeline tests passed")
