#!/usr/bin/env python3
"""Generate a real NuvioTV player lab beside the native provider corpus test.

The existing native corpus proves that the official PluginRuntime can execute a
provider and that its first URL is reachable. This lab goes one level further:
it feeds returned streams through NuvioTV's real PlayerMediaSourceFactory and
ExoPlayer, then through NuvioMpvSurfaceView/libmpv when ExoPlayer cannot prepare
the stream. The emitted evidence is intentionally sanitized: provider ids,
hostnames, status/error codes and format signatures are kept; raw URLs, cookies,
tokens and header values are never logged.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402


def _k(value: object) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def _provider_literal(fixture: dict) -> str:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    staged = corpus.manifest_providers()
    manifest_by_id = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers", [])
        if isinstance(row, dict)
    }
    requested = {
        str(value).casefold()
        for value in fixture.get("providers", [])
        if str(value).strip()
    }
    rows: list[str] = []
    for index, provider in enumerate(staged):
        meta = manifest_by_id.get(provider["id"].casefold(), {})
        supported = {
            str(value).casefold()
            for value in meta.get("supportedTypes", [])
            if str(value).strip()
        }
        movie_capable = not supported or "movie" in supported
        selected = provider["enabled"] and movie_capable
        if requested:
            selected = selected and provider["id"].casefold() in requested
        if not selected:
            continue
        rows.append(
            "ProviderSpec("
            f"id={_k(provider['id'])},asset={_k(f'p{index:03d}.js')},enabled=true"
            ")"
        )
    if not rows:
        raise SystemExit("player lab selected no enabled movie providers")
    return ",\n        ".join(rows)


def _fixture_values(fixture: dict) -> dict[str, str]:
    return {
        "slug": _k(fixture["slug"]),
        "tmdb": _k(fixture.get("tmdbId") or ""),
        "media_type": _k(fixture.get("mediaType") or "movie"),
        "season": "null" if fixture.get("season") in (None, "") else str(int(fixture["season"])),
        "episode": "null" if fixture.get("episode") in (None, "") else str(int(fixture["episode"])),
    }


def tv_test(fixture: dict, max_streams: int, timeout_ms: int) -> str:
    f = _fixture_values(fixture)
    providers = _provider_literal(fixture)
    return f'''package com.nuvio.tv.ui.screens.player

import android.os.SystemClock
import android.util.Log
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.test.platform.app.InstrumentationRegistry
import com.nuvio.tv.core.plugin.PluginRuntime
import com.nuvio.tv.domain.model.LocalScraperResult
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL
import java.util.Base64
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NiakvioNativePlayerLabTvTest {{
    data class ProviderSpec(val id: String, val asset: String, val enabled: Boolean)
    data class SourceEvidence(
        val status: Int,
        val contentType: String,
        val signature: String,
        val finalHost: String,
        val acceptsRanges: Boolean,
    )
    data class EngineProbe(
        val state: String,
        val code: Int,
        val codeName: String,
        val cause: String,
        val mimeType: String,
        val durationMs: Long,
    )

    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context = instrumentation.targetContext
    private val runtime = PluginRuntime()
    private val providers = listOf(
        {providers}
    )

    private fun code(asset: String): String = instrumentation.context.assets
        .open("niakvio/$asset").bufferedReader().use {{ it.readText() }}

    private fun b64(value: Any?): String = Base64.getUrlEncoder().withoutPadding()
        .encodeToString((value?.toString() ?: "").toByteArray(Charsets.UTF_8))

    private fun emit(message: String) {{
        println(message)
        Log.i("NiakvioPlayerLab", message)
    }}

    private fun hostOnly(raw: String): String = try {{ URI(raw).host.orEmpty().lowercase() }} catch (_: Throwable) {{ "" }}

    private fun rootCause(error: Throwable): String {{
        val parts = mutableListOf<String>()
        var current: Throwable? = error
        var depth = 0
        while (current != null && depth < 5) {{
            val name = current::class.simpleName.orEmpty()
            val message = current.message.orEmpty().replace(Regex("https?://\\S+"), "<url>")
            parts += if (message.isBlank()) name else "$name:$message"
            current = current.cause
            depth++
        }}
        return parts.joinToString(" <- ").take(700)
    }}

    private fun inspectSource(row: LocalScraperResult): SourceEvidence {{
        var connection: HttpURLConnection? = null
        return try {{
            connection = URL(row.url).openConnection() as HttpURLConnection
            connection.instanceFollowRedirects = true
            connection.connectTimeout = 8_000
            connection.readTimeout = 10_000
            connection.setRequestProperty("Range", "bytes=0-4095")
            connection.setRequestProperty("Accept", "application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,*/*;q=0.8")
            if (row.headers.orEmpty().keys.none {{ it.equals("User-Agent", ignoreCase = true) }}) {{
                connection.setRequestProperty("User-Agent", PlayerMediaSourceFactory.DEFAULT_USER_AGENT)
            }}
            row.headers.orEmpty().forEach {{ (key, value) ->
                if (!key.equals("Range", ignoreCase = true)) connection.setRequestProperty(key, value)
            }}
            val status = connection.responseCode
            val contentType = connection.contentType.orEmpty().substringBefore(';').trim().lowercase()
            val input = if (status in 200..299) connection.inputStream else connection.errorStream
            val bytes = if (input == null) ByteArray(0) else input.use {{ stream ->
                val out = java.io.ByteArrayOutputStream()
                val buffer = ByteArray(1024)
                while (out.size() < 4096) {{
                    val count = stream.read(buffer, 0, minOf(buffer.size, 4096 - out.size()))
                    if (count <= 0) break
                    out.write(buffer, 0, count)
                }}
                out.toByteArray()
            }}
            val text = runCatching {{ bytes.toString(Charsets.UTF_8).trimStart() }}.getOrDefault("")
            val signature = when {{
                text.startsWith("#EXTM3U", ignoreCase = true) -> "hls"
                text.startsWith("<MPD", ignoreCase = true) || (text.startsWith("<?xml") && text.contains("<MPD", ignoreCase = true)) -> "dash"
                bytes.size >= 8 && String(bytes.copyOfRange(4, 8), Charsets.ISO_8859_1) == "ftyp" -> "mp4_ftyp"
                bytes.size >= 4 && bytes[0].toInt() and 0xff == 0x1a && bytes[1].toInt() and 0xff == 0x45 && bytes[2].toInt() and 0xff == 0xdf && bytes[3].toInt() and 0xff == 0xa3 -> "matroska_ebml"
                bytes.size >= 376 && bytes[0].toInt() and 0xff == 0x47 && bytes[188].toInt() and 0xff == 0x47 -> "mpeg_ts"
                text.startsWith("<!doctype", ignoreCase = true) || text.startsWith("<html", ignoreCase = true) -> "html"
                text.startsWith("{{") || text.startsWith("[") -> "json"
                bytes.isEmpty() -> "empty"
                else -> "unknown_binary"
            }}
            SourceEvidence(
                status = status,
                contentType = contentType,
                signature = signature,
                finalHost = hostOnly(connection.url.toString()),
                acceptsRanges = connection.getHeaderField("Accept-Ranges")?.contains("bytes", ignoreCase = true) == true || status == 206,
            )
        }} catch (error: Throwable) {{
            SourceEvidence(0, error::class.simpleName.orEmpty(), "probe_error", hostOnly(row.url), false)
        }} finally {{
            connection?.disconnect()
        }}
    }}

    private suspend fun probeExo(row: LocalScraperResult): EngineProbe = withContext(Dispatchers.Main) {{
        val request = PlayerMediaSourceFactory.normalizePlaybackRequest(row.url, row.headers)
        val inferredMime = PlayerMediaSourceFactory.inferMimeType(request.url, filename = null, responseHeaders = emptyMap()).orEmpty()
        val factory = PlayerMediaSourceFactory(context).apply {{
            useParallelConnections = false
            vodCacheEnabled = false
            nuvioPerformanceModeEnabled = false
        }}
        val player = ExoPlayer.Builder(context).build()
        val result = CompletableDeferred<EngineProbe>()
        val listener = object : Player.Listener {{
            override fun onPlaybackStateChanged(playbackState: Int) {{
                if (playbackState == Player.STATE_READY && !result.isCompleted) {{
                    result.complete(EngineProbe("ready", 0, "READY", "", inferredMime, player.duration.coerceAtLeast(0L)))
                }}
            }}
            override fun onPlayerError(error: PlaybackException) {{
                if (!result.isCompleted) {{
                    result.complete(EngineProbe("error", error.errorCode, error.errorCodeName, rootCause(error), inferredMime, player.duration.coerceAtLeast(0L)))
                }}
            }}
        }}
        player.addListener(listener)
        try {{
            val mediaSource = factory.createMediaSource(
                context = context,
                url = request.url,
                headers = request.headers,
                filename = null,
                responseHeaders = emptyMap(),
                mimeTypeOverride = inferredMime.ifBlank {{ null }},
            )
            player.setMediaSource(mediaSource)
            player.playWhenReady = false
            player.prepare()
            withTimeoutOrNull({timeout_ms}L) {{ result.await() }}
                ?: EngineProbe("timeout", 0, "TIMEOUT", "", inferredMime, player.duration.coerceAtLeast(0L))
        }} catch (error: Throwable) {{
            EngineProbe("exception", 0, error::class.simpleName.orEmpty(), rootCause(error), inferredMime, player.duration.coerceAtLeast(0L))
        }} finally {{
            player.removeListener(listener)
            player.release()
            factory.shutdown()
        }}
    }}

    private suspend fun probeMpv(row: LocalScraperResult): EngineProbe {{
        var view: NuvioMpvSurfaceView? = null
        return try {{
            withContext(Dispatchers.Main) {{
                view = NuvioMpvSurfaceView(context)
                view!!.ensureInitialized()
                view!!.setMedia(row.url, row.headers.orEmpty())
                view!!.setPaused(false)
            }}
            val deadline = SystemClock.elapsedRealtime() + {timeout_ms}L
            var duration = 0L
            var video = false
            var idle = true
            while (SystemClock.elapsedRealtime() < deadline) {{
                withContext(Dispatchers.Main) {{
                    duration = view?.durationMs() ?: 0L
                    video = view?.hasVideoTrackSelectedNow() == true
                    idle = view?.isCoreIdleNow() != false
                }}
                if (video && (duration > 0L || !idle)) {{
                    return EngineProbe("ready", 0, "MPV_READY", "", "", duration)
                }}
                delay(400)
            }}
            EngineProbe("timeout", 0, "MPV_TIMEOUT", "video=$video idle=$idle", "", duration)
        }} catch (error: Throwable) {{
            EngineProbe("exception", 0, error::class.simpleName.orEmpty(), rootCause(error), "", 0L)
        }} finally {{
            withContext(Dispatchers.Main) {{ runCatching {{ view?.releasePlayer() }} }}
        }}
    }}

    private fun repairClass(exo: EngineProbe, mpv: EngineProbe?, source: SourceEvidence): String {{
        if (exo.state == "ready") return "healthy"
        if (source.status in listOf(401, 403, 407, 429, 451)) return "playback_context_gap"
        if (source.signature in setOf("html", "json", "empty", "probe_error")) return "media_extraction_gap"
        if (exo.code in listOf(2004, 2005, 2006, 2007, 2008)) return "playback_context_gap"
        if (exo.code == PlaybackException.ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED) {{
            if (mpv?.state == "ready") return "player_engine_compatibility_gap"
            return "player_container_unsupported"
        }}
        if (exo.code == PlaybackException.ERROR_CODE_PARSING_CONTAINER_MALFORMED) return "player_container_malformed"
        if (exo.code == PlaybackException.ERROR_CODE_PARSING_MANIFEST_UNSUPPORTED || exo.code == PlaybackException.ERROR_CODE_PARSING_MANIFEST_MALFORMED) return "player_manifest_gap"
        if (exo.code in 4001..4005) return "player_decoder_gap"
        if (source.signature == "unknown_binary") return "media_validation_gap"
        return "player_runtime_gap"
    }}

    @Test
    fun selectedFixtureThroughRealTvPlayers() = runBlocking {{
        val fixtureSlug = {f['slug']}
        val tmdbId = {f['tmdb']}
        val mediaType = {f['media_type']}
        val season: Int? = {f['season']}
        val episode: Int? = {f['episode']}
        var providersWithRows = 0
        var exoReadyProviders = 0
        var mpvRecoveredProviders = 0
        emit("FIELD_PLAYER_LAB_BEGIN client=tv fixture=$fixtureSlug providers=${{providers.size}} engines=exo,mpv")
        for (provider in providers) {{
            val rows = try {{
                runtime.executePlugin(
                    code = code(provider.asset),
                    tmdbId = tmdbId,
                    mediaType = mediaType,
                    season = season,
                    episode = episode,
                    scraperId = provider.id,
                )
            }} catch (error: Throwable) {{
                emit("FIELD_PLAYER_PROVIDER client=tv fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=runtime_error error64=${{b64(rootCause(error))}}")
                continue
            }}
            if (rows.isEmpty()) {{
                emit("FIELD_PLAYER_PROVIDER client=tv fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=empty streams=0")
                continue
            }}
            providersWithRows++
            var providerReady = false
            var providerMpvRecovered = false
            var lastRepair = "player_runtime_gap"
            for ((index, row) in rows.take({max_streams}).withIndex()) {{
                val source = withContext(Dispatchers.IO) {{ inspectSource(row) }}
                val exo = probeExo(row)
                val mpv = if (exo.state == "ready") null else probeMpv(row)
                val repair = repairClass(exo, mpv, source)
                lastRepair = repair
                emit(
                    "FIELD_PLAYER_ATTEMPT client=tv fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index " +
                    "host64=${{b64(hostOnly(row.url))}} final_host64=${{b64(source.finalHost)}} source_status=${{source.status}} " +
                    "content_type64=${{b64(source.contentType)}} signature=${{source.signature}} ranges=${{source.acceptsRanges}} " +
                    "exo_state=${{exo.state}} exo_code=${{exo.code}} exo_name=${{exo.codeName}} exo_mime64=${{b64(exo.mimeType)}} " +
                    "exo_cause64=${{b64(exo.cause)}} mpv_state=${{mpv?.state ?: "not_needed"}} mpv_name=${{mpv?.codeName ?: ""}} " +
                    "mpv_cause64=${{b64(mpv?.cause)}} repair_class=$repair"
                )
                if (exo.state == "ready") {{ providerReady = true; break }}
                if (mpv?.state == "ready") {{ providerMpvRecovered = true; break }}
            }}
            if (providerReady) exoReadyProviders++
            if (providerMpvRecovered) mpvRecoveredProviders++
            val state = when {{
                providerReady -> "exo_ready"
                providerMpvRecovered -> "mpv_only"
                else -> "unplayable"
            }}
            emit("FIELD_PLAYER_PROVIDER client=tv fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=$state streams=${{rows.size}} repair_class=$lastRepair")
        }}
        emit("FIELD_PLAYER_LAB_END client=tv fixture=$fixtureSlug providers_with_rows=$providersWithRows exo_ready=$exoReadyProviders mpv_recovered=$mpvRecoveredProviders")
        assertTrue("player lab provider selection must not be empty", providers.isNotEmpty())
    }}
}}
'''


def prepare_tv(workspace: Path, fixture: dict, max_streams: int, timeout_ms: int) -> Path:
    tv = workspace / "nuvio-tv"
    if not tv.is_dir():
        raise SystemExit(f"missing NuvioTV checkout: {tv}")
    assets = tv / "app/src/androidTest/assets/niakvio"
    if not assets.is_dir():
        raise SystemExit("native corpus assets must be staged before preparing player lab")
    target = tv / "app/src/androidTest/java/com/nuvio/tv/ui/screens/player/NiakvioNativePlayerLabTvTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(tv_test(fixture, max_streams=max_streams, timeout_ms=timeout_ms), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("tv",))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--max-streams", type=int, default=3)
    parser.add_argument("--timeout-ms", type=int, default=18_000)
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    target = prepare_tv(
        workspace,
        fixture,
        max_streams=max(1, min(args.max_streams, 5)),
        timeout_ms=max(4_000, min(args.timeout_ms, 30_000)),
    )
    print(f"FIELD_PLAYER_LAB_PREPARED target=tv fixture={args.fixture} path={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
