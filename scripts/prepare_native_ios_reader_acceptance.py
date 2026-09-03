#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
PROVIDER_TIMEOUT_MS = 40_000
NUVIO_MOBILE = Path("nuvio-mobile")
IOS_KOTLIN_TARGET = Path("nuvio-mobile/composeApp/src/iosFull/kotlin/com/nuvio/app/NiakvioIosLab.kt")

KOTLIN_TEMPLATE = r'''@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.nuvio.app

import com.nuvio.app.features.addons.httpGetText
import com.nuvio.app.features.player.NuvioPlayerBridgeFactory
import com.nuvio.app.features.plugins.PluginManifestParser
import com.nuvio.app.features.plugins.PluginRepository
import com.nuvio.app.features.plugins.PluginRuntimeResult
import com.nuvio.app.features.plugins.PluginScraper
import kotlinx.cinterop.toKString
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import platform.Foundation.NSURL
import platform.UIKit.UIApplication
import platform.UIKit.UIModalPresentationFullScreen
import platform.posix.exit
import platform.posix.getenv
import kotlin.time.TimeSource

private const val FULL_PROVIDER_TIMEOUT_MS = __PROVIDER_TIMEOUT_MS__L
private const val FULL_PLAYER_TIMEOUT_MS = 22000L
private const val LEARNING_PROVIDER_TIMEOUT_MS = 8000L
private const val LEARNING_PLAYER_TIMEOUT_MS = 6000L
private val json = Json { encodeDefaults = true }

@Serializable
private data class Fixture(
    val slug: String,
    val tmdbId: String,
    val mediaType: String,
    val season: Int? = null,
    val episode: Int? = null,
)

@Serializable
private data class ResultObservation(
    val fixture: String,
    val provider: String,
    val mediaType: String,
    val enabled: Boolean,
    val count: Int,
    val durationMs: Long,
    val state: String,
)

@Serializable
private data class PlayerObservation(
    val fixture: String,
    val provider: String,
    val mediaType: String,
    val state: String,
    val engine: String,
    val durationSeconds: Double,
    val host: String,
    val errorClass: String,
)

private val fixtures = __FIXTURES__
private var started = false

private fun env(name: String): String = getenv(name)?.toKString().orEmpty()
private fun envLong(name: String, fallback: Long, min: Long, max: Long): Long =
    env(name).toLongOrNull()?.coerceIn(min, max) ?: fallback

private fun normalizedType(value: String): String = when (value.lowercase()) {
    "series", "show", "other" -> "tv"
    else -> value.lowercase()
}

private fun emit(marker: String, payload: Any) {
    val encoded = when (payload) {
        is ResultObservation -> json.encodeToString(payload)
        is PlayerObservation -> json.encodeToString(payload)
        else -> payload.toString()
    }
    println("$marker $encoded")
}

private fun supportsIos(supported: List<String>?, disabled: List<String>?): Boolean {
    val allow = supported.orEmpty().map(String::lowercase).toSet()
    val deny = disabled.orEmpty().map(String::lowercase).toSet()
    return (allow.isEmpty() || "ios" in allow) && "ios" !in deny
}

private fun codeUrl(manifestUrl: String, filename: String): String {
    if (filename.startsWith("http://") || filename.startsWith("https://")) return filename
    val base = manifestUrl.substringBefore("?").removeSuffix("/manifest.json")
    return "$base/${filename.trimStart('/')}"
}

private fun hostOnly(url: String): String = NSURL.URLWithString(url)?.host.orEmpty()

private suspend fun probeProductionPlayer(row: PluginRuntimeResult, playerTimeoutMs: Long): Triple<String, Double, String> =
    withContext(Dispatchers.Main) {
        val bridge = NuvioPlayerBridgeFactory.create()
            ?: return@withContext Triple("bridge_unavailable", 0.0, "")
        val host = hostOnly(row.url)
        val root = UIApplication.sharedApplication.keyWindow?.rootViewController
        val controller = bridge.createPlayerViewController()
        controller.modalPresentationStyle = UIModalPresentationFullScreen
        if (root != null) {
            root.presentViewController(controller, animated = false, completion = null)
            delay(250L)
        }
        try {
            val headersJson = row.headers
                ?.takeIf { it.isNotEmpty() }
                ?.let { json.encodeToString(it) }
            bridge.loadFileWithAudio(
                videoUrl = row.url,
                audioUrl = null,
                headersJson = headersJson,
                subtitlesJson = null,
            )
            bridge.play()
            var state = "timeout"
            var duration = 0.0
            for (attempt in 0 until (playerTimeoutMs / 250L).toInt()) {
                delay(250L)
                duration = bridge.getDurationMs().toDouble() / 1000.0
                val error = bridge.getErrorMessage().trim()
                if (error.isNotEmpty()) {
                    state = "error"
                    break
                }
                if (bridge.getIsPlaying() || bridge.getIsEnded() || duration > 0.0) {
                    state = if (bridge.getIsEnded()) "ended" else "ready"
                    break
                }
            }
            Triple(state, duration, host)
        } finally {
            bridge.destroy()
            if (root?.presentedViewController === controller) {
                root.dismissViewControllerAnimated(false, completion = null)
            }
        }
    }

private suspend fun runLab(manifestUrl: String) {
    val manifestPayload = httpGetText(manifestUrl)
    val manifest = PluginManifestParser.parse(manifestPayload)
    val mode = env("NIAKVIO_IOS_LAB_MODE").lowercase().ifBlank { "full" }
    val targetProvider = env("NIAKVIO_IOS_TARGET_PROVIDER").lowercase()
    val learning = mode == "learning" || mode == "quick"
    val resumeFixture = env("NIAKVIO_IOS_RESUME_FIXTURE")
    val resumeAfterProvider = env("NIAKVIO_IOS_RESUME_AFTER_PROVIDER")
    val providerTimeoutMs = envLong(
        "NIAKVIO_IOS_PROVIDER_TIMEOUT_MS",
        if (learning) LEARNING_PROVIDER_TIMEOUT_MS else FULL_PROVIDER_TIMEOUT_MS,
        3000L,
        60000L,
    )
    val playerTimeoutMs = envLong(
        "NIAKVIO_IOS_PLAYER_TIMEOUT_MS",
        if (learning) LEARNING_PLAYER_TIMEOUT_MS else FULL_PLAYER_TIMEOUT_MS,
        3000L,
        30000L,
    )
    val allIosProviders = manifest.scrapers.filter {
        supportsIos(it.supportedPlatforms, it.disabledPlatforms)
    }
    val iosProviders = if (learning) {
        if (targetProvider.isBlank()) error("learning iOS Lab requires NIAKVIO_IOS_TARGET_PROVIDER")
        allIosProviders.filter { it.id.lowercase() == targetProvider }
            .also { if (it.size != 1) error("learning iOS Lab target provider not found: $targetProvider") }
    } else allIosProviders
    val fixturesForRun = if (learning) {
        val firstType = iosProviders.first().supportedTypes
            .map(::normalizedType)
            .firstOrNull { it in setOf("movie", "tv", "anime") }
            ?: "movie"
        listOf(fixtures.first { it.mediaType == firstType })
    } else fixtures
    val resumedFixtures = if (!learning && resumeFixture.isNotBlank()) {
        val index = fixturesForRun.indexOfFirst { it.slug == resumeFixture }
        if (index >= 0) fixturesForRun.drop(index) else fixturesForRun
    } else fixturesForRun
    println("FIELD_NATIVE_CORPUS_IOS_BEGIN mode=$mode fixtures=${resumedFixtures.size} providers=${iosProviders.size} target=$targetProvider provider_timeout_ms=$providerTimeoutMs player_timeout_ms=$playerTimeoutMs resume_fixture=$resumeFixture resume_after=$resumeAfterProvider")

    resumedFixtures.forEach { fixture ->
        val selectedBase = iosProviders.filter { provider ->
            provider.supportedTypes.any { type ->
                normalizedType(type) == fixture.mediaType
            }
        }
        val selected = if (!learning && fixture.slug == resumeFixture && resumeAfterProvider.isNotBlank()) {
            val resumeIndex = selectedBase.indexOfFirst { it.id.equals(resumeAfterProvider, ignoreCase = true) }
            if (resumeIndex >= 0) {
                val blocked = selectedBase[resumeIndex]
                emit(
                    "FIELD_NATIVE_IOS_RESULT",
                    ResultObservation(
                        fixture = fixture.slug,
                        provider = blocked.id,
                        mediaType = fixture.mediaType,
                        enabled = blocked.enabled,
                        count = 0,
                        durationMs = providerTimeoutMs,
                        state = "timeout",
                    ),
                )
                println("FIELD_NATIVE_IOS_PROVIDER_END fixture=${fixture.slug} provider=${blocked.id} state=watchdog_timeout duration_ms=$providerTimeoutMs")
                selectedBase.drop(resumeIndex + 1)
            } else selectedBase
        } else selectedBase
        println("FIELD_NATIVE_IOS_FIXTURE_BEGIN fixture=${fixture.slug} type=${fixture.mediaType} providers=${selected.size}")
        selected.forEach { info ->
            val startedAt = TimeSource.Monotonic.markNow()
            println("FIELD_NATIVE_IOS_PROVIDER_BEGIN fixture=${fixture.slug} provider=${info.id} type=${fixture.mediaType} enabled=${info.enabled}")
            try {
                val code = withTimeout(providerTimeoutMs) {
                    httpGetText(codeUrl(manifestUrl, info.filename))
                }
                val scraper = PluginScraper(
                    id = info.id,
                    repositoryUrl = manifestUrl,
                    name = info.name,
                    description = info.description.orEmpty(),
                    version = info.version,
                    filename = info.filename,
                    supportedTypes = info.supportedTypes,
                    enabled = info.enabled,
                    manifestEnabled = info.enabled,
                    hasSettings = info.hasSettings,
                    logo = info.logo,
                    contentLanguage = info.contentLanguage ?: emptyList(),
                    formats = info.formats ?: info.supportedFormats,
                    code = code,
                )
                val rows = withTimeout(providerTimeoutMs) {
                    PluginRepository.executeScraper(
                        scraper = scraper,
                        tmdbId = fixture.tmdbId,
                        mediaType = fixture.mediaType,
                        season = fixture.season,
                        episode = fixture.episode,
                    ).getOrThrow()
                }
                emit(
                    "FIELD_NATIVE_IOS_RESULT",
                    ResultObservation(
                        fixture = fixture.slug,
                        provider = info.id,
                        mediaType = fixture.mediaType,
                        enabled = info.enabled,
                        count = rows.size,
                        durationMs = startedAt.elapsedNow().inWholeMilliseconds,
                        state = "completed",
                    ),
                )
                rows.firstOrNull()?.let { row ->
                    val (playerState, durationSeconds, host) = probeProductionPlayer(row, playerTimeoutMs)
                    emit(
                        "FIELD_NATIVE_IOS_PLAYER",
                        PlayerObservation(
                            fixture = fixture.slug,
                            provider = info.id,
                            mediaType = fixture.mediaType,
                            state = playerState,
                            engine = "nuvio-mobile-ios-production",
                            durationSeconds = durationSeconds,
                            host = host,
                            errorClass = if (playerState == "error") "player_error" else "",
                        ),
                    )
                }
                println("FIELD_NATIVE_IOS_PROVIDER_END fixture=${fixture.slug} provider=${info.id} state=completed duration_ms=${startedAt.elapsedNow().inWholeMilliseconds}")
            } catch (error: Throwable) {
                println("FIELD_NATIVE_IOS_PROVIDER_END fixture=${fixture.slug} provider=${info.id} state=${if (error is TimeoutCancellationException) "timeout" else "error"} duration_ms=${startedAt.elapsedNow().inWholeMilliseconds}")
                emit(
                    "FIELD_NATIVE_IOS_RESULT",
                    ResultObservation(
                        fixture = fixture.slug,
                        provider = info.id,
                        mediaType = fixture.mediaType,
                        enabled = info.enabled,
                        count = 0,
                        durationMs = startedAt.elapsedNow().inWholeMilliseconds,
                        state = if (error is TimeoutCancellationException) "timeout" else "error",
                    ),
                )
            }
        }
        println("FIELD_NATIVE_IOS_FIXTURE_END fixture=${fixture.slug} type=${fixture.mediaType} providers=${selected.size}")
    }
    println("FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=completed mode=$mode fixtures=${fixturesForRun.size} target=$targetProvider")
}

fun startNiakvioIosLabIfRequested() {
    if (started || env("NIAKVIO_IOS_LAB") != "1") return
    started = true
    val manifestUrl = env("NIAKVIO_MANIFEST_URL")
    if (manifestUrl.isBlank()) {
        println("FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=missing_manifest_url")
        exit(2)
    }
    CoroutineScope(SupervisorJob() + Dispatchers.Default).launch {
        try {
            runLab(manifestUrl)
            exit(0)
        } catch (error: Throwable) {
            println("FIELD_NATIVE_CORPUS_IOS_SUITE_STATUS status=infra_error reason=${error::class.simpleName ?: "Throwable"}")
            exit(2)
        }
    }
}
'''

