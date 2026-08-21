#!/usr/bin/env python3
"""Bind generated NuvioTV androidTest code to the debug-built Hilt EntryPoint.

Hilt cannot add an androidTest-declared EntryPoint to the target APK's already
compiled SingletonComponent. The test bootstrap therefore materializes the
EntryPoint in app/src/debug; this postprocessor removes the duplicate nested
androidTest declaration and leaves the generated test using the same-package
NiakvioPluginManagerEntryPoint compiled into the debug application.

Only generated diagnostic test source is changed here. Production/main runtime,
networking, provider code and player code remain untouched.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

NESTED_ENTRYPOINT = re.compile(
    r"\n    @EntryPoint\n"
    r"    @InstallIn\(SingletonComponent::class\)\n"
    r"    interface NiakvioPluginManagerEntryPoint \{\n"
    r"        fun pluginManager\(\): PluginManager\n"
    r"    \}\n",
    re.MULTILINE,
)

REMOVABLE_IMPORTS = (
    "import dagger.hilt.EntryPoint\n",
    "import dagger.hilt.InstallIn\n",
    "import dagger.hilt.components.SingletonComponent\n",
)


def finalize(source: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"missing generated TV androidTest source: {source}")
    text = source.read_text(encoding="utf-8")

    if "NiakvioPluginManagerEntryPoint::class.java" not in text:
        raise SystemExit("TV generated test no longer references the PluginManager EntryPoint")

    matches = list(NESTED_ENTRYPOINT.finditer(text))
    if len(matches) > 1:
        raise SystemExit(f"unexpected nested TV EntryPoint count={len(matches)}")
    if matches:
        text = NESTED_ENTRYPOINT.sub("\n", text, count=1)

    for import_line in REMOVABLE_IMPORTS:
        text = text.replace(import_line, "")

    # The official EntryPointAccessors call remains. With no nested declaration,
    # Kotlin resolves NiakvioPluginManagerEntryPoint from the same package in the
    # target debug APK, where Hilt actually aggregated it.
    if "import dagger.hilt.android.EntryPointAccessors\n" not in text:
        raise SystemExit("TV generated test lost EntryPointAccessors import")
    if "interface NiakvioPluginManagerEntryPoint" in text:
        raise SystemExit("nested androidTest Hilt EntryPoint still present")

    source.write_text(text, encoding="utf-8")
    print(
        "FIELD_NATIVE_TV_HILT_ENTRYPOINT scope=debug-target-apk "
        "android_test_nested_entrypoint=false runtime_mutation=false"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()
    finalize(Path(args.source).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
