#!/usr/bin/env python3
"""Minimal test-only bootstrap for official Nuvio client checkouts.

This module may enable an upstream project's instrumentation source set, test
runner, test dependencies, and (for TV) a debug signing configuration required
to install the debug APK on the emulator.  It must never change production
Android manifests, networking policy, player code, stream headers, storage,
DNS, proxying, decoder settings, or any other runtime behaviour.
"""
from __future__ import annotations

from pathlib import Path

MOBILE_RUNNER = 'instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"'
MOBILE_EXT_JUNIT = 'implementation("androidx.test.ext:junit:1.3.0")'
MOBILE_TEST_RUNNER = 'implementation("androidx.test:runner:1.7.0")'
TV_RUNNER = 'testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"'
TV_EXT_JUNIT = 'androidTestImplementation("androidx.test.ext:junit:1.3.0")'
TV_TEST_RUNNER = 'androidTestImplementation("androidx.test:runner:1.7.0")'


def enable_mobile_device_tests(repo: Path) -> None:
    """Enable only the Android device-test source set in NuvioMobile.

    No main manifest is created or edited here. If the official application is
    missing a capability required by playback, the native lab must observe that
    failure rather than manufacture the capability.
    """
    build = Path(repo) / "composeApp/build.gradle.kts"
    text = build.read_text(encoding="utf-8")

    if "withDeviceTest {" not in text:
        compilation_needle = "        withHostTest {}\n\n        compilerOptions {"
        compilation_replacement = '''        withHostTest {}
        withDeviceTest {
            instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
            execution = "HOST"
        }

        compilerOptions {'''
        if text.count(compilation_needle) != 1:
            raise SystemExit(
                f"mobile device-test compilation anchor count={text.count(compilation_needle)}"
            )
        text = text.replace(compilation_needle, compilation_replacement, 1)

    if "val androidDeviceTest by getting {" not in text:
        source_needle = "        commonMain.dependencies {"
        source_replacement = '''        val androidDeviceTest by getting {
            dependencies {
                implementation("junit:junit:4.13.2")
                implementation("androidx.test.ext:junit:1.3.0")
                implementation("androidx.test:runner:1.7.0")
            }
        }
        commonMain.dependencies {'''
        if text.count(source_needle) != 1:
            raise SystemExit(
                f"mobile device-test dependency anchor count={text.count(source_needle)}"
            )
        text = text.replace(source_needle, source_replacement, 1)

    build.write_text(text, encoding="utf-8")
    print("FIELD_NATIVE_TEST_BOOTSTRAP client=mobile scope=test-only runtime_mutation=false")


def enable_tv_tests(repo: Path) -> None:
    """Enable NuvioTV instrumentation without touching production runtime code."""
    build = Path(repo) / "app/build.gradle.kts"
    text = build.read_text(encoding="utf-8")

    # Hosted CI does not possess the official release signing key. Switching the
    # debug variant back to the standard debug keystore is a packaging-only test
    # prerequisite; it does not alter player/network/provider behaviour.
    release_signing = '        debug {\n            signingConfig = signingConfigs.getByName("release")'
    debug_signing = '        debug {\n            signingConfig = signingConfigs.getByName("debug")'
    if release_signing in text:
        text = text.replace(release_signing, debug_signing, 1)
    elif debug_signing not in text:
        raise SystemExit("NuvioTV debug signing contract missing")

    if TV_RUNNER not in text:
        default_config = "    defaultConfig {\n"
        if text.count(default_config) != 1:
            raise SystemExit(
                f"NuvioTV defaultConfig structural anchor count={text.count(default_config)}"
            )
        text = text.replace(default_config, default_config + f"        {TV_RUNNER}\n", 1)

    missing_dependencies = [
        dependency for dependency in (TV_EXT_JUNIT, TV_TEST_RUNNER) if dependency not in text
    ]
    if missing_dependencies:
        text = text.rstrip() + "\n\n\ndependencies {\n"
        text += "\n".join(f"    {dependency}" for dependency in missing_dependencies)
        text += "\n}\n"

    build.write_text(text, encoding="utf-8")
    print("FIELD_NATIVE_TEST_BOOTSTRAP client=tv scope=test-only runtime_mutation=false")
