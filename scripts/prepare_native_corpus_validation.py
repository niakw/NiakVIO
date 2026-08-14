#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def kotlin_string(value: object) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def fixture_by_slug(slug: str) -> dict:
    config = load_json(CORPUS)
    for row in config.get("fixtures", []):
        if isinstance(row, dict) and str(row.get("slug") or "") == slug:
            fixture = row.get("fixture")
            if not isinstance(fixture, dict):
                break
            return {"slug": slug, **fixture}
    raise SystemExit(f"unknown native corpus fixture: {slug}")


def manifest_providers() -> list[dict]:
    manifest = load_json(ROOT / "manifest.json")
    providers: list[dict] = []
    seen: set[str] = set()
    for row in manifest.get("scrapers", []):
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        filename = str(row.get("filename") or "").strip()
        key = provider_id.casefold()
        if not provider_id or not filename or key in seen:
            continue
        source = ROOT / filename
        if not source.is_file():
            raise SystemExit(f"manifest provider bundle missing: {provider_id} -> {filename}")
        seen.add(key)
        providers.append(
            {
                "id": provider_id,
                "enabled": bool(row.get("enabled")),
                "filename": filename,
                "source": source,
            }
        )
    if not providers:
        raise SystemExit("manifest contains no stageable providers")
    return providers


def stage_providers(destination: Path) -> list[dict]:
    providers = manifest_providers()
    destination.mkdir(parents=True, exist_ok=True)
    staged: list[dict] = []
    for index, provider in enumerate(providers):
        asset = f"p{index:03d}.js"
        shutil.copy2(provider["source"], destination / asset)
        staged.append({**provider, "asset": asset})
    print(
        f"FIELD_NATIVE_CORPUS_STAGE providers={len(staged)} "
        f"enabled={sum(1 for row in staged if row['enabled'])} disabled={sum(1 for row in staged if not row['enabled'])}"
    )
    return staged


def provider_literal(providers: list[dict]) -> str:
    rows = []
    for provider in providers:
        rows.append(
            "ProviderSpec("
            f"id={kotlin_string(provider['id'])},"
            f"asset={kotlin_string(provider['asset'])},"
            f"enabled={'true' if provider['enabled'] else 'false'}"
            ")"
        )
    return ",\n        ".join(rows)


def common_fixture_values(fixture: dict) -> dict[str, str]:
    season = fixture.get("season")
    episode = fixture.get("episode")
    return {
        "slug": kotlin_string(fixture["slug"]),
        "tmdb": kotlin_string(fixture.get("tmdbId") or ""),
        "media_type": kotlin_string(fixture.get("mediaType") or "movie"),
        "title": kotlin_string(fixture.get("title") or fixture["slug"]),
        "season": "null" if season in (None, "") else str(int(season)),
        "episode": "null" if episode in (None, "") else str(int(episode)),
    }


