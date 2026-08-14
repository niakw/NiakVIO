#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ("moviebox", "netmirror", "streamzo")
EXPECTED_ENABLED = {"moviebox": False, "netmirror": False, "streamzo": True}


def manifest_rows() -> dict[str, dict]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers", [])
        if isinstance(row, dict)
    }
    for provider_id, expected in EXPECTED_ENABLED.items():
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f"missing provider in manifest: {provider_id}")
        actual = bool(row.get("enabled"))
        if actual != expected:
            raise SystemExit(
                f"unexpected activation for {provider_id}: {actual} != {expected}"
            )
    return rows


def copy_bundles(destination: Path) -> None:
    rows = manifest_rows()
    destination.mkdir(parents=True, exist_ok=True)
    for provider_id in PROVIDERS:
        source = ROOT / str(rows[provider_id]["filename"])
        target = destination / f"{provider_id}.js"
        shutil.copy2(source, target)
        print(
            f"FIELD_NATIVE_STAGE provider={provider_id} "
            f"enabled={str(rows[provider_id].get('enabled')).lower()} source={source}"
        )


DESKTOP_TEST = r'''package com.nuvio.app.features.plugins

import com.nuvio.app.features.plugins.runtime.PluginRuntime
import java.io.File
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class NiakvioFinalNativeDesktopTest {
    private val workspace = File(System.getenv("GITHUB_WORKSPACE"))
    private val root = File(workspace, "niakvio/real-client-stage")
    private val resultFile = File(workspace, "desktop-native-results.log")

    private fun emit(message: String) {
        println(message)
        resultFile.appendText(message + "\n")
    }

    @Test
    fun exactMonNinjaProviders() = runBlocking {
        for (id in listOf("moviebox", "netmirror", "streamzo")) {
            val started = System.currentTimeMillis()
            val rows = PluginRuntime.executePlugin(
                code = File(root, "$id.js").readText(),
                tmdbId = "1215638",
                mediaType = "movie",
                season = null,
                episode = null,
                scraperId = id,
            )
            emit("FIELD_DESKTOP_NATIVE provider=$id duration_ms=${System.currentTimeMillis()-started} count=${rows.size}")
            rows.forEachIndexed { index, row ->
                emit("FIELD_DESKTOP_NATIVE_ROW provider=$id index=$index title=${row.title} name=${row.name} quality=${row.quality} language=${row.language} type=${row.type} url=${row.url}")
            }
            when (id) {
                "moviebox", "netmirror" -> assertTrue(rows.isEmpty(), "$id must fail closed")
                "streamzo" -> {
                    assertTrue(rows.isNotEmpty(), "StreamZo must resolve Mon ninja et moi 3")
                    assertTrue(rows.any { it.url.contains(".m3u8", ignoreCase = true) }, "StreamZo must expose HLS")
                }
            }
        }
    }

    @Test
    fun missingOptionalMetadataIsAccepted() = runBlocking {
        val rows = PluginRuntime.executePlugin(
            code = "module.exports.getStreams=async()=>[{title:'Metadata control',url:'https://example.test/video.mp4'}];",
            tmdbId = "1215638",
            mediaType = "movie",
            season = null,
            episode = null,
            scraperId = "metadata-control",
        )
        assertEquals(1, rows.size)
        assertEquals(null, rows.single().quality)
        assertEquals(null, rows.single().language)
        emit("FIELD_DESKTOP_METADATA_NULL_ACCEPTED=true")
    }
}
'''

MOBILE_TEST = r'''package com.nuvio.app.features.plugins

import android.util.Log
import androidx.test.platform.app.InstrumentationRegistry
import com.nuvio.app.features.plugins.runtime.PluginRuntime
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class NiakvioFinalNativeMobileTest {
    private fun emit(message: String) {
        println(message)
        Log.i("NiakvioRealLab", message)
    }

    private fun code(id: String): String =
        InstrumentationRegistry.getInstrumentation().context.assets
            .open("niakvio/$id.js").bufferedReader().use { it.readText() }

    @Test
    fun exactMonNinjaProviders() = runBlocking {
        for (id in listOf("moviebox", "netmirror", "streamzo")) {
            val started = System.currentTimeMillis()
            val rows = PluginRuntime.executePlugin(
                code = code(id),
                tmdbId = "1215638",
                mediaType = "movie",
                season = null,
                episode = null,
                scraperId = id,
            )
            emit("FIELD_MOBILE_NATIVE provider=$id duration_ms=${System.currentTimeMillis()-started} count=${rows.size}")
            rows.forEachIndexed { index, row ->
                emit("FIELD_MOBILE_NATIVE_ROW provider=$id index=$index title=${row.title} name=${row.name} quality=${row.quality} language=${row.language} type=${row.type} url=${row.url}")
            }
            when (id) {
                "moviebox", "netmirror" -> assertTrue("$id must fail closed", rows.isEmpty())
                "streamzo" -> {
                    assertTrue("StreamZo must resolve Mon ninja et moi 3", rows.isNotEmpty())
                    assertTrue("StreamZo must expose HLS", rows.any { it.url.contains(".m3u8", ignoreCase = true) })
                }
            }
        }
    }

    @Test
    fun missingOptionalMetadataIsAccepted() = runBlocking {
        val rows = PluginRuntime.executePlugin(
            code = "module.exports.getStreams=async()=>[{title:'Metadata control',url:'https://example.test/video.mp4'}];",
            tmdbId = "1215638",
            mediaType = "movie",
            season = null,
            episode = null,
            scraperId = "metadata-control",
        )
        assertEquals(1, rows.size)
        assertEquals(null, rows.single().quality)
        assertEquals(null, rows.single().language)
        emit("FIELD_MOBILE_METADATA_NULL_ACCEPTED=true")
    }
}
'''

