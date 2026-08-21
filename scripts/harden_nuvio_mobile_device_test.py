#!/usr/bin/env python3
"""Apply behavior-neutral compatibility to NuvioMobile device tests.

Human-UX invariant: this helper must not change Nuvio application runtime,
player, network, provider behavior, settings, or Android OS policy. It only:
- resolves the duplicate libc++_shared.so merge conflict in the instrumentation APK;
- removes Sentry auto-init from the *instrumentation test process* so a missing DSN
  cannot crash the harness before the first test starts.

The production application manifest/process is never edited. Changes are scoped to
the prepared ephemeral upstream checkout and are idempotent.
"""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
TOOLS_NS = "http://schemas.android.com/tools"
SENTRY_INIT_PROVIDER = "io.sentry.android.core.SentryInitProvider"

ET.register_namespace("android", ANDROID_NS)
ET.register_namespace("tools", TOOLS_NS)


def _ensure_device_test_packaging(repo: Path) -> None:
    build = repo / "composeApp/build.gradle.kts"
    if not build.is_file():
        raise SystemExit(f"missing NuvioMobile compose build file: {build}")

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

    final = build.read_text(encoding="utf-8")
    if final.count(packaging_line) != 1:
        raise SystemExit(f"unexpected libc++ packaging rule count={final.count(packaging_line)}")


def _disable_sentry_only_in_test_process(repo: Path) -> None:
    # This is the Android instrumentation manifest overlay, not the application's
    # production manifest. Removing this provider only prevents the test APK process
    # (com.nuvio.app.test) from requiring a Sentry DSN before JUnit starts.
    test_manifest = repo / "composeApp/src/androidDeviceTest/AndroidManifest.xml"
    test_manifest.parent.mkdir(parents=True, exist_ok=True)

    if test_manifest.is_file():
        try:
            tree = ET.parse(test_manifest)
        except ET.ParseError as error:
            raise SystemExit(f"invalid NuvioMobile androidDeviceTest manifest: {error}") from error
        root = tree.getroot()
        if root.tag != "manifest":
            raise SystemExit(f"unexpected androidDeviceTest manifest root: {root.tag}")
    else:
        root = ET.Element("manifest")
        tree = ET.ElementTree(root)

    application = root.find("application")
    if application is None:
        application = ET.SubElement(root, "application")

    name_key = f"{{{ANDROID_NS}}}name"
    node_key = f"{{{TOOLS_NS}}}node"
    providers = [
        child
        for child in list(application)
        if child.tag == "provider" and child.attrib.get(name_key) == SENTRY_INIT_PROVIDER
    ]
    if len(providers) > 1:
        raise SystemExit(f"unexpected SentryInitProvider overlay count={len(providers)}")
    if providers:
        provider = providers[0]
    else:
        provider = ET.SubElement(application, "provider")
        provider.set(name_key, SENTRY_INIT_PROVIDER)
    provider.set(node_key, "remove")

    tree.write(test_manifest, encoding="utf-8", xml_declaration=True)

    # Fail closed if this ever drifts away from the test-only source set.
    expected = "composeApp/src/androidDeviceTest/AndroidManifest.xml"
    relative = test_manifest.relative_to(repo).as_posix()
    if relative != expected:
        raise SystemExit(f"refusing non-test manifest mutation: {relative}")
    check = ET.parse(test_manifest).getroot()
    app_check = check.find("application")
    matching = [] if app_check is None else [
        child
        for child in list(app_check)
        if child.tag == "provider"
        and child.attrib.get(name_key) == SENTRY_INIT_PROVIDER
        and child.attrib.get(node_key) == "remove"
    ]
    if len(matching) != 1:
        raise SystemExit("Sentry test-process provider removal was not materialized exactly once")


def harden(repo: Path) -> None:
    _ensure_device_test_packaging(repo)
    _disable_sentry_only_in_test_process(repo)
    print(
        "NuvioMobile device-test bootstrap compatibility applied "
        "libcxx_pick_first=true sentry_test_process_autoinit=false runtime_mutation=false"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default="nuvio-mobile")
    args = parser.parse_args()
    harden(Path(args.repo).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
