#!/usr/bin/env python3
"""Harden a prepared NuvioMobile Android device-test workspace.

The native lab preparation intentionally modifies a pinned upstream checkout.
This helper keeps infrastructure-only Android requirements in one place:
- resolve duplicate libc++_shared.so packaging in instrumentation APKs;
- disable Sentry auto-init in the test process so no DSN is required.

It is idempotent and tolerant of whitespace changes in the prepared Gradle block.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def harden(repo: Path) -> None:
    build = repo / "composeApp/build.gradle.kts"
    text = build.read_text(encoding="utf-8")

    packaging_line = 'pickFirsts.add("lib/*/libc++_shared.so")'
    if packaging_line not in text:
        pattern = re.compile(
            r"(?P<device>^[ \t]*withDeviceTest\s*\{.*?^[ \t]*\}\s*)"
            r"(?P<compiler>^[ \t]*compilerOptions\s*\{)",
            re.MULTILINE | re.DOTALL,
        )
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise SystemExit(
                f"expected one prepared withDeviceTest/compilerOptions block, found {len(matches)}"
            )
        match = matches[0]
        indent = re.match(r"^[ \t]*", match.group("compiler")).group(0)
        packaging = (
            f'{indent}packaging {{\n'
            f'{indent}    jniLibs {{\n'
            f'{indent}        {packaging_line}\n'
            f'{indent}    }}\n'
            f'{indent}}}\n\n'
        )
        text = text[: match.start("compiler")] + packaging + text[match.start("compiler") :]
        build.write_text(text, encoding="utf-8")

    test_manifest = repo / "composeApp/src/androidDeviceTest/AndroidManifest.xml"
    test_manifest.parent.mkdir(parents=True, exist_ok=True)
    test_manifest.write_text(
        '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <application>
        <meta-data
            android:name="io.sentry.auto-init"
            android:value="false"
            tools:replace="android:value" />
    </application>
</manifest>
''',
        encoding="utf-8",
    )

    final = build.read_text(encoding="utf-8")
    if final.count(packaging_line) != 1:
        raise SystemExit(
            f"unexpected libc++ shared packaging rule count={final.count(packaging_line)}"
        )
    print("NuvioMobile device-test hardening applied")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default="nuvio-mobile")
    args = parser.parse_args()
    harden(Path(args.repo).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
