#!/usr/bin/env python3
"""Enforce production-equivalent Android transport conditions for native UX labs.

The lab is observational. It must never make playback or repository traffic easier
than the accepted Nuvio application would make it on the same device. In particular
this helper must not add INTERNET permission, cleartext exceptions, network-security
configuration, proxy/DNS overrides or any other test-only transport capability.

It is intentionally a validator rather than a configurator. Existing test manifests
are accepted only when they do not opt into cleartext transport. Production manifests
are never modified.
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID = f"{{{ANDROID_NS}}}"


def _assert_test_manifest(path: Path) -> None:
    normalized = path.as_posix().lower()
    if "/src/main/" in normalized or normalized.endswith("/src/main/androidmanifest.xml"):
        raise ValueError(f"refusing to inspect production manifest as a lab manifest: {path}")
    if "/src/androidtest/" not in normalized and "/src/androiddevicetest/" not in normalized:
        raise ValueError(
            "native UX transport validation only accepts androidTest/androidDeviceTest manifests: "
            f"{path}"
        )


def validate_manifest(path: Path) -> None:
    path = path.resolve()
    _assert_test_manifest(path)
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        # A missing/empty test overlay is the cleanest case: the target application
        # keeps its own production network policy unchanged.
        return

    root = ET.parse(path).getroot()
    if root.tag != "manifest":
        raise ValueError(f"unexpected Android manifest root {root.tag!r}: {path}")

    applications = [child for child in root if child.tag == "application"]
    if len(applications) > 1:
        raise ValueError(f"multiple <application> elements in test manifest: {path}")
    application = applications[0] if applications else None
    if application is not None:
        cleartext = application.get(f"{ANDROID}usesCleartextTraffic")
        if cleartext is not None and cleartext.strip().lower() == "true":
            raise RuntimeError(
                "native UX lab refuses test-only android:usesCleartextTraffic=true; "
                "the accepted Nuvio production policy must decide whether the request is allowed"
            )
        network_security = application.get(f"{ANDROID}networkSecurityConfig")
        if network_security:
            raise RuntimeError(
                "native UX lab refuses a test-only networkSecurityConfig; use the accepted "
                "Nuvio production network policy unchanged"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifests", nargs="+", type=Path)
    args = parser.parse_args()
    for manifest in args.manifests:
        validate_manifest(manifest)
        print(
            f"FIELD_NATIVE_ANDROID_LAB_TRANSPORT manifest={manifest.resolve()} "
            "mode=production-policy observational=true modified=false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
