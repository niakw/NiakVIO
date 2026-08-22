#!/usr/bin/env python3
"""Minimal test-only bootstrap for official Nuvio client checkouts.

This module may enable an upstream project's instrumentation source set, test
runner, test dependencies, and (for TV) a debug signing configuration required
to install the debug APK on the emulator. It must never change production
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
TV_DEBUG_ENTRYPOINT = '''package com.nuvio.tv.core.plugin

import com.nuvio.tv.data.local.PlayerSettingsDataStore
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

/** Test-build-only accessors aggregated into the real debug SingletonComponent. */
@EntryPoint
@InstallIn(SingletonComponent::class)
interface NiakvioPluginManagerEntryPoint {
    fun pluginManager(): PluginManager
}

@EntryPoint
@InstallIn(SingletonComponent::class)
interface NiakvioPlayerSettingsEntryPoint {
    fun playerSettingsDataStore(): PlayerSettingsDataStore
}
'''


def enable_mobile_device_tests(repo: Path) -> None:
    """Enable only the Android device-test source set in NuvioMobile."""
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
    repo = Path(repo)
    build = repo / "app/build.gradle.kts"
    text = build.read_text(encoding="utf-8")

    # Hosted CI does not possess the official release signing key. Switching the
    # debug variant back to the standard debug keystore is packaging-only test plumbing.
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

    # Hilt aggregates EntryPoints when compiling the target APK, not afterwards
    # when androidTest is compiled. Materialize both accessors in debug-only source
    # so they are part of the real debug SingletonComponent without changing main/release.
    entrypoint = repo / "app/src/debug/java/com/nuvio/tv/core/plugin/NiakvioPluginManagerEntryPoint.kt"
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    if entrypoint.exists() and entrypoint.read_text(encoding="utf-8") != TV_DEBUG_ENTRYPOINT:
        raise SystemExit(f"unexpected existing TV debug entrypoint content: {entrypoint}")
    entrypoint.write_text(TV_DEBUG_ENTRYPOINT, encoding="utf-8")

    print(
        "FIELD_NATIVE_TEST_BOOTSTRAP client=tv scope=test-only runtime_mutation=false "
        "hilt_debug_entrypoints=plugin_manager,player_settings"
    )