def desktop_test(fixture: dict, providers: list[dict]) -> str:
    f = common_fixture_values(fixture)
    return f'''package com.nuvio.app.features.plugins

import com.nuvio.app.features.plugins.runtime.PluginRuntime
import java.io.File
import java.util.Base64
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertTrue

class NiakvioNativeCorpusDesktopTest {{
    data class ProviderSpec(val id: String, val asset: String, val enabled: Boolean)

    private val workspace = File(System.getenv("GITHUB_WORKSPACE"))
    private val root = File(workspace, "niakvio/native-corpus-stage")
    private val resultFile = File(workspace, "desktop-native-corpus-{fixture['slug']}.log")
    private val providers = listOf(
        {provider_literal(providers)}
    )

    private fun b64(value: Any?): String = Base64.getUrlEncoder().withoutPadding()
        .encodeToString((value?.toString() ?: "").toByteArray(Charsets.UTF_8))

    private fun emit(message: String) {{
        println(message)
        resultFile.appendText(message + "\\n")
    }}

    @Test
    fun selectedFixtureAcrossEveryProvider() = runBlocking {{
        val fixtureSlug = {f['slug']}
        val tmdbId = {f['tmdb']}
        val mediaType = {f['media_type']}
        val title = {f['title']}
        val season: Int? = {f['season']}
        val episode: Int? = {f['episode']}
        val errors = mutableListOf<String>()
        emit("FIELD_NATIVE_CORPUS_BEGIN client=desktop fixture=$fixtureSlug title64=${{b64(title)}} providers=${{providers.size}}")
        for (provider in providers) {{
            val started = System.currentTimeMillis()
            try {{
                val rows = PluginRuntime.executePlugin(
                    code = File(root, provider.asset).readText(),
                    tmdbId = tmdbId,
                    mediaType = mediaType,
                    season = season,
                    episode = episode,
                    scraperId = provider.id,
                )
                emit("FIELD_NATIVE_RESULT client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} duration_ms=${{System.currentTimeMillis()-started}} count=${{rows.size}}")
                rows.take(3).forEachIndexed {{ index, row ->
                    emit("FIELD_NATIVE_ROW client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index title64=${{b64(row.title)}} name64=${{b64(row.name)}} quality64=${{b64(row.quality)}} language64=${{b64(row.language)}} type64=${{b64(row.type)}} url64=${{b64(row.url)}}")
                }}
            }} catch (error: Throwable) {{
                errors += provider.id + ":" + (error.message ?: error::class.simpleName.orEmpty())
                emit("FIELD_NATIVE_ERROR client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} duration_ms=${{System.currentTimeMillis()-started}} error64=${{b64(error.message ?: error.toString())}}")
            }}
        }}
        emit("FIELD_NATIVE_CORPUS_END client=desktop fixture=$fixtureSlug errors=${{errors.size}}")
        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))
    }}
}}
'''


def android_test(fixture: dict, providers: list[dict], client: str) -> str:
    f = common_fixture_values(fixture)
    if client == "mobile":
        package = "com.nuvio.app.features.plugins"
        klass = "NiakvioNativeCorpusMobileTest"
        runtime_decl = ""
        execute = "PluginRuntime.executePlugin"
        imports = "import com.nuvio.app.features.plugins.runtime.PluginRuntime"
    else:
        package = "com.nuvio.tv.core.plugin"
        klass = "NiakvioNativeCorpusTvTest"
        runtime_decl = "    private val runtime = PluginRuntime()\n"
        execute = "runtime.executePlugin"
        imports = ""
    return f'''package {package}

import android.util.Log
import androidx.test.platform.app.InstrumentationRegistry
{imports}
import java.util.Base64
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Test

class {klass} {{
    data class ProviderSpec(val id: String, val asset: String, val enabled: Boolean)
{runtime_decl}    private val providers = listOf(
        {provider_literal(providers)}
    )

    private fun code(asset: String): String =
        InstrumentationRegistry.getInstrumentation().context.assets
            .open("niakvio/$asset").bufferedReader().use {{ it.readText() }}

    private fun b64(value: Any?): String = Base64.getUrlEncoder().withoutPadding()
        .encodeToString((value?.toString() ?: "").toByteArray(Charsets.UTF_8))

    private fun emit(message: String) {{
        println(message)
        Log.i("NiakvioCorpus", message)
    }}

    @Test
    fun selectedFixtureAcrossEveryProvider() = runBlocking {{
        val fixtureSlug = {f['slug']}
        val tmdbId = {f['tmdb']}
        val mediaType = {f['media_type']}
        val title = {f['title']}
        val season: Int? = {f['season']}
        val episode: Int? = {f['episode']}
        val errors = mutableListOf<String>()
        emit("FIELD_NATIVE_CORPUS_BEGIN client={client} fixture=$fixtureSlug title64=${{b64(title)}} providers=${{providers.size}}")
        for (provider in providers) {{
            val started = System.currentTimeMillis()
            try {{
                val rows = {execute}(
                    code = code(provider.asset),
                    tmdbId = tmdbId,
                    mediaType = mediaType,
                    season = season,
                    episode = episode,
                    scraperId = provider.id,
                )
                emit("FIELD_NATIVE_RESULT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} duration_ms=${{System.currentTimeMillis()-started}} count=${{rows.size}}")
                rows.take(3).forEachIndexed {{ index, row ->
                    emit("FIELD_NATIVE_ROW client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index title64=${{b64(row.title)}} name64=${{b64(row.name)}} quality64=${{b64(row.quality)}} language64=${{b64(row.language)}} type64=${{b64(row.type)}} url64=${{b64(row.url)}}")
                }}
            }} catch (error: Throwable) {{
                errors += provider.id + ":" + (error.message ?: error::class.simpleName.orEmpty())
                emit("FIELD_NATIVE_ERROR client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} duration_ms=${{System.currentTimeMillis()-started}} error64=${{b64(error.message ?: error.toString())}}")
            }}
        }}
        emit("FIELD_NATIVE_CORPUS_END client={client} fixture=$fixtureSlug errors=${{errors.size}}")
        assertTrue("native provider runtime errors: " + errors.take(12).joinToString(" | "), errors.isEmpty())
    }}
}}
'''


