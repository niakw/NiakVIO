#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from native_client_test_bootstrap import (  # noqa: E402
    MOBILE_DEVICE_TEST_MANIFEST,
    enable_mobile_device_tests,
)

BASE_SOURCE_SETS = '''
    sourceSets {
        commonMain.dependencies {
            implementation("example:dependency:1")
        }
    }
'''

HOST_TEST_VARIANTS = (
    "        withHostTest {}\n\n        compilerOptions {\n            jvmTarget.set(JvmTarget.JVM_11)\n        }",
    "        withHostTest { isIncludeAndroidResources = true }\n\n        compilerOptions {\n            jvmTarget.set(JvmTarget.JVM_11)\n        }",
)

PRODUCTION_MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="production-sentinel" />
</manifest>
'''

for host_test in HOST_TEST_VARIANTS:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        build = repo / "composeApp/build.gradle.kts"
        build.parent.mkdir(parents=True)
        build.write_text(
            "kotlin {\n    android {\n" + host_test + "\n    }\n" + BASE_SOURCE_SETS + "}\n",
            encoding="utf-8",
        )

        # A production sentinel proves that the bootstrap only creates the
        # androidDeviceTest manifest and never edits androidMain/runtime config.
        production_manifest = repo / "composeApp/src/androidMain/AndroidManifest.xml"
        production_manifest.parent.mkdir(parents=True, exist_ok=True)
        production_manifest.write_text(PRODUCTION_MANIFEST, encoding="utf-8")

        enable_mobile_device_tests(repo)
        once = build.read_text(encoding="utf-8")
        assert once.count("withDeviceTest {") == 1
        assert once.count('instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"') == 1
        assert once.count('execution = "HOST"') == 1
        assert once.count("val androidDeviceTest by getting {") == 1
        assert once.count('pickFirsts.add("lib/*/libc++_shared.so")') == 1
        assert "withHostTest {" in once

        test_manifest = repo / "composeApp/src/androidDeviceTest/AndroidManifest.xml"
        assert test_manifest.read_text(encoding="utf-8") == MOBILE_DEVICE_TEST_MANIFEST
        assert 'android:name="io.sentry.auto-init"' in MOBILE_DEVICE_TEST_MANIFEST
        assert 'android:value="false"' in MOBILE_DEVICE_TEST_MANIFEST
        assert production_manifest.read_text(encoding="utf-8") == PRODUCTION_MANIFEST

        # The bootstrap is deliberately idempotent so a fixture restage cannot
        # accumulate test-only Gradle or manifest mutations.
        enable_mobile_device_tests(repo)
        twice = build.read_text(encoding="utf-8")
        assert twice == once
        assert test_manifest.read_text(encoding="utf-8") == MOBILE_DEVICE_TEST_MANIFEST
        assert production_manifest.read_text(encoding="utf-8") == PRODUCTION_MANIFEST

# The canonical bootstrap is invoked by prepare_native_reader_acceptance.py before
# Android prebuild. A retired secondary hardener must never reappear as a dangling
# prebuild dependency after repository cleanup.
prebuild = (ROOT / "scripts/prebuild_native_android_reader_suite.sh").read_text(encoding="utf-8")
prepare = (ROOT / "scripts/prepare_native_reader_acceptance.py").read_text(encoding="utf-8")
assert "harden_nuvio_mobile_device_test.py" not in prebuild
assert "enable_mobile_device_tests" in prepare
assert "enable_tv_tests" in prepare

print("native client test bootstrap upstream-DSL/Sentry isolation compatibility passed")