TV_TEST = r'''package com.nuvio.tv.core.plugin

import android.util.Log
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class NiakvioFinalNativeTvTest {
    private val runtime = PluginRuntime()

    private fun emit(message: String) {
        println(message)
        Log.i("NiakvioRealLab", message)
    }

    private fun code(id: String): String =
        InstrumentationRegistry.getInstrumentation().context.assets
            .open("niakvio/$id.js").bufferedReader().use { it.readText() }

    @Test
    fun exactMonNinjaProviders() = runBlocking {
        for (id in listOf("moviebox", "netmirror", "streamzo")) {
            val started = System.currentTimeMillis()
            val rows = runtime.executePlugin(
                code = code(id),
                tmdbId = "1215638",
                mediaType = "movie",
                season = null,
                episode = null,
                scraperId = id,
            )
            emit("FIELD_TV_NATIVE provider=$id duration_ms=${System.currentTimeMillis()-started} count=${rows.size}")
            rows.forEachIndexed { index, row ->
                emit("FIELD_TV_NATIVE_ROW provider=$id index=$index title=${row.title} name=${row.name} quality=${row.quality} language=${row.language} type=${row.type} url=${row.url}")
            }
            when (id) {
                "moviebox", "netmirror" -> assertTrue("$id must fail closed", rows.isEmpty())
                "streamzo" -> {
                    assertTrue("StreamZo must resolve Mon ninja et moi 3", rows.isNotEmpty())
                    assertTrue("StreamZo must expose HLS", rows.any { it.url.contains(".m3u8", ignoreCase = true) })
                }
            }
        }
    }

    @Test
    fun missingOptionalMetadataIsAccepted() = runBlocking {
        val rows = runtime.executePlugin(
            code = "module.exports.getStreams=async()=>[{title:'Metadata control',url:'https://example.test/video.mp4'}];",
            tmdbId = "1215638",
            mediaType = "movie",
            season = null,
            episode = null,
            scraperId = "metadata-control",
        )
        assertEquals(1, rows.size)
        assertEquals(null, rows.single().quality)
        assertEquals(null, rows.single().language)
        emit("FIELD_TV_METADATA_NULL_ACCEPTED=true")
    }
}
'''


def prepare_desktop(workspace: Path) -> None:
    copy_bundles(ROOT / "real-client-stage")
    target = (
        workspace
        / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioFinalNativeDesktopTest.kt"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(DESKTOP_TEST, encoding="utf-8")


def prepare_mobile(workspace: Path) -> None:
    repo = workspace / "nuvio-mobile"
    build = repo / "composeApp/build.gradle.kts"
    text = build.read_text(encoding="utf-8")
    needle = "        withHostTest {}\n\n        compilerOptions {"
    replacement = '''        withHostTest {}
        withDeviceTest {
            instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
            execution = "HOST"
        }

        compilerOptions {'''
    if text.count(needle) != 1:
        raise SystemExit(f"mobile device-test compilation anchor count={text.count(needle)}")
    text = text.replace(needle, replacement, 1)
    needle = "        commonMain.dependencies {"
    replacement = '''        val androidDeviceTest by getting {
            dependencies {
                implementation("junit:junit:4.13.2")
                implementation("androidx.test.ext:junit:1.3.0")
                implementation("androidx.test:runner:1.7.0")
            }
        }
        commonMain.dependencies {'''
    if text.count(needle) != 1:
        raise SystemExit(f"mobile device-test dependency anchor count={text.count(needle)}")
    build.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
    (repo / "composeApp/src/androidMain/AndroidManifest.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <uses-permission android:name="android.permission.INTERNET" />\n'
        '</manifest>\n',
        encoding="utf-8",
    )
    copy_bundles(repo / "composeApp/src/androidDeviceTest/assets/niakvio")
    test = repo / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioFinalNativeMobileTest.kt"
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text(MOBILE_TEST, encoding="utf-8")


def prepare_tv(workspace: Path) -> None:
    repo = workspace / "nuvio-tv"
    build = repo / "app/build.gradle.kts"
    text = build.read_text(encoding="utf-8")
    signing = '        debug {\n            signingConfig = signingConfigs.getByName("release")'
    if signing not in text:
        raise SystemExit("NuvioTV debug signing anchor missing")
    text = text.replace(
        signing,
        '        debug {\n            signingConfig = signingConfigs.getByName("debug")',
        1,
    )
    runner_anchor = '        versionName = "0.8.4-beta"\n'
    if runner_anchor not in text:
        raise SystemExit("NuvioTV defaultConfig anchor missing")
    text = text.replace(
        runner_anchor,
        runner_anchor + '        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"\n',
        1,
    )
    text += (
        '\n\ndependencies {\n'
        '    androidTestImplementation("androidx.test.ext:junit:1.3.0")\n'
        '    androidTestImplementation("androidx.test:runner:1.7.0")\n'
        '}\n'
    )
    build.write_text(text, encoding="utf-8")
    copy_bundles(repo / "app/src/androidTest/assets/niakvio")
    test = repo / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioFinalNativeTvTest.kt"
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text(TV_TEST, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "android"))
    parser.add_argument("--workspace", default=str(ROOT.parent))
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    if args.target == "desktop":
        prepare_desktop(workspace)
    else:
        prepare_mobile(workspace)
        prepare_tv(workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
