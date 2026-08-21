#!/usr/bin/env python3
"""Apply infrastructure-only packaging compatibility to NuvioMobile device tests.

Human-UX invariant: this helper must not change Nuvio player, network, provider,
application runtime, settings, or OS policy. It only resolves the duplicate
libc++_shared.so merge conflict in the generated instrumentation APK so the real
application can be launched and observed.

The change is scoped to the prepared ephemeral upstream checkout and is idempotent.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def harden(repo: Path) -> None:
    build = repo / "composeApp/build.gradle.kts"
    if not build.is_file():
        raise SystemExit(f"missing NuvioMobile compose build file: {build}")

    text = build.read_text(encoding="utf-8")
    packaging_line = 'pickFirsts.add("lib/*/libc++_shared.so")'
    if packaging_line in text:
        if text.count(packaging_line) != 1:
            raise SystemExit(f"unexpected libc++ packaging rule count={text.count(packaging_line)}")
        print("NuvioMobile device-test packaging compatibility already applied")
        return

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

    final = build.read_text(encoding="utf-8")
    if final.count(packaging_line) != 1:
        raise SystemExit(f"unexpected libc++ packaging rule count={final.count(packaging_line)}")
    print("NuvioMobile device-test packaging compatibility applied")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default="nuvio-mobile")
    args = parser.parse_args()
    harden(Path(args.repo).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
