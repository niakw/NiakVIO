#!/usr/bin/env python3
"""Configure HTTP transport for Android instrumentation-only native labs.

NiakVIO's local_candidate repository is served from the CI host and reached by
Android emulators through 10.0.2.2. Android's cleartext policy applies to the
instrumentation/test APK independently of the production application, so this
helper enables lab HTTP only in androidTest/androidDeviceTest manifests.

Production manifests are deliberately rejected.
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID = f"{{{ANDROID_NS}}}"
ET.register_namespace("android", ANDROID_NS)


def _assert_test_manifest(path: Path) -> None:
    normalized = path.as_posix().lower()
    if "/src/main/" in normalized or normalized.endswith("/src/main/androidmanifest.xml"):
        raise ValueError(f"refusing to modify production manifest: {path}")
    if "/src/androidtest/" not in normalized and "/src/androiddevicetest/" not in normalized:
        raise ValueError(
            "native lab transport may only modify androidTest/androidDeviceTest manifests: "
            f"{path}"
        )


def configure_manifest(path: Path) -> None:
    path = path.resolve()
    _assert_test_manifest(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and path.read_text(encoding="utf-8").strip():
        root = ET.parse(path).getroot()
        if root.tag != "manifest":
            raise ValueError(f"unexpected Android manifest root {root.tag!r}: {path}")
    else:
        root = ET.Element("manifest")

    permission_name = f"{ANDROID}name"
    internet = "android.permission.INTERNET"
    if not any(
        child.tag == "uses-permission" and child.get(permission_name) == internet
        for child in root
    ):
        permission = ET.Element("uses-permission")
        permission.set(permission_name, internet)
        root.insert(0, permission)

    applications = [child for child in root if child.tag == "application"]
    if len(applications) > 1:
        raise ValueError(f"multiple <application> elements in test manifest: {path}")
    application = applications[0] if applications else ET.SubElement(root, "application")
    application.set(f"{ANDROID}usesCleartextTraffic", "true")

    ET.indent(root, space="    ")
    body = ET.tostring(root, encoding="unicode")
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + body + "\n", encoding="utf-8")

    verify = ET.parse(path).getroot()
    verify_app = next((child for child in verify if child.tag == "application"), None)
    verify_internet = any(
        child.tag == "uses-permission" and child.get(permission_name) == internet
        for child in verify
    )
    if verify_app is None or verify_app.get(f"{ANDROID}usesCleartextTraffic") != "true" or not verify_internet:
        raise RuntimeError(f"failed to configure native Android lab transport: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifests", nargs="+", type=Path)
    args = parser.parse_args()
    for manifest in args.manifests:
        configure_manifest(manifest)
        print(f"FIELD_NATIVE_ANDROID_LAB_TRANSPORT manifest={manifest} cleartext=true internet=true scope=test-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