def prepare_desktop(workspace: Path, fixture: dict) -> None:
    providers = stage_providers(ROOT / "native-corpus-stage")
    target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(desktop_test(fixture, providers), encoding="utf-8")


def enable_mobile_device_tests(repo: Path) -> None:
    build = repo / "composeApp/build.gradle.kts"
    text = build.read_text(encoding="utf-8")
    compilation_needle = "        withHostTest {}\n\n        compilerOptions {"
    compilation_replacement = '''        withHostTest {}
        withDeviceTest {
            instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
            execution = "HOST"
        }

        compilerOptions {'''
    if text.count(compilation_needle) != 1:
        raise SystemExit(f"mobile device-test compilation anchor count={text.count(compilation_needle)}")
    text = text.replace(compilation_needle, compilation_replacement, 1)
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
        raise SystemExit(f"mobile device-test dependency anchor count={text.count(source_needle)}")
    build.write_text(text.replace(source_needle, source_replacement, 1), encoding="utf-8")
    (repo / "composeApp/src/androidMain/AndroidManifest.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <uses-permission android:name="android.permission.INTERNET" />\n'
        '</manifest>\n',
        encoding="utf-8",
    )


def enable_tv_tests(repo: Path) -> None:
    build = repo / "app/build.gradle.kts"
    text = build.read_text(encoding="utf-8")
    signing = '        debug {\n            signingConfig = signingConfigs.getByName("release")'
    if signing not in text:
        raise SystemExit("NuvioTV debug signing anchor missing")
    text = text.replace(signing, '        debug {\n            signingConfig = signingConfigs.getByName("debug")', 1)
    runner_anchor = '        versionName = "0.8.4-beta"\n'
    if runner_anchor not in text:
        raise SystemExit("NuvioTV defaultConfig anchor missing")
    text = text.replace(runner_anchor, runner_anchor + '        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"\n', 1)
    text += (
        '\n\ndependencies {\n'
        '    androidTestImplementation("androidx.test.ext:junit:1.3.0")\n'
        '    androidTestImplementation("androidx.test:runner:1.7.0")\n'
        '}\n'
    )
    build.write_text(text, encoding="utf-8")


def prepare_android(workspace: Path, fixture: dict) -> None:
    providers = manifest_providers()

    mobile = workspace / "nuvio-mobile"
    enable_mobile_device_tests(mobile)
    mobile_assets = mobile / "composeApp/src/androidDeviceTest/assets/niakvio"
    staged = stage_providers(mobile_assets)
    mobile_test = mobile / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
    mobile_test.parent.mkdir(parents=True, exist_ok=True)
    mobile_test.write_text(android_test(fixture, staged, "mobile"), encoding="utf-8")

    tv = workspace / "nuvio-tv"
    enable_tv_tests(tv)
    tv_assets = tv / "app/src/androidTest/assets/niakvio"
    tv_assets.mkdir(parents=True, exist_ok=True)
    for provider in staged:
        shutil.copy2(provider["source"], tv_assets / provider["asset"])
    tv_test = tv / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    tv_test.parent.mkdir(parents=True, exist_ok=True)
    tv_test.write_text(android_test(fixture, staged, "tv"), encoding="utf-8")

    if len(providers) != len(staged):
        raise SystemExit("native corpus staging changed provider population")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "android"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", default=str(ROOT.parent))
    args = parser.parse_args()
    fixture = fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    if args.target == "desktop":
        prepare_desktop(workspace, fixture)
    else:
        prepare_android(workspace, fixture)
    print(
        f"FIELD_NATIVE_CORPUS_PREPARED target={args.target} fixture={args.fixture} "
        f"title={fixture.get('title')} tmdb={fixture.get('tmdbId')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
