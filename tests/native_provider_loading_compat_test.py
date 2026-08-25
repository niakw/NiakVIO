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

print("native provider-loading runtime-trap compatibility tests passed")