def fixture_rows() -> list[dict]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    acceptance = data.get("native_reader_acceptance") or {}
    fixture_by_type = acceptance.get("fixture_by_type") or {}
    wanted = [fixture_by_type.get(kind) for kind in ("movie", "tv", "anime")]
    index = {
        str(row.get("slug") or ""): row.get("fixture") or {}
        for row in data.get("fixtures") or []
        if isinstance(row, dict)
    }
    rows = []
    for kind, slug in zip(("movie", "tv", "anime"), wanted):
        if not slug or slug not in index:
            raise SystemExit(f"missing canonical fixture for {kind}: {slug!r}")
        fixture = index[slug]
        rows.append(
            {
                "slug": slug,
                "tmdbId": str(fixture.get("tmdbId") or ""),
                "mediaType": kind,
                "season": fixture.get("season"),
                "episode": fixture.get("episode"),
            }
        )
    return rows

def kotlin_fixture_list(rows: list[dict]) -> str:
    values = []
    for row in rows:
        season = "null" if row["season"] is None else str(int(row["season"]))
        episode = "null" if row["episode"] is None else str(int(row["episode"]))
        values.append(
            "Fixture(slug = {slug}, tmdbId = {tmdb}, mediaType = {kind}, season = {season}, episode = {episode})".format(
                slug=json.dumps(row["slug"]),
                tmdb=json.dumps(row["tmdbId"]),
                kind=json.dumps(row["mediaType"]),
                season=season,
                episode=episode,
            )
        )
    return "listOf(\n    " + ",\n    ".join(values) + "\n)"

def main() -> int:
    # The workflow checks NiakVIO out as ./niakvio and NuvioMobile as
    # ./nuvio-mobile. Validate that fixed layout before touching the sibling
    # checkout; all write targets below are literal relative paths.
    if (Path("niakvio").resolve(strict=True)) != ROOT:
        raise SystemExit("unexpected workspace layout for the iOS native Lab")
    repo = NUVIO_MOBILE
    if not repo.is_dir():
        raise SystemExit(f"missing NuvioMobile checkout: {repo}")
    rows = fixture_rows()
    source = KOTLIN_TEMPLATE.replace("__PROVIDER_TIMEOUT_MS__", str(PROVIDER_TIMEOUT_MS))
    source = source.replace("__FIXTURES__", kotlin_fixture_list(rows))
    IOS_KOTLIN_TARGET.parent.mkdir(parents=True, exist_ok=True)
    IOS_KOTLIN_TARGET.write_text(source, encoding="utf-8")
    print("FIELD_NATIVE_IOS_PREPARED fixtures=" + ",".join(row["slug"] for row in rows))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
