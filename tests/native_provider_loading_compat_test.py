#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compat = load("native_provider_loading_compat", "scripts/augment_native_provider_loading_compat.py")
canonical = load("native_provider_loading", "scripts/augment_native_provider_loading.py")

CASES = {
    "desktop": (
        """val rows = PluginRuntime.executePlugin(
                    code = trapRuntimeErrors(File(root, provider.asset).readText()),
                    tmdbId = tmdbId,
                    mediaType = requestMediaType,
                    season = season,
                    episode = episode,
                    scraperId = provider.id,
                )""",
        "PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()",
    ),
    "mobile": (
        """val rows = PluginRuntime.executePlugin(
                    code = trapRuntimeErrors(code(provider.asset)),
                    tmdbId = tmdbId,
                    mediaType = requestMediaType,
                    season = season,
                    episode = episode,
                    scraperId = provider.id,
                )""",
        "PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()",
    ),
    "tv": (
        """val rows = runtime.executePlugin(
                    code = trapRuntimeErrors(code(provider.asset)),
                    tmdbId = tmdbId,
                    mediaType = requestMediaType,
                    season = season,
                    episode = episode,
                    scraperId = provider.id,
                )""",
        "officialPluginManager.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode)",
    ),
}

with tempfile.TemporaryDirectory() as raw_tmp:
    tmp = Path(raw_tmp)
    for client, (source, expected) in CASES.items():
        path = tmp / f"{client}.kt"
        path.write_text(source, encoding="utf-8")
        changed = compat.unwrap_runtime_trap(path, client)
        assert changed is True, client
        normalized = path.read_text(encoding="utf-8")
        assert "trapRuntimeErrors(" not in normalized, client
        rewritten = canonical.replace_official_execution(normalized, client)
        assert expected in rewritten, client
        assert "executePlugin(" not in rewritten, client

    # The production corpus wraps provider execution in a per-provider timeout.
    # Rewriting must preserve that outer budget while swapping only the invocation.
    wrapped = tmp / "tv-timeout.kt"
    wrapped.write_text(
        "val rows = kotlinx.coroutines.withTimeout(25000L) {\n"
        + CASES["tv"][0].replace("val rows = ", "")
        + "\n}",
        encoding="utf-8",
    )
    assert compat.unwrap_runtime_trap(wrapped, "tv") is True
    wrapped_text = canonical.replace_official_execution(wrapped.read_text(encoding="utf-8"), "tv")
    assert "kotlinx.coroutines.withTimeout(25000L)" in wrapped_text
    assert CASES["tv"][1] in wrapped_text
    assert "runtime.executePlugin(" not in wrapped_text

    # Android FULL isolation puts the blocking QuickJS call behind a Future hard
    # timeout. Official Nuvio loading must still rewrite only that inner invocation.
    hard = tmp / "tv-hard-timeout.kt"
    hard.write_text(
        "val providerFuture = providerExecutor.submit(java.util.concurrent.Callable {\n"
        "    runBlocking {\n"
        + CASES["tv"][0].replace("val rows = ", "")
        + "\n    }\n"
        "}\n"
        "val rows = providerFuture.get(25000L, java.util.concurrent.TimeUnit.MILLISECONDS)",
        encoding="utf-8",
    )
    assert compat.unwrap_runtime_trap(hard, "tv") is True
    hard_text = canonical.replace_official_execution(hard.read_text(encoding="utf-8"), "tv")
    assert "providerFuture.get(25000L" in hard_text
    assert CASES["tv"][1] in hard_text
    assert "runtime.executePlugin(" not in hard_text

    hard_constructor = hard.read_text(encoding="utf-8").replace(
        "runtime.executePlugin(",
        "PluginRuntime().executePlugin(",
    )
    hard_constructor_text = canonical.replace_official_execution(hard_constructor, "tv")
    assert "providerFuture.get(25000L" in hard_constructor_text
    assert CASES["tv"][1] in hard_constructor_text
    assert "PluginRuntime().executePlugin(" not in hard_constructor_text

    # Acceptance-prepared sources can already be in canonical raw form. The
    # compatibility layer must remain safe and idempotent for that path.
    raw_path = tmp / "desktop-raw.kt"
    raw_path.write_text(
        CASES["desktop"][0].replace(
            "trapRuntimeErrors(File(root, provider.asset).readText())",
            "File(root, provider.asset).readText()",
        ),
        encoding="utf-8",
    )
    assert compat.unwrap_runtime_trap(raw_path, "desktop") is False
    assert CASES["desktop"][1] in canonical.replace_official_execution(
        raw_path.read_text(encoding="utf-8"), "desktop"
    )

    # Mobile/Desktop native evidence must expose the same scraper-selection path
    # used by the real Streams repositories. Repository installation alone is not
    # sufficient if getEnabledScrapersForType() returns zero launchable providers.
    for client in ("desktop", "mobile"):
        app_path = tmp / f"{client}-app-path.kt"
        app_path.write_text(
            """    private suspend fun loadProvidersThroughNuvio(): Map<String, PluginScraper> {
        val repositoryUrl = repositoryManifestUrl
        val byId = emptyMap<String, PluginScraper>()
        return byId
    }
""",
            encoding="utf-8",
        )
        compat.inject_app_path_diagnostics(app_path, client)
        injected = app_path.read_text(encoding="utf-8")
        assert 'PluginRepository.getEnabledScrapersForType("movie")' in injected, client
        assert 'PluginRepository.getEnabledScrapersForType("tv")' in injected, client
        assert 'PluginRepository.getEnabledScrapersForType("series")' in injected, client
        assert f"FIELD_NATIVE_REPOSITORY_APP_PATH client={client}" in injected, client
        assert "plugins_enabled=${pluginStateForAppPath.pluginsEnabled}" in injected, client
        assert "group_by_repository=${pluginStateForAppPath.groupStreamsByRepository}" in injected, client
        assert "movie_enabled=${appMovieScrapers.size}" in injected, client
        assert "tv_enabled=${appTvScrapers.size}" in injected, client
        assert "series_enabled=${appSeriesScrapers.size}" in injected, client
        before = injected
        compat.inject_app_path_diagnostics(app_path, client)
        assert app_path.read_text(encoding="utf-8") == before, client

    tv_app_path = tmp / "tv-app-path.kt"
    tv_app_path.write_text("return manager to byId\n", encoding="utf-8")
    compat.inject_app_path_diagnostics(tv_app_path, "tv")
    assert "getEnabledScrapersForType" not in tv_app_path.read_text(encoding="utf-8")

    # Ambiguous generated code must fail closed rather than silently rewriting a
    # random occurrence and producing misleading native evidence.
    bad = tmp / "bad.kt"
    bad.write_text(CASES["mobile"][0] + "\n" + CASES["mobile"][0], encoding="utf-8")
    try:
        compat.unwrap_runtime_trap(bad, "mobile")
    except SystemExit as error:
        assert "count=2" in str(error)
    else:
        raise AssertionError("duplicate runtime-trap anchors must be rejected")

print("native provider-loading runtime-trap and app-path compatibility tests passed")