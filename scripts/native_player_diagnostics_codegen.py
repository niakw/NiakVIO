#!/usr/bin/env python3
"""Augment generated Android native-corpus tests with real Media3 reader diagnostics."""
from __future__ import annotations
from typing import Iterable

ANDROID_IMPORT_ANCHOR = "import android.util.Log\n"
TEST_ANCHOR = "    @Test\n"

COMMON_IMPORTS = """import android.os.Handler
import android.os.Looper
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.datasource.HttpDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
"""
TV_IMPORT = "import com.nuvio.tv.ui.screens.player.PlayerPlaybackNetworking\n"
MOBILE_IMPORT = "import com.nuvio.app.features.player.PlatformPlaybackDataSourceFactory\n"

PLAYER_HELPERS_TEMPLATE = r'''
    data class NativePlayerProbe(
        val state: String,
        val engine: String,
        val errorClass: String,
        val errorCode: String,
        val httpStatus: Int,
        val failureStage: String,
        val host: String,
        val durationSeconds: Double?,
        val exceptionChain: String,
        val responseHeaderNames: String,
    )

    private fun sanitizeDiag(raw: String?): String {
        if (raw.isNullOrBlank()) return ""
        return raw
            .replace(Regex("https?://\\S+", RegexOption.IGNORE_CASE), "<url>")
            .replace(Regex("(?i)(authorization|cookie|token|secret)\\s*[:=]\\s*\\S+"), "$1=<redacted>")
            .replace(Regex("\\s+"), " ")
            .take(420)
    }

    private fun exceptionChain(error: Throwable?): String {
        val out = mutableListOf<String>()
        var current = error
        var depth = 0
        while (current != null && depth < 8) {
            val name = current::class.qualifiedName ?: current::class.simpleName.orEmpty()
            val message = sanitizeDiag(current.message)
            out += if (message.isBlank()) name else "$name:$message"
            current = current.cause
            depth += 1
        }
        return out.joinToString(" -> ").take(1000)
    }

    private fun invalidResponse(error: Throwable?): HttpDataSource.InvalidResponseCodeException? {
        var current = error
        var depth = 0
        while (current != null && depth < 10) {
            if (current is HttpDataSource.InvalidResponseCodeException) return current
            current = current.cause
            depth += 1
        }
        return null
    }

    private fun playerFailureStage(error: PlaybackException?): String {
        if (error == null) return "none"
        val response = invalidResponse(error)
        if (response != null) return when (response.responseCode) {
            401, 403, 407, 451 -> "http_access"
            404, 410 -> "http_gone"
            429 -> "http_rate_limit"
            in 500..599 -> "http_upstream"
            else -> "http_response"
        }
        val code = error.errorCodeName.lowercase()
        val chain = exceptionChain(error).lowercase()
        return when {
            "timeout" in chain -> "timeout"
            "unknownhost" in chain || "dns" in chain -> "dns"
            "ssl" in chain || "certificate" in chain || "handshake" in chain -> "tls"
            "parser" in code || "parsing" in code || "unrecognized" in chain -> "parser"
            "decoder" in code || "codec" in code || "mediacodec" in chain -> "decoder"
            "behind_live_window" in code -> "live_window"
            "io_" in code || "datasource" in chain || "http" in chain -> "io"
            else -> "player"
        }
    }

    private fun nativeReaderDataSource(
        context: android.content.Context,
        headers: Map<String, String>,
    ): androidx.media3.datasource.DataSource.Factory {
        __DATA_SOURCE_FACTORY__
    }

    private fun probeNativePlayer(
        url: String,
        headers: Map<String, String>?,
        expectedDurationMinutes: Int,
    ): NativePlayerProbe {
        val host = hostOnly(url)
        val terminal = CountDownLatch(1)
        val outcome = AtomicReference<NativePlayerProbe?>(null)
        val playerRef = AtomicReference<ExoPlayer?>(null)
        val safeHeaders = headers.orEmpty().filterKeys { !it.equals("Range", ignoreCase = true) }
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val handler = Handler(Looper.getMainLooper())

        fun complete(probe: NativePlayerProbe) {
            if (outcome.compareAndSet(null, probe)) terminal.countDown()
        }

        try {
            instrumentation.runOnMainSync {
                val dataSourceFactory = nativeReaderDataSource(context, safeHeaders)
                val player = ExoPlayer.Builder(context)
                    .setMediaSourceFactory(DefaultMediaSourceFactory(dataSourceFactory))
                    .build()
                playerRef.set(player)
                player.addListener(object : Player.Listener {
                    override fun onPlayerError(error: PlaybackException) {
                        val response = invalidResponse(error)
                        val headerNames = response?.headerFields?.keys
                            ?.filterNotNull()?.map { it.lowercase() }?.distinct()?.sorted()?.joinToString(",").orEmpty()
                        complete(NativePlayerProbe(
                            state = "error", engine = "media3",
                            errorClass = error::class.qualifiedName.orEmpty(), errorCode = error.errorCodeName,
                            httpStatus = response?.responseCode ?: 0, failureStage = playerFailureStage(error),
                            host = host, durationSeconds = null, exceptionChain = exceptionChain(error),
                            responseHeaderNames = headerNames.take(360),
                        ))
                    }

                    override fun onPlaybackStateChanged(state: Int) {
                        if (state == Player.STATE_READY) {
                            val durationMs = player.duration
                            val durationSeconds = if (durationMs > 0 && durationMs != C.TIME_UNSET) durationMs / 1000.0 else null
                            val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
                            val shortMedia = durationSeconds != null && (durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55))
                            handler.postDelayed({
                                complete(NativePlayerProbe(
                                    state = if (shortMedia) "short_media" else "ready", engine = "media3",
                                    errorClass = "", errorCode = "", httpStatus = 0,
                                    failureStage = if (shortMedia) "duration_identity" else "none",
                                    host = host, durationSeconds = durationSeconds, exceptionChain = "", responseHeaderNames = "",
                                ))
                            }, 2500L)
                        } else if (state == Player.STATE_ENDED) {
                            val durationMs = player.duration
                            val durationSeconds = if (durationMs > 0 && durationMs != C.TIME_UNSET) durationMs / 1000.0 else null
                            complete(NativePlayerProbe("ended", "media3", "", "", 0, "none", host, durationSeconds, "", ""))
                        }
                    }
                })
                player.setMediaItem(MediaItem.fromUri(url))
                player.playWhenReady = true
                player.prepare()
            }
            if (!terminal.await(18, TimeUnit.SECONDS)) {
                complete(NativePlayerProbe("timeout", "media3", "reader_timeout", "", 0, "timeout", host, null, "", ""))
            }
            return outcome.get() ?: NativePlayerProbe("unknown", "media3", "", "", 0, "player", host, null, "", "")
        } catch (error: Throwable) {
            return NativePlayerProbe(
                state = "error", engine = "media3", errorClass = error::class.qualifiedName.orEmpty(), errorCode = "",
                httpStatus = invalidResponse(error)?.responseCode ?: 0,
                failureStage = when {
                    error::class.qualifiedName.orEmpty().contains("UnknownHost", ignoreCase = true) -> "dns"
                    error::class.qualifiedName.orEmpty().contains("SSL", ignoreCase = true) -> "tls"
                    else -> "player_setup"
                },
                host = host, durationSeconds = null, exceptionChain = exceptionChain(error), responseHeaderNames = "",
            )
        } finally {
            runCatching { instrumentation.runOnMainSync { playerRef.getAndSet(null)?.release() } }
        }
    }
'''

