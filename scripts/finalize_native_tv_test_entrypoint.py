#!/usr/bin/env python3
"""Bind generated NuvioTV androidTest code to debug-built Hilt EntryPoints.

Hilt cannot add androidTest-declared EntryPoints to the target APK's already
compiled SingletonComponent. The test bootstrap therefore materializes both
required accessors in app/src/debug; this postprocessor removes the duplicate
androidTest declarations and leaves the generated test using the same-package
accessors compiled into the debug application.

Only generated diagnostic test source is changed here. Production/main runtime,
networking, provider code and player code remain untouched.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PLUGIN_ENTRYPOINT = re.compile(
    r"\n    @EntryPoint\n"
    r"    @InstallIn\(SingletonComponent::class\)\n"
    r"    interface NiakvioPluginManagerEntryPoint \{\n"
    r"        fun pluginManager\(\): PluginManager\n"
    r"    \}\n",
    re.MULTILINE,
)

PLAYER_SETTINGS_ENTRYPOINT = re.compile(
    r"\n    @EntryPoint\n"
    r"    @InstallIn\(SingletonComponent::class\)\n"
    r"    interface NiakvioPlayerSettingsEntryPoint \{\n"
    r"        fun playerSettingsDataStore\(\): PlayerSettingsDataStore\n"
    r"    \}\n",
    re.MULTILINE,
)

REMOVABLE_IMPORTS = (
    "import dagger.hilt.EntryPoint\n",
    "import dagger.hilt.InstallIn\n",
    "import dagger.hilt.components.SingletonComponent\n",
)


def _remove_exactly_one(text: str, pattern: re.Pattern[str], label: str) -> str:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"unexpected nested TV {label} EntryPoint count={len(matches)}")
    return pattern.sub("\n", text, count=1)


def finalize(source: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"missing generated TV androidTest source: {source}")
    text = source.read_text(encoding="utf-8")

    for reference, label in (
        ("NiakvioPluginManagerEntryPoint::class.java", "PluginManager"),
        ("NiakvioPlayerSettingsEntryPoint::class.java", "PlayerSettings"),
    ):
        if reference not in text:
            raise SystemExit(f"TV generated test no longer references the {label} EntryPoint")

    text = _remove_exactly_one(text, PLUGIN_ENTRYPOINT, "PluginManager")
    text = _remove_exactly_one(text, PLAYER_SETTINGS_ENTRYPOINT, "PlayerSettings")

    for import_line in REMOVABLE_IMPORTS:
        text = text.replace(import_line, "")

    # EntryPointAccessors stays in androidTest, but every @EntryPoint declaration
    # itself must come from the target debug APK so Hilt aggregates it correctly.
    if "import dagger.hilt.android.EntryPointAccessors\n" not in text:
        raise SystemExit("TV generated test lost EntryPointAccessors import")
    for forbidden in (
        "interface NiakvioPluginManagerEntryPoint",
        "interface NiakvioPlayerSettingsEntryPoint",
        "@EntryPoint",
        "@InstallIn(SingletonComponent::class)",
    ):
        if forbidden in text:
            raise SystemExit(f"nested androidTest Hilt declaration still present: {forbidden}")

    source.write_text(text, encoding="utf-8")
    print(
        "FIELD_NATIVE_TV_HILT_ENTRYPOINT scope=debug-target-apk "
        "android_test_nested_entrypoints=false accessors=plugin_manager,player_settings "
        "runtime_mutation=false"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()
    finalize(Path(args.source).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