OLD_ANDROID_PROBE_BLOCK = '''                rows.firstOrNull()?.let { row ->
                    val probe = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} state=${probe.state} kind=${probe.kind} status=${probe.status} content_type64=${b64(probe.contentType)} extm3u=${probe.extm3u} duration_seconds=${probe.durationSeconds ?: 0.0} host64=${b64(probe.host)} media_hint64=${b64(probe.mediaHint)}")
                }
'''

NEW_ANDROID_PROBE_BLOCK = '''                rows.take(__MAX_PROBES__).forEachIndexed { index, row ->
                    val transport = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index state=${transport.state} kind=${transport.kind} status=${transport.status} content_type64=${b64(transport.contentType)} extm3u=${transport.extm3u} duration_seconds=${transport.durationSeconds ?: 0.0} host64=${b64(transport.host)} media_hint64=${b64(transport.mediaHint)}")
                    val reader = probeNativePlayer(row.url, row.headers, __EXPECTED_MINUTES__)
                    emit("FIELD_NATIVE_PLAYER client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index state=${reader.state} engine=${reader.engine} http_status=${reader.httpStatus} failure_stage=${reader.failureStage} duration_seconds=${reader.durationSeconds ?: 0.0} host64=${b64(reader.host)} error_class64=${b64(reader.errorClass)} error_code64=${b64(reader.errorCode)} exception_chain64=${b64(reader.exceptionChain)} response_header_names64=${b64(reader.responseHeaderNames)}")
                }
'''

def augment_android_test(source: str, *, client: str, expected_duration_minutes: int | float | None = None, max_player_probes: int = 1) -> str:
    if client not in {"mobile", "tv"}:
        raise ValueError(f"unsupported Android client: {client}")
    max_player_probes = max(1, min(int(max_player_probes or 1), 4))
    expected = max(0, int(expected_duration_minutes or 0))
    if "FIELD_NATIVE_PLAYER " in source:
        return source
    if source.count(ANDROID_IMPORT_ANCHOR) != 1:
        raise ValueError("android import anchor missing or ambiguous")
    imports = COMMON_IMPORTS + (TV_IMPORT if client == "tv" else MOBILE_IMPORT)
    source = source.replace(ANDROID_IMPORT_ANCHOR, ANDROID_IMPORT_ANCHOR + imports, 1)
    factory = (
        "return PlayerPlaybackNetworking.createDataSourceFactory(context, headers)"
        if client == "tv"
        else """return PlatformPlaybackDataSourceFactory.create(
            context = context,
            defaultRequestHeaders = headers,
            defaultResponseHeaders = emptyMap(),
            useYoutubeChunkedPlayback = false,
        )"""
    )
    helpers = PLAYER_HELPERS_TEMPLATE.replace("__DATA_SOURCE_FACTORY__", factory)
    if source.count(TEST_ANCHOR) != 1:
        raise ValueError("test anchor missing or ambiguous")
    source = source.replace(TEST_ANCHOR, helpers + "\n" + TEST_ANCHOR, 1)
    old = OLD_ANDROID_PROBE_BLOCK.replace("__CLIENT__", client)
    if source.count(old) != 1:
        raise ValueError(f"transport probe anchor missing for {client}: count={source.count(old)}")
    new = NEW_ANDROID_PROBE_BLOCK.replace("__CLIENT__", client).replace("__MAX_PROBES__", str(max_player_probes)).replace("__EXPECTED_MINUTES__", str(expected))
    return source.replace(old, new, 1)


def filter_staged_providers(providers: Iterable[dict], provider: str | None) -> list[dict]:
    rows = list(providers)
    wanted = str(provider or "").strip().casefold()
    if not wanted:
        return rows
    filtered = [row for row in rows if str(row.get("id") or "").strip().casefold() == wanted]
    if not filtered:
        available = ", ".join(str(row.get("id") or "") for row in rows[:40])
        raise ValueError(f"unknown provider {provider!r}; available sample: {available}")
    return filtered
